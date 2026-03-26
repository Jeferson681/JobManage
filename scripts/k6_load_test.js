import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

import { randomString } from './k6/k6-utils.js';

// =========================
// METRICS CUSTOM
// =========================
const createdJobs = new Counter('jobs_created');
const idempotentHits = new Counter('idempotent_hits');
const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency');

// =========================
// CONFIG
// =========================
export const options = {
  scenarios: {
    spike_test: {
      executor: 'ramping-arrival-rate',
      startRate: 200,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 500,
      stages: [
        { duration: '20s', target: 500 },
        { duration: '20s', target: 1000 },
        { duration: '30s', target: 1000 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<1200'],
    errors: ['rate<0.05'],
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';

// pool FIXO de idempotência → força colisão real (aumentar colisões)
const IDEMPOTENCY_POOL = Array.from({ length: 10 }, (_, i) => `idem-${i}`);

// =========================
// PAYLOAD
// =========================
function makePayload(i) {
  return {
    job_type: 'email',
    payload: {
      to: `user+${i}@test.com`,
      content: "hello"
    },
    max_attempts: 3,
  };
}

// =========================
// TEST
// =========================
export default function () {
  const i = Math.floor(Math.random() * 1e9);
  const body = JSON.stringify(makePayload(i));

  const headers = {
    'Content-Type': 'application/json',
  };

  // 20% das requisições com chave REPETIDA
  if (Math.random() < 0.2) {
    const key = IDEMPOTENCY_POOL[Math.floor(Math.random() * IDEMPOTENCY_POOL.length)];
    headers['Idempotency-Key'] = key;
  }

  const res = http.post(`${BASE}/jobs`, body, { headers });

  latencyTrend.add(res.timings.duration);

  const ok = check(res, {
    'status 200/201/409': (r) =>
      r.status === 200 || r.status === 201 || r.status === 409,
  });

  if (!ok) {
    errorRate.add(1);
  }

  if (res.status === 201) {
    createdJobs.add(1);
  }

  if (res.status === 409) {
    idempotentHits.add(1);
  }

  // quase sem descanso → pressão contínua (quase zero)
  sleep(0.001);
}
## Use cases

```mermaid
flowchart LR
  subgraph Actor[Actor]
    U[User]
  end

  subgraph API[API Service]
    A[POST /jobs]
    B[GET /jobs/{id}]
    C[POST /jobs/{id}/cancel]
  end

  subgraph System[System]
    Q[Job Store]
    W[Worker]
  end

  U -->|create job| A
  A -->|returns job_id| U
  A --> Q
  W -->|reserve job| Q
  W -->|execute| Q
  U -->|query status| B
  U -->|request cancel| C

classDef meta fill:#f9f,stroke:#333,stroke-width:1px
class Actor,API,System meta
```

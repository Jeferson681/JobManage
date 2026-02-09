from jobmanager.schemas.models import JobCreate, Status


def test_jobcreate_validation():
    item = JobCreate(job_type="send_email", payload={"to": "x"}, max_attempts=2)
    assert item.job_type == "send_email"
    assert item.payload["to"] == "x"
    assert item.max_attempts == 2


def test_status_enum():
    assert Status.QUEUED.name == "QUEUED"
    assert Status.SUCCEEDED.name == "SUCCEEDED"

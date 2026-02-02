from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class JobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class Job:
    id: int = None
    job_type: str = None
    payload: dict = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    retries: int = 0
    max_retries: int = 3
    result: dict = field(default_factory=dict)
    last_error: str = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_db_tuple(self):
        return (
            self.job_type,
            json.dumps(self.payload),
            self.status.value,
            self.retries,
            self.max_retries,
            json.dumps(self.result) if self.result else None,
            self.last_error,
            self.created_at.isoformat(),
            self.updated_at.isoformat()
        )

    @staticmethod
    def from_row(row):
        if not row:
            return None
        job = Job()
        job.id = row['id']
        job.job_type = row['job_type']
        try:
            job.payload = json.loads(row['payload']) if row['payload'] else {}
        except Exception:
            job.payload = {}
        job.status = JobStatus(row['status']) if row['status'] else JobStatus.PENDING
        job.retries = row['retries'] or 0
        job.max_retries = row['max_retries'] or 3
        try:
            job.result = json.loads(row['result']) if row['result'] else {}
        except Exception:
            job.result = {}
        job.last_error = row.get('last_error')
        job.created_at = row.get('created_at')
        job.updated_at = row.get('updated_at')
        return job

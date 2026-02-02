import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'backend'))
from infra.job_queue import JobQueue
from database import Database


def test_job_create_claim_mark_done():
    db_file = 'test_jobs.db'
    if os.path.exists(db_file):
        os.unlink(db_file)
    db = Database(db_path=db_file)
    q = JobQueue(db=db)

    job_id = q.create_job('test_job', payload={'x': 1})
    assert job_id is not None

    # Claim next job
    job = q.claim_next_job()
    assert job is not None
    assert job.job_type == 'test_job'

    # Mark done
    q.mark_done(job.id, {'ok': True})
    job2 = q.get_job(job.id)
    assert job2.status.value == 'DONE'
    assert job2.result.get('ok') is True

    # Cleanup
    os.unlink(db_file)

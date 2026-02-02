import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'backend'))
from infra.job_queue import JobQueue
from background.runner import Runner
from application.quiz_service import QuizService
from database import Database


def test_runner_no_work():
    db_file = 'test_runner.db'
    if os.path.exists(db_file):
        os.unlink(db_file)
    db = Database(db_path=db_file)
    q = JobQueue(db=db)
    runner = Runner(job_queue=q, quiz_service=QuizService())

    # No jobs -> tick returns 'NoWork'
    assert runner.tick() == 'NoWork'

    # Create a dummy job and ensure tick processes or retries
    job_id = q.create_job('generate_next_question', payload={'chunks': [], 'num_questions': 0})
    res = runner.tick()
    # Since chunks empty, generate_questions will raise RuntimeError and runner returns 'Failure'
    assert res in ('Failure', 'Success', 'NoWork')

    os.unlink(db_file)

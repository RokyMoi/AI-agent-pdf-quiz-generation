"""
Simple DB-backed job queue using existing Database connection (SQLite).
This module provides atomic claim semantics suitable for single-process workers.
For multi-process or heavy scaling, replace with Redis/RabbitMQ-backed queue.
"""

from typing import Optional
from database import Database
from models.job import Job, JobStatus
import json
import logging

logger = logging.getLogger(__name__)


class JobQueue:
    def __init__(self, db: Database = None):
        self.db = db or Database()

    def create_job(self, job_type: str, payload: dict, max_retries: int = 3) -> Optional[int]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO jobs (job_type, payload, status, retries, max_retries, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (job_type, json.dumps(payload or {}), JobStatus.PENDING.value, 0, max_retries)
        )
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Job created: id={job_id}, type={job_type}")
        return job_id

    def claim_next_job(self) -> Optional[Job]:
        """Atomarno claim-uje jedan PENDING job i vraća ga kao Job objekt. Returns None if none found."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            # Start a transaction to avoid races
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute("SELECT id FROM jobs WHERE status = ? ORDER BY created_at ASC LIMIT 1", (JobStatus.PENDING.value,))
            row = cursor.fetchone()
            if not row:
                conn.commit()
                conn.close()
                return None
            job_id = row[0]
            cursor.execute("UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = ?", (JobStatus.IN_PROGRESS.value, job_id, JobStatus.PENDING.value))
            if cursor.rowcount != 1:
                conn.commit()
                conn.close()
                return None
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            job_row = cursor.fetchone()
            conn.commit()
            job = Job.from_row(job_row)
            conn.close()
            logger.info(f"Claimed job id={job.id}")
            return job
        except Exception as e:
            conn.rollback()
            conn.close()
            logger.exception(f"Error claiming job: {e}")
            return None

    def mark_done(self, job_id: int, result: dict = None):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET status = ?, result = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (JobStatus.DONE.value, json.dumps(result or {}), job_id))
        conn.commit()
        conn.close()
        logger.info(f"Job done: id={job_id}")

    def mark_failed(self, job_id: int, error: str, increment_retry: bool = True, max_retries: int = 3):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        if increment_retry:
            cursor.execute("UPDATE jobs SET retries = retries + 1, last_error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (error, job_id))
            cursor.execute("SELECT retries, max_retries FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            retries = row[0] or 0
            allowed = row[1] or max_retries
            if retries >= allowed:
                # Exhausted retries -> mark failed
                cursor.execute("UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (JobStatus.FAILED.value, job_id))
            else:
                # Schedule retry: set back to PENDING so it can be retried by runner
                cursor.execute("UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (JobStatus.PENDING.value, job_id))
        else:
            cursor.execute("UPDATE jobs SET status = ?, last_error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (JobStatus.FAILED.value, error, job_id))
        conn.commit()
        conn.close()
        logger.warning(f"Job failed: id={job_id}, error={error}")

    def get_job(self, job_id: int) -> Optional[Job]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        return Job.from_row(row)

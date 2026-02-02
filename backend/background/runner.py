"""
Background Runner: loop koji poziva tick() da obradi jedan job.
Implementiran kao thread da bude kompatibilan sa postojećim Flask/Sync okruženjem.
"""

import threading
import time
import logging
from infra.job_queue import JobQueue
from application.quiz_service import QuizService

logger = logging.getLogger(__name__)


class Runner:
    def __init__(self, job_queue: JobQueue = None, quiz_service: QuizService = None, poll_interval: float = 1.0, backoff: float = 2.0):
        self.job_queue = job_queue or JobQueue()
        self.quiz_service = quiz_service or QuizService()
        self.poll_interval = poll_interval
        self.backoff = backoff
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name='BackgroundRunner')
        self._thread.daemon = True
        self._thread.start()
        logger.info('Background Runner started')

    def stop(self, timeout: float = 5.0):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout)
        logger.info('Background Runner stopped')

    def _run(self):
        while not self._stop_event.is_set():
            try:
                res = self.tick()
                if res == 'NoWork':
                    time.sleep(self.poll_interval)
                else:
                    # Immediately continue to try to process more work
                    continue
            except Exception as e:
                logger.exception(f'Runner loop error: {e}')
                time.sleep(self.backoff)

    def tick(self):
        job = self.job_queue.claim_next_job()
        if not job:
            logger.debug('tick: NoWork')
            return 'NoWork'
        try:
            logger.info(f'Processing job id={job.id} type={job.job_type}')
            result = self.quiz_service.process_job(job)
            self.job_queue.mark_done(job.id, result)
            return 'Success'
        except Exception as e:
            self.job_queue.mark_failed(job.id, str(e), increment_retry=True)
            logger.exception(f'Error processing job id={job.id}: {e}')
            return 'Failure'

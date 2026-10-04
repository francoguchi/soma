import asyncio
from concurrent.futures import ThreadPoolExecutor, wait
import threading
from contextvars import copy_context

from soma.foundation.errors import SomaError


class BoundedExecutor:
    def __init__(self, workers, queue_bound=8):
        if not 1 <= workers <= 4 or not 0 <= queue_bound <= 32:
            raise ValueError("Invalid executor capacity")
        self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="soma")
        self.slots = threading.BoundedSemaphore(workers + queue_bound)
        self.lock = threading.Lock()
        self.futures = set()
        self.accepting = True

    def submit(self, function, *args):
        with self.lock:
            if not self.accepting or not self.slots.acquire(blocking=False):
                raise SomaError("HOST_BUSY", "SOMA is busy or stopping.", "retry")
            try:
                future = self.executor.submit(copy_context().run, function, *args)
                self.futures.add(future)
            except BaseException:
                self.slots.release()
                raise

        def complete(future):
            with self.lock:
                self.futures.discard(future)
                self.slots.release()

        future.add_done_callback(complete)
        return future

    async def run(self, function, *args):
        return await asyncio.wrap_future(self.submit(function, *args))

    def quiesce(self):
        with self.lock:
            self.accepting = False

    def drain(self, timeout):
        self.quiesce()
        with self.lock:
            pending = set(self.futures)
        return not wait(pending, timeout=max(0, timeout))[1] if pending else True

    def close(self):
        self.quiesce()
        self.executor.shutdown(wait=False, cancel_futures=True)


class JobWorkers:
    def __init__(self, coordinator, handlers, run_id, log, *, workers=2):
        if not 1 <= workers <= 2:
            raise ValueError("Invalid background worker count")
        if set(handlers) != set(coordinator.contracts):
            raise ValueError("Every durable job contract requires exactly one handler")
        self.coordinator, self.handlers, self.run_id, self.log = coordinator, handlers, run_id, log
        self.cancel = threading.Event()
        self.executor = BoundedExecutor(workers, 0)
        self.workers = workers

    def start(self):
        while self.coordinator.recover(self.run_id):
            pass
        for _ in range(self.workers):
            self.executor.submit(self._loop)

    def _loop(self):
        while not self.cancel.is_set():
            try:
                claim = self.coordinator.claim_next(self.run_id)
                if claim is None:
                    self.cancel.wait(0.2)
                    continue
                if self.cancel.is_set():
                    # Persisted running claim is recoverable; do not run new work.
                    break
                self.handlers[(claim.job_type, claim.version)](claim, self.cancel, self.coordinator)
            except Exception:
                self.log.emit("JOB_HANDLER_FAILED")
                # No made-up retry policy: exact owner failure validation governs.
                if "claim" in locals() and claim is not None:
                    try:
                        self.coordinator.fail(claim, "JOB_HANDLER_FAILED")
                    except Exception:
                        self.log.emit("JOB_RECOVERY_REQUIRED")
                self.cancel.wait(0.2)

    def stop(self, timeout):
        self.cancel.set()
        drained = self.executor.drain(timeout)
        if drained:
            self.executor.close()
        return drained

"""
Worker Management Service

Manages Temporal worker processes for workflow execution.
Automatically starts run_worker_with_correct_host.py when needed.
"""

import asyncio
import logging
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages Temporal worker processes"""

    def __init__(self):
        self._worker_process: Optional[subprocess.Popen] = None
        self._worker_lock = asyncio.Lock()
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds

    async def ensure_worker_running(self) -> bool:
        """
        Ensure a worker is running for processing workflows.
        Uses run_worker_with_correct_host.py as the default worker.

        Returns:
            True if worker is running, False otherwise
        """
        async with self._worker_lock:
            # Check if worker is already running and healthy
            if await self._is_worker_healthy():
                return True

            # Start new worker process
            return await self._start_worker()

    async def _is_worker_healthy(self) -> bool:
        """Check if the current worker process is healthy"""
        current_time = time.time()

        # Skip frequent health checks
        if current_time - self._last_health_check < self._health_check_interval:
            return self._worker_process is not None and self._worker_process.poll() is None

        self._last_health_check = current_time

        # Check if process is still running
        if not self._worker_process or self._worker_process.poll() is not None:
            logger.info("Worker process is not running")
            return False

        # Process is running
        logger.debug("Worker process is healthy")
        return True

    async def _start_worker(self) -> bool:
        """Start the Temporal worker using run_worker_with_correct_host.py"""
        try:
            # Stop existing worker if any
            await self._stop_worker()

            # Path to the worker script
            repo_root = Path(__file__).resolve().parents[3]
            worker_script = repo_root / "odw" / "services" / "data-warehouse" / "run_worker_with_correct_host.py"

            if not worker_script.exists():
                logger.error(f"Worker script not found: {worker_script}")
                return False

            # Change to the correct directory
            work_dir = repo_root / "odw" / "services" / "data-warehouse"

            # Start the worker process
            logger.info(f"Starting Temporal worker: {worker_script}")
            self._worker_process = subprocess.Popen(
                ["python", str(worker_script)],
                cwd=str(work_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )

            # Give the worker a moment to start
            await asyncio.sleep(2)

            # Check if it started successfully
            if self._worker_process.poll() is None:
                logger.info(f"Worker started successfully with PID {self._worker_process.pid}")
                return True
            else:
                stdout, stderr = self._worker_process.communicate()
                logger.error(f"Worker failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            return False

    async def _stop_worker(self):
        """Stop the current worker process"""
        if self._worker_process:
            try:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(self._worker_process.pid), signal.SIGTERM)

                # Wait for graceful shutdown
                try:
                    self._worker_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop gracefully
                    os.killpg(os.getpgid(self._worker_process.pid), signal.SIGKILL)
                    self._worker_process.wait()

                logger.info("Worker process stopped")

            except Exception as e:
                logger.warning(f"Error stopping worker: {e}")
            finally:
                self._worker_process = None

    async def get_worker_status(self) -> Dict[str, any]:
        """Get current worker status information"""
        if not self._worker_process:
            return {
                "running": False,
                "pid": None,
                "script": "run_worker_with_correct_host.py",
                "status": "not_started"
            }

        poll_result = self._worker_process.poll()
        if poll_result is None:
            return {
                "running": True,
                "pid": self._worker_process.pid,
                "script": "run_worker_with_correct_host.py",
                "status": "running"
            }
        else:
            return {
                "running": False,
                "pid": self._worker_process.pid,
                "script": "run_worker_with_correct_host.py",
                "status": f"exited_with_code_{poll_result}"
            }

    async def restart_worker(self) -> bool:
        """Restart the worker process"""
        logger.info("Restarting worker process")
        async with self._worker_lock:
            await self._stop_worker()
            return await self._start_worker()

    async def shutdown(self):
        """Shutdown the worker manager and stop all workers"""
        logger.info("Shutting down worker manager")
        await self._stop_worker()


# Global worker manager instance
_worker_manager: Optional[WorkerManager] = None


def get_worker_manager() -> WorkerManager:
    """Get the global worker manager instance"""
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = WorkerManager()
    return _worker_manager
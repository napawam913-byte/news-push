from __future__ import annotations

import atexit
import json
import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessStatus:
    running: bool
    pid: int | None = None
    started_at: str = ""
    pid_file: Path | None = None


class SingleInstance:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.pid_file = data_dir / "news-push.pid"
        self.acquired = False

    def acquire(self) -> None:
        status = read_status(self.data_dir)
        if status.running and status.pid:
            raise RuntimeError(
                f"news-push is already running, pid={status.pid}. "
                "Use --status to inspect or --stop to stop it."
            )

        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "pid": os.getpid(),
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.pid_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.acquired = True
        atexit.register(self.release)

    def release(self) -> None:
        if not self.acquired:
            return
        try:
            current = _read_pid_file(self.pid_file)
            if current.get("pid") == os.getpid():
                self.pid_file.unlink(missing_ok=True)
        finally:
            self.acquired = False


def read_status(data_dir: Path) -> ProcessStatus:
    pid_file = data_dir / "news-push.pid"
    payload = _read_pid_file(pid_file)
    pid = _as_int(payload.get("pid"))
    if not pid:
        return ProcessStatus(running=False, pid_file=pid_file)

    if not _is_process_running(pid):
        pid_file.unlink(missing_ok=True)
        return ProcessStatus(running=False, pid=pid, pid_file=pid_file)

    return ProcessStatus(
        running=True,
        pid=pid,
        started_at=str(payload.get("started_at", "")),
        pid_file=pid_file,
    )


def stop_running_process(data_dir: Path) -> bool:
    status = read_status(data_dir)
    if not status.running or not status.pid:
        return False

    os.kill(status.pid, signal.SIGTERM)
    for _ in range(20):
        if not _is_process_running(status.pid):
            if status.pid_file:
                status.pid_file.unlink(missing_ok=True)
            return True
        time.sleep(0.2)
    return not _is_process_running(status.pid)


def _read_pid_file(pid_file: Path) -> dict:
    if not pid_file.exists():
        return {}
    try:
        return json.loads(pid_file.read_text(encoding="utf-8"))
    except Exception:
        pid_file.unlink(missing_ok=True)
        return {}


def _as_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _is_process_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        return _is_windows_process_running(pid)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _is_windows_process_running(pid: int) -> bool:
    try:
        import ctypes
    except ImportError:
        return True

    synchronize = 0x00100000
    process = ctypes.windll.kernel32.OpenProcess(synchronize, False, pid)
    if not process:
        return False
    try:
        wait_timeout = 0x00000102
        result = ctypes.windll.kernel32.WaitForSingleObject(process, 0)
        return result == wait_timeout
    finally:
        ctypes.windll.kernel32.CloseHandle(process)

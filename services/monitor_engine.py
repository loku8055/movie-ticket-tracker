import time
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List, Callable
from strategies.registry import registry
from services.notifier import Notifier

class MonitorEngine:
    def __init__(self, storage):
        self.storage = storage
        self.notifier = Notifier(storage)
        self._running = False
        self._threads: Dict[str, threading.Thread] = {}
        self._subscribers: List[queue.Queue] = []
        self._subscribers_lock = threading.Lock()

    def subscribe(self) -> queue.Queue:
        q = queue.Queue(maxsize=100)
        with self._subscribers_lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue):
        with self._subscribers_lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with self._subscribers_lock:
            dead_queues = []
            for q in self._subscribers:
                try:
                    q.put_nowait(payload)
                except queue.Full:
                    dead_queues.append(q)
            for dq in dead_queues:
                self._subscribers.remove(dq)

    def start(self):
        if self._running:
            return
        self._running = True
        self.sync_target_threads()

    def stop(self):
        self._running = False

    def sync_target_threads(self):
        """Ensure background checking threads match enabled targets in storage"""
        if not self._running:
            return

        targets = self.storage.get_targets()
        enabled_ids = {t["id"] for t in targets if t.get("enabled", True)}

        # Stop removed or disabled threads
        for target_id in list(self._threads.keys()):
            if target_id not in enabled_ids:
                del self._threads[target_id]

        # Start new threads for targets not already running
        for target in targets:
            tid = target["id"]
            if target.get("enabled", True) and tid not in self._threads:
                t = threading.Thread(target=self._run_target_loop, args=(tid,), daemon=True)
                self._threads[tid] = t
                t.start()

    def _run_target_loop(self, target_id: str):
        while self._running:
            target = self.storage.get_target(target_id)
            if not target or not target.get("enabled", True):
                break

            self.execute_check(target_id)

            interval = max(target.get("interval_sec", 15), 5)
            # Sleep in 1-second chunks to allow rapid cancellation
            for _ in range(interval):
                if not self._running or target_id not in self._threads:
                    break
                time.sleep(1)

    def execute_check(self, target_id: str) -> Dict[str, Any]:
        target = self.storage.get_target(target_id)
        if not target:
            return {"error": "Target not found"}

        strategy_id = target.get("strategy_id", "victory_cinema")
        strategy = registry.get(strategy_id)

        if not strategy:
            check_result = {
                "status": "ERROR",
                "is_available": False,
                "movie_title": target.get("movie_title"),
                "details": f"Unknown strategy ID: {strategy_id}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            start_time = time.time()
            check_result = strategy.inspect(target)
            latency_ms = int((time.time() - start_time) * 1000)
            check_result["latency_ms"] = latency_ms

        previous_status = target.get("last_status", "UNKNOWN")
        current_status = check_result.get("status", "ERROR")
        is_available = check_result.get("is_available", False)

        # Update storage for this target
        updates = {
            "last_status": current_status,
            "last_checked": datetime.utcnow().isoformat() + "Z",
            "last_latency_ms": check_result.get("latency_ms", 0),
            "booking_url": check_result.get("booking_url") or target.get("booking_url")
        }
        updated_target = self.storage.update_target(target_id, updates)

        # Record log entry
        log_entry = {
            "id": f"log-{int(time.time()*1000)}",
            "target_id": target_id,
            "movie_title": target.get("movie_title"),
            "theatre": target.get("theatre"),
            "status": current_status,
            "latency_ms": check_result.get("latency_ms", 0),
            "details": check_result.get("details", ""),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.storage.add_log(log_entry)
        self.broadcast_event("log:new", log_entry)
        self.broadcast_event("target:updated", updated_target)

        # Check for status transition to AVAILABLE
        if is_available or (previous_status != "AVAILABLE" and current_status == "AVAILABLE"):
            alert_entry = {
                "id": f"alert-{int(time.time()*1000)}",
                "target_id": target_id,
                "movie_title": target.get("movie_title"),
                "theatre": target.get("theatre"),
                "booking_url": check_result.get("booking_url") or target.get("target_url"),
                "details": check_result.get("details"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            self.storage.add_alert(alert_entry)
            self.broadcast_event("alert:triggered", alert_entry)
            self.notifier.notify(updated_target, check_result)

        return check_result

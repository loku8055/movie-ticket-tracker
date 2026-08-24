import json
import os
import threading
from typing import Dict, Any, List, Optional
from config import STORE_FILE

DEFAULT_INITIAL_DATA = {
    "targets": [
        {
            "id": "target-victory-toxic",
            "movie_title": "Toxic: A Fairy Tale for Grown Ups (Kannada)",
            "theatre": "Victory Cinema",
            "website": "https://victorycinema.in/",
            "target_url": "https://victorycinema.in/upcoming-movie/toxic-kannada-with-english-subtitles/",
            "strategy_id": "victory_cinema",
            "interval_sec": 15,
            "enabled": True,
            "last_status": "COMING_SOON",
            "last_checked": None,
            "last_latency_ms": 0,
            "booking_url": None,
            "created_at": "2026-08-24T21:00:00Z"
        }
    ],
    "settings": {
        "sound_enabled": True,
        "desktop_notifications": True,
        "voice_alerts": True,
        "telegram_webhook_url": "",
        "discord_webhook_url": "",
        "custom_webhook_url": ""
    },
    "alerts": [],
    "logs": []
}

class Storage:
    def __init__(self, filepath: str = STORE_FILE):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        with self._lock:
            if not os.path.exists(self.filepath):
                self._data = DEFAULT_INITIAL_DATA
                self._save_unlocked()
            else:
                try:
                    with open(self.filepath, 'r', encoding='utf-8') as f:
                        self._data = json.load(f)
                except Exception:
                    self._data = DEFAULT_INITIAL_DATA
                    self._save_unlocked()

    def _save_unlocked(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2)

    def save(self):
        with self._lock:
            self._save_unlocked()

    def get_targets(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._data.get("targets", []))

    def get_target(self, target_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for t in self._data.get("targets", []):
                if t["id"] == target_id:
                    return dict(t)
            return None

    def add_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._data.setdefault("targets", []).append(target)
            self._save_unlocked()
            return target

    def update_target(self, target_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            for t in self._data.get("targets", []):
                if t["id"] == target_id:
                    t.update(updates)
                    self._save_unlocked()
                    return dict(t)
            return None

    def delete_target(self, target_id: str) -> bool:
        with self._lock:
            targets = self._data.get("targets", [])
            initial_count = len(targets)
            self._data["targets"] = [t for t in targets if t["id"] != target_id]
            if len(self._data["targets"]) < initial_count:
                self._save_unlocked()
                return True
            return False

    def get_settings(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data.get("settings", DEFAULT_INITIAL_DATA["settings"]))

    def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._data.setdefault("settings", {}).update(new_settings)
            self._save_unlocked()
            return dict(self._data["settings"])

    def add_log(self, log_entry: Dict[str, Any]):
        with self._lock:
            logs = self._data.setdefault("logs", [])
            logs.insert(0, log_entry)
            # Keep max 100 logs
            if len(logs) > 100:
                self._data["logs"] = logs[:100]
            self._save_unlocked()

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._data.get("logs", []))[:limit]

    def add_alert(self, alert_entry: Dict[str, Any]):
        with self._lock:
            alerts = self._data.setdefault("alerts", [])
            alerts.insert(0, alert_entry)
            if len(alerts) > 100:
                self._data["alerts"] = alerts[:100]
            self._save_unlocked()

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._data.get("alerts", []))[:limit]

storage_instance = Storage()

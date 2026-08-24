from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

class BaseStrategy(ABC):
    """
    Abstract Base Class for Cinema Ticket Release Strategies.
    All site-specific or target-specific monitoring strategies must inherit from this class.
    """
    def __init__(self, strategy_id: str, name: str, description: str):
        self.strategy_id = strategy_id
        self.name = name
        self.description = description

    @abstractmethod
    def inspect(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspect target cinema page and return standardized check result dict:
        {
            "status": "AVAILABLE" | "COMING_SOON" | "UNAVAILABLE" | "ERROR",
            "is_available": bool,
            "movie_title": str,
            "booking_url": Optional[str],
            "details": str,
            "raw_match": Optional[Dict],
            "timestamp": str (ISO)
        }
        """
        pass

    def format_result(
        self,
        status: str,
        is_available: bool,
        movie_title: str,
        booking_url: Optional[str] = None,
        details: str = "",
        raw_match: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "is_available": bool(is_available),
            "movie_title": movie_title or "Unknown Movie",
            "booking_url": booking_url,
            "details": details or "",
            "raw_match": raw_match or {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

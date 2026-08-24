from typing import Dict, List, Optional
from strategies.base_strategy import BaseStrategy
from strategies.victory_cinema_strategy import VictoryCinemaStrategy
from strategies.generic_selector_strategy import GenericSelectorStrategy

class StrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}
        self._register_default_strategies()

    def _register_default_strategies(self):
        victory = VictoryCinemaStrategy()
        generic = GenericSelectorStrategy()
        self.register(victory)
        self.register(generic)

    def register(self, strategy: BaseStrategy):
        self._strategies[strategy.strategy_id] = strategy

    def get(self, strategy_id: str) -> Optional[BaseStrategy]:
        return self._strategies.get(strategy_id)

    def list_strategies(self) -> List[Dict[str, str]]:
        return [
            {
                "id": s.strategy_id,
                "name": s.name,
                "description": s.description
            }
            for s in self._strategies.values()
        ]

registry = StrategyRegistry()

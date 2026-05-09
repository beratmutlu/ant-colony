from enum import Enum

class ItemType(Enum):
    FOOD = 1
    PHEROMONE_NEST = 2
    PHEROMONE_FOOD = 3

    @property
    def decays(self) -> bool:
        return self in (ItemType.PHEROMONE_FOOD, ItemType.PHEROMONE_NEST)

    @property
    def decay_rate(self) -> float:
        rates = {
            ItemType.PHEROMONE_FOOD: 0.1,
            ItemType.PHEROMONE_NEST: 0.1,
        }
        return rates.get(self, 0.0)
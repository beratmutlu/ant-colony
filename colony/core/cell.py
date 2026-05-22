from colony.types.item_type import ItemType

class Cell:
    def __init__(self, pos: tuple[int, int], cap_ant: int, cap_item: int, items: dict[ItemType, float] | None = None):
        self.pos = pos
        self.cap_ant = cap_ant
        self.cap_item = cap_item
        self.items: dict[ItemType, float] = {t: 0.0 for t in ItemType}
        if items:
            self.items.update(items)

    def add_item(self, item: ItemType, amount: float) -> None:
        if item.decays:
            self.items[item] = min(self.items[item] + amount, self.cap_item)
        else:
            self.items[item] += amount

    def remove_item(self, item: ItemType, amount: float) -> None:
        self.items[item] = max(self.items[item] - amount, 0)

    def get_food(self) -> float:
        return self.items[ItemType.FOOD]

    def get_pheromones(self) -> dict[ItemType, float]:
        return {t: v for t, v in self.items.items() if t.decays}

    def clear_pheromones(self) -> None:
        for item in ItemType:
            if item.decays:
                self.items[item] = 0.0
    
    def decay_item(self, item: ItemType) -> None:
        if item.decays:
            self.items[item] = max(self.items[item] * item.decay_rate, 0.0)

    def decay_all(self) -> None:
        for item in self.items:
            self.decay_item(item)

from colony.core.cell import Cell
from colony.agents.action import Direction

class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.cells: dict[tuple[int, int], Cell] = {
            (x, y): Cell((x, y), cap_ant=10, cap_item=100)
            for x in range(width)
            for y in range(height)
        }

    def get_cell(self, x: int, y: int) -> Cell:
        if (x, y) not in self.cells:
            raise IndexError(f"({x}, {y}) not in grid")
        return self.cells[(x, y)]

    def get_neighbours(self, cell: Cell) -> dict[Direction, Cell | None]:
        return {
            d: self.cells.get(d.apply(cell.pos))
            for d in Direction
        }

    def tick_decay(self) -> None:
        for cell in self.cells.values():
            cell.decay_all()

    def __repr__(self) -> str:
        return f"Grid({self.width}x{self.height})"

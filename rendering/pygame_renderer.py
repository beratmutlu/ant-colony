import pygame
from colony.core.simulation import Simulation
from colony.types.item_type import ItemType

CELL = 24
FPS = 15

class PygameRenderer:
    def __init__(self, sim: Simulation):
        self.sim = sim
        cfg = sim.config
        self.W = cfg["grid"]["width"]
        self.H = cfg["grid"]["height"]
        self.nest = tuple(cfg["nest_pos"])
        self.debug = False
        self.show_food_ph = True
        self.show_nest_ph = True

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.W * CELL, self.H * CELL))
        pygame.display.set_caption("AntSim")
        clock = pygame.time.Clock()
        paused = False

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        paused = not paused
                    if event.key == pygame.K_d:
                        self.debug = not self.debug
                    if event.key == pygame.K_f:
                        self.show_food_ph = not self.show_food_ph
                    if event.key == pygame.K_n:
                        self.show_nest_ph = not self.show_nest_ph

            if not paused:
                self.sim.step()

            for (x, y), cell in self.sim.manager.grid.cells.items():
                color = self._cell_color(cell)
                pygame.draw.rect(screen, color, (x*CELL, y*CELL, CELL-1, CELL-1))

            for ant in self.sim.manager.ants:
                x, y = ant.cell.pos
                color = (255, 200, 0) if ant.carrying else (255, 255, 255)
                pygame.draw.circle(screen, color,
                    (x*CELL + CELL//2, y*CELL + CELL//2), CELL//3)

            pygame.display.flip()
            clock.tick(FPS)

    def _cell_color(self, cell) -> tuple:
        if cell.pos == self.nest:
            return (255, 220, 50)
        if cell.get_food() > 0:
            g = int(min(cell.get_food() / 10 * 255, 255))
            return (0, g, 0)

        if self.debug:
            return (20, 20, 20)

        r = int(min(cell.items[ItemType.PHEROMONE_FOOD] / 10 * 255, 255)) if self.show_food_ph else 0
        b = int(min(cell.items[ItemType.PHEROMONE_NEST] / 10 * 255, 255)) if self.show_nest_ph else 0
        return (r, 10, b)
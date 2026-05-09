import pygame
from colony.core.simulation import Simulation
from colony.types.item_type import ItemType
import math

CELL = 24
FPS = 10

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
        self.show_gradient = False

    def _draw_arrow(self, screen, color, start, end, size=4):
        pygame.draw.line(screen, color, start, end, 1)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        for side in (+0.5, -0.5):
            ax = end[0] - size * math.cos(angle - side)
            ay = end[1] - size * math.sin(angle - side)
            pygame.draw.line(screen, color, end, (int(ax), int(ay)), 1)

    def _draw_gradient_arrow(self, screen, cell, x, y):
        pheromones = cell.get_pheromones()

        food_ph = pheromones.get(ItemType.PHEROMONE_FOOD, 0.0)
        nest_ph = pheromones.get(ItemType.PHEROMONE_NEST, 0.0)
        if food_ph + nest_ph < 5.0:
            return

        best_dir = max(
            self.sim.manager.grid.get_neighbours(cell).items(),
            key=lambda kv: kv[1].get_pheromones().get(ItemType.PHEROMONE_FOOD, 0.0) if kv[1] else 0
        )

        d, _ = best_dir
        dx, dy = d.value
        cx, cy = x*CELL + CELL//2, y*CELL + CELL//2
        ex, ey = cx + dx*(CELL//2 - 1), cy + dy*(CELL//2 - 1)
        self._draw_arrow(screen, (255, 255, 0), (cx, cy), (ex, ey))

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
                    if event.key == pygame.K_g:
                        self.show_gradient = not self.show_gradient

            if not paused:
                self.sim.step()

            for (x, y), cell in self.sim.manager.grid.cells.items():
                color = self._cell_color(cell)
                pygame.draw.rect(screen, color, (x*CELL, y*CELL, CELL-1, CELL-1))

            if self.show_gradient:
                for (x, y), cell in self.sim.manager.grid.cells.items():
                    if x % 2 != 0 or y % 2 != 0:
                        continue
                    self._draw_gradient_arrow(screen, cell, x, y)

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

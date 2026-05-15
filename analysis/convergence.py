from dataclasses import dataclass, field
import statistics


@dataclass
class ConvergenceTracker:
    window: int = 10
    epsilon: float = 0.01 # CV^2 = var / mean^2
    min_mean: float = 30.0
    history: list[int] = field(default_factory=list)
    convergence_epoch: int | None = None

    def _is_stable(self, window_data: list[int]) -> bool:
        m = statistics.mean(window_data)
        if m < self.min_mean:
            return False
        cv_squared = statistics.variance(window_data) / (m ** 2)
        return cv_squared < self.epsilon

    def update(self, epoch: int, food_this_epoch: int) -> None:
        self.history.append(food_this_epoch)

        if self.convergence_epoch is not None:
            return

        if len(self.history) >= self.window:
            if self._is_stable(self.history[-self.window:]):
                self.convergence_epoch = epoch


    @property
    def converged(self) -> bool:
        return self.convergence_epoch is not None

    @property
    def stable(self) -> bool:
        if not self.converged or len(self.history) < self.window:
            return False
        return self._is_stable(self.history[-self.window:])

    def reset(self) -> None:
        self.history.clear()
        self.convergence_epoch = None

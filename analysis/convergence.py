from dataclasses import dataclass, field
import statistics


@dataclass
class OnlineConvergenceTracker:
    # Gate: do not evaluate convergence before enough data exists.
    window: int = 10
    min_epochs: int = 30

    # Local stability: recent window must be calm and productive enough.
    epsilon: float = 0.01 # CV^2 = var / mean^2
    min_mean: float = 30.0
    max_slope: float = 1.0

    # Drift checks: reject locally calm windows that are still changing.
    change_window: int = 10
    trend_window: int = 30
    max_recent_change: float = 3.0
    max_trend_slope: float = 0.15

    # Confirmation/revocation: require repeated evidence before changing state.
    required_stable_windows: int = 3
    required_unstable_windows: int = 10

    # Runtime state.
    history: list[int] = field(default_factory=list)
    stable_windows: int = 0
    unstable_windows: int = 0
    convergence_epoch: int | None = None
    active_plateau_start: int | None = None
    plateau_ranges: list[tuple[int, int]] = field(default_factory=list)

    def _is_stable(self, window_data: list[int]) -> bool:
        m = statistics.mean(window_data)
        if m < self.min_mean:
            return False
        cv_squared = statistics.variance(window_data) / (m ** 2)
        slope = self._slope(window_data)

        return cv_squared < self.epsilon and abs(slope) <= self.max_slope

    def _slope(self, window_data: list[int]) -> float:
        if len(window_data) < 2:
            return 0.0
        return (window_data[-1] - window_data[0]) / (len(window_data) - 1)
    
    def _trend_slope(self) -> float:
        if len(self.history) < self.trend_window:
            return 0.0
        
        window_data = self.history[-self.trend_window:]
        return self._slope(window_data)
    
    def _recent_change(self) -> float:
        needed = self.change_window * 2
        if len(self.history) < needed:
            return 0.0

        previous = self.history[-needed:-self.change_window]
        recent = self.history[-self.change_window:]

        return abs(statistics.mean(recent) - statistics.mean(previous))

    def _stable_now(self) -> bool:
        if len(self.history) < max(self.window, self.min_epochs):
            return False

        stable_window = self._is_stable(self.history[-self.window:])
        low_recent_change = self._recent_change() <= self.max_recent_change
        low_long_trend = abs(self._trend_slope()) <= self.max_trend_slope

        return stable_window and low_recent_change and low_long_trend
    
    def update(self, epoch: int, food_this_epoch: int) -> None:
        self.history.append(food_this_epoch)

        if epoch < self.min_epochs:
            return
        
        if len(self.history) < self.window:
            return
        
        stable_now = self._stable_now()

        if self.convergence_epoch is None:
            if stable_now:
                self.stable_windows += 1
            else:
                self.stable_windows = 0

            if self.stable_windows >= self.required_stable_windows:
                plateau_start = epoch - self.required_stable_windows + 1

                self.convergence_epoch = plateau_start
                self.active_plateau_start = plateau_start
                self.unstable_windows = 0
        
        else:
            if stable_now:
                self.unstable_windows = 0
            else:
                self.unstable_windows += 1

            if self.unstable_windows >= self.required_unstable_windows:
                plateau_end = epoch - self.required_unstable_windows

                if self.active_plateau_start is not None:
                    self.plateau_ranges.append((self.active_plateau_start, plateau_end))

                self.convergence_epoch = None
                self.active_plateau_start = None
                self.stable_windows = 0
                self.unstable_windows = 0


    @property
    def converged(self) -> bool:
        return self.convergence_epoch is not None

    @property
    def stable(self) -> bool:
        return self._stable_now()

    def reset(self) -> None:
        self.history.clear()
        self.stable_windows = 0
        self.unstable_windows = 0
        self.convergence_epoch = None
        self.active_plateau_start = None
        self.plateau_ranges.clear()

@dataclass
class PostHocConvergenceDetector:
    pass

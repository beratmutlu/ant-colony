from dataclasses import dataclass, field
import statistics

import math
import numpy as np
import ruptures as rpt

@dataclass
class OnlineConvergenceTracker:
    # Gate: do not evaluate convergence before enough data exists.
    window: int = 10
    min_epochs: int = 30

    # Local stability: recent window must be calm.
    epsilon: float = 0.01 # CV^2 = var / mean^2
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
        if m == 0:
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



@dataclass(frozen=True)
class PostHocSegment:
    start_epoch: int
    end_epoch: int
    length: int
    mean: float
    std: float
    slope: float
    relative_total_drift: float

@dataclass(frozen=True)
class PostHocConvergenceResult:
    convergence_epoch : int | None = None
    change_points: list[int] = field(default_factory=list)
    segments: list[PostHocSegment] = field(default_factory=list)
    plateau_ranges: list[tuple[int, int]] = field(default_factory=list)

@dataclass
class PostHocConvergenceDetector:
    model: str = "l2"
    min_size: int = 10
    jump: int = 1
    penalty_scale: float = 1.0
    penalty: float | None = None
    min_plateau_epochs: int = 10
    max_relative_total_drift: float = 0.08
    min_relative_regime_step: float = 0.08
    ignore_first_segment: bool = True

    def detect(self, epoch_history: list[int]) -> PostHocConvergenceResult:
        n = len(epoch_history)

        if n == 0:
            return PostHocConvergenceResult()

        segment = self._build_segment(epoch_history, 0, n)

        if n < self.min_size * 2:
            return PostHocConvergenceResult(
                convergence_epoch=None,
                change_points=[],
                segments=[segment],
                plateau_ranges=[],
            )
        
        signal = np.asarray(epoch_history, dtype=float).reshape(-1, 1)
        variance = float(np.var(signal))

        if variance == 0.0:
            return PostHocConvergenceResult(
                convergence_epoch=1,
                change_points=[],
                segments=[segment],
                plateau_ranges=[(segment.start_epoch, segment.end_epoch)],
            )
        
        penalty = self.penalty
        if penalty is None:
            penalty = self.penalty_scale * variance * math.log(n)

        breakpoints = rpt.Pelt(
            model=self.model,
            min_size=self.min_size,
            jump=self.jump
        ).fit(signal).predict(pen=penalty)

        starts = [0] + breakpoints[: -1]
        segments = [
            self._build_segment(epoch_history, start, end)
            for start, end in zip(starts, breakpoints)
        ]

        plateau_ranges = [
            (segment.start_epoch, segment.end_epoch)
            for index, segment in enumerate(segments)
            if self._is_plateau(segment, index) 
            and not self._is_mean_stair_step(segments, index)
        ]

        convergence_epoch = plateau_ranges[0][0] if plateau_ranges else None

        return PostHocConvergenceResult(
            convergence_epoch=convergence_epoch,
            change_points=breakpoints[:-1],
            segments=segments,
            plateau_ranges=plateau_ranges
        )

    def _build_segment(self, epoch_history: list[int], start: int, end: int) -> PostHocSegment:
        values = epoch_history[start:end]
        slope = self._slope(values)
        mean  = statistics.mean(values)

        relative_total_drift = self._relative_total_drift(
            mean=mean,
            slope=slope,
            length= end - start
        )

        return PostHocSegment(
            start_epoch=start + 1,
            end_epoch=end,
            length=end - start,
            mean=mean,
            std=statistics.stdev(values) if len(values) > 1 else 0.0,
            slope=slope,
            relative_total_drift=relative_total_drift
        )
    
    def _slope(self, values: list[int]) -> float:
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values), dtype=float)
        y = np.asarray(values, dtype=float)

        slope, _ = np.polyfit(x, y, deg=1)
        return float(slope)
    
    def _relative_total_drift(self, mean: float, slope: float, length: int) -> float:
        if mean == 0:
            return 0.0 if slope == 0 else float("inf")
        
        total_drift = abs(slope) * max(length - 1, 0)
        return total_drift / abs(mean)
    
    def _is_mean_stair_step(self, segments, index) -> bool:
        if index == 0 or index == len(segments) - 1:
            return False
        
        prev_mean = segments[index - 1].mean
        curr_mean = segments[index].mean
        next_mean = segments[index + 1].mean

        scale = max(abs(curr_mean), 1e-9)

        drop_from_prev = (prev_mean - curr_mean) / scale
        drop_to_next = (curr_mean - next_mean) / scale

        rise_from_prev = (curr_mean - prev_mean) / scale
        rise_to_next = (next_mean - curr_mean) / scale

        descending = (
            drop_from_prev >= self.min_relative_regime_step
            and drop_to_next >= self.min_relative_regime_step
        )

        ascending = (
            rise_from_prev >= self.min_relative_regime_step
            and rise_to_next >= self.min_relative_regime_step
        )
        return descending or ascending
    
    def _is_plateau(self, segment: PostHocSegment, index: int) -> bool:
        if self.ignore_first_segment and index == 0:
            return False
        
        if segment.length < self.min_plateau_epochs:
            return False
        
        return segment.relative_total_drift <= self.max_relative_total_drift


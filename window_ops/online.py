# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/online.ipynb.

# %% auto 0
__all__ = ['RollingMean', 'RollingMax', 'RollingMin', 'RollingStd', 'SeasonalRollingMean', 'SeasonalRollingStd',
           'SeasonalRollingMin', 'SeasonalRollingMax', 'ExpandingMean', 'ExpandingMax', 'ExpandingMin', 'ExpandingStd',
           'SeasonalExpandingMean', 'SeasonalExpandingStd', 'SeasonalExpandingMin', 'SeasonalExpandingMax', 'EWMMean',
           'Shift']

# %% ../nbs/online.ipynb 3
from math import ceil, sqrt
from typing import Callable, List, Optional, Union

import numpy as np

from .expanding import *
from .ewm import *
from .rolling import *
from .rolling import _rolling_std
from .shift import shift_array

# %% ../nbs/online.ipynb 8
class BaseOnlineRolling:
    
    def __init__(self, rolling_op: Callable, window_size: int, min_samples: Optional[int] = None):
        self.rolling_op = rolling_op
        self.window_size = window_size
        self.min_samples = min_samples or window_size
        
    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        self.window = tuple(x[-self.window_size:])
        return self.rolling_op(x, self.window_size, self.min_samples)
    
    def update(self, new: float) -> float:
        if len(self.window) < self.window_size:
            self.window += (new,)
            if len(self.window) < self.min_samples:
                return np.nan
        else:
            self.window = self.window[1:] + (new,)
        return self._update_op()

# %% ../nbs/online.ipynb 9
class RollingMean(BaseOnlineRolling):
    
    def __init__(self, window_size: int, min_samples: Optional[int] = None):
        super().__init__(rolling_mean, window_size, min_samples)
    
    def _update_op(self) -> float:
        return sum(self.window) / len(self.window)

# %% ../nbs/online.ipynb 11
class RollingMax(BaseOnlineRolling):
    
    def __init__(self, window_size: int, min_samples: Optional[int] = None):
        super().__init__(rolling_max, window_size, min_samples)
    
    def _update_op(self) -> float:
        return max(self.window)

# %% ../nbs/online.ipynb 13
class RollingMin(BaseOnlineRolling):
    
    def __init__(self, window_size: int, min_samples: Optional[int] = None):
        super().__init__(rolling_min, window_size, min_samples)
    
    def _update_op(self) -> float:
        return min(self.window)

# %% ../nbs/online.ipynb 15
class RollingStd(BaseOnlineRolling):
    
    def __init__(self, window_size: int, min_samples: Optional[int] = None):
        super().__init__(rolling_std, window_size, min_samples or window_size)
        
    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        result, self.curr_avg, self.m2 = _rolling_std(x, self.window_size, self.min_samples)
        if x.size < self.min_samples:
            _, self.curr_avg, self.m2 = _rolling_std(x, self.window_size, 2)
        self.window = tuple(x[-self.window_size:])
        return result
    
    def update(self, new: float) -> float:
        prev_avg = self.curr_avg
        if len(self.window) < self.window_size:
            self.window += (new,)
            self.curr_avg = prev_avg + (new - prev_avg) /  len(self.window)
            self.m2 += (new - prev_avg) * (new - self.curr_avg)
        else:
            old = self.window[0]
            self.window = self.window[1:] + (new,)
            self.curr_avg = prev_avg + (new - old) / len(self.window)
            self.m2 += (new - old) * (new - self.curr_avg + old - prev_avg)
        if len(self.window) < self.min_samples:
            return np.nan
        self.m2 = max(self.m2, 0) # loss of precision        
        return sqrt(self.m2 / (len(self.window) - 1))

# %% ../nbs/online.ipynb 19
class BaseOnlineSeasonalRolling:

    def __init__(self,
                 RollingOp: type,
                 season_length: int,
                 window_size: int,
                 min_samples: Optional[int] = None):
        self.RollingOp = RollingOp
        self.season_length = season_length
        self.window_size = window_size
        self.min_samples = min_samples

    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        self.rolling_ops = []
        self.n_samples = x.size
        result = np.full_like(x, np.nan)
        for season in range(self.season_length):
            rolling_op = self.RollingOp(window_size=self.window_size, min_samples=self.min_samples)
            result[season::self.season_length] = rolling_op.fit_transform(x[season::self.season_length])
            self.rolling_ops.append(rolling_op)
        return result

    def update(self, new: float) -> float:
        season = self.n_samples % self.season_length
        self.n_samples += 1
        return self.rolling_ops[season].update(new)

# %% ../nbs/online.ipynb 20
class SeasonalRollingMean(BaseOnlineSeasonalRolling):
    
    def __init__(self,
                 season_length: int,
                 window_size: int,
                 min_samples: Optional[int] = None):
        super().__init__(RollingMean, season_length, window_size, min_samples)

# %% ../nbs/online.ipynb 22
class SeasonalRollingStd(BaseOnlineSeasonalRolling):
    
    def __init__(self,
                 season_length: int,
                 window_size: int,
                 min_samples: Optional[int] = None):
        super().__init__(RollingStd, season_length, window_size, min_samples)

# %% ../nbs/online.ipynb 24
class SeasonalRollingMin(BaseOnlineSeasonalRolling):
    
    def __init__(self,
                 season_length: int,
                 window_size: int,
                 min_samples: Optional[int] = None):
        super().__init__(RollingMin, season_length, window_size, min_samples)

# %% ../nbs/online.ipynb 26
class SeasonalRollingMax(BaseOnlineSeasonalRolling):
    
    def __init__(self,
                 season_length: int,
                 window_size: int,
                 min_samples: Optional[int] = None):
        super().__init__(RollingMax, season_length, window_size, min_samples)

# %% ../nbs/online.ipynb 30
class ExpandingMean:
    
    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        exp_mean = expanding_mean(x)
        self.n = x.size
        self.cumsum = exp_mean[-1] * self.n
        return exp_mean
        
    def update(self, x: float) -> float:
        self.cumsum += x
        self.n += 1
        return self.cumsum / self.n

# %% ../nbs/online.ipynb 33
class ExpandingMax:
    
    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        exp_max = expanding_max(x)
        self.max = exp_max[-1]
        return exp_max
        
    def update(self, x: float) -> float:
        if x > self.max:
            self.max = x
        return self.max

# %% ../nbs/online.ipynb 35
class ExpandingMin:
    
    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        exp_min = expanding_min(x)
        self.min = exp_min[-1]
        return exp_min
        
    def update(self, x: float) -> float:
        if x < self.min:
            self.min = x
        return self.min

# %% ../nbs/online.ipynb 37
class ExpandingStd:
    
    def fit_transform(self, x):
        self.n = x.size
        exp_std, self.curr_avg, self.x_m2n = _rolling_std(x,
                                                          window_size=self.n,
                                                          min_samples=2)
        return exp_std
    
    def update(self, x):
        prev_avg = self.curr_avg
        self.n += 1
        self.curr_avg = prev_avg + (x - prev_avg) / self.n
        self.x_m2n += (x - prev_avg) * (x - self.curr_avg)
        return sqrt(self.x_m2n / (self. n - 1))

# %% ../nbs/online.ipynb 40
class BaseSeasonalExpanding:

    def __init__(self,
                 ExpandingOp: type,
                 season_length: int):
        self.ExpandingOp = ExpandingOp
        self.season_length = season_length

    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        self.expanding_ops = []
        self.n_samples = x.size
        result = np.empty(self.n_samples)
        for season in range(self.season_length):
            exp_op = self.ExpandingOp()
            result[season::self.season_length] = exp_op.fit_transform(x[season::self.season_length])
            self.expanding_ops.append(exp_op)
        return result

    def update(self, x: float) -> float:
        season = self.n_samples % self.season_length
        self.n_samples += 1
        return self.expanding_ops[season].update(x)

# %% ../nbs/online.ipynb 41
class SeasonalExpandingMean(BaseSeasonalExpanding):
    
    def __init__(self, season_length: int):
        super().__init__(ExpandingMean, season_length)

# %% ../nbs/online.ipynb 43
class SeasonalExpandingStd(BaseSeasonalExpanding):
    
    def __init__(self, season_length: int):
        super().__init__(ExpandingStd, season_length)

# %% ../nbs/online.ipynb 45
class SeasonalExpandingMin(BaseSeasonalExpanding):
    
    def __init__(self, season_length: int):
        super().__init__(ExpandingMin, season_length)

# %% ../nbs/online.ipynb 47
class SeasonalExpandingMax(BaseSeasonalExpanding):
    
    def __init__(self, season_length: int):
        super().__init__(ExpandingMax, season_length)

# %% ../nbs/online.ipynb 50
class EWMMean:
    
    def __init__(self, alpha):
        self.alpha = alpha
        
    def fit_transform(self, x):
        mn = ewm_mean(x, self.alpha)
        self.smoothed = mn[-1]
        return mn
    
    def update(self, x):
        self.smoothed = self.alpha * x + (1 - self.alpha) * self.smoothed
        return self.smoothed

# %% ../nbs/online.ipynb 53
class Shift:
    
    def __init__(self, offset: int):
        if offset <= 0:
            raise ValueError('offset must be positive.')
        self.offset = offset
        
    def fit_transform(self, x: np.ndarray) -> np.ndarray:
        self.window = tuple(x[-self.offset:])
        return shift_array(x, self.offset)
        
    def update(self, new: float) -> float:
        if len(self.window) < self.offset:
            self.window = self.window + (new,)
            return np.nan
        result = self.window[0]
        self.window = self.window[1:] + (new,)
        return result

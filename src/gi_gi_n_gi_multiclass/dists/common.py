from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass(frozen=True)
class Exponential:
    rate: float

    def sample(self, rng: np.random.Generator) -> float:
        if self.rate <= 0:
            raise ValueError("rate must be > 0")
        return float(rng.exponential(scale=1.0 / self.rate))

    def mean(self) -> Optional[float]:
        return 1.0 / self.rate

    def pdf(self, w: float) -> float:
        if w < 0.0:
            return 0.0
        return float(self.rate * np.exp(-self.rate * w))

    def cdf(self, w: float) -> float:
        if w < 0.0:
            return 0.0
        return float(1.0 - np.exp(-self.rate * w))

    def survival(self, w: float) -> float:
        if w < 0.0:
            return 1.0
        return float(np.exp(-self.rate * w))

    def hazard(self, w: float) -> float:
        if w < 0.0:
            return 0.0
        return float(self.rate)


@dataclass(frozen=True)
class Deterministic:
    value: float

    def sample(self, rng) -> float:
        return float(self.value)

    def mean(self) -> Optional[float]:
        return float(self.value)

    def cdf(self, w: float) -> float:
        return 0.0 if w < self.value else 1.0

    def survival(self, w: float) -> float:
        return 1.0 - self.cdf(w)

    def pdf(self, w: float) -> float:
        raise NotImplementedError("Deterministic has no density in the usual sense.")

    def hazard(self, w: float) -> float:
        raise NotImplementedError("Deterministic has no hazard in the usual sense.")


@dataclass(frozen=True)
class ErlangK:
    k: int
    rate: float

    def sample(self, rng: np.random.Generator) -> float:
        if self.k <= 0 or self.rate <= 0:
            raise ValueError("k and rate must be > 0")
        return float(rng.gamma(shape=self.k, scale=1.0 / self.rate))

    def mean(self) -> Optional[float]:
        return self.k / self.rate

    def pdf(self, w: float) -> float:
        if w < 0.0:
            return 0.0
        if self.k <= 0 or self.rate <= 0:
            raise ValueError("k and rate must be > 0")
        import math
        if w == 0.0:
            return 0.0 if self.k > 1 else float(self.rate)
        return float((self.rate ** self.k) * (w ** (self.k - 1)) * np.exp(-self.rate * w) / math.factorial(self.k - 1))

    def survival(self, w: float) -> float:
        if w < 0.0:
            return 1.0
        if self.k <= 0 or self.rate <= 0:
            raise ValueError("k and rate must be > 0")
        import math
        x = self.rate * w
        # Survival for integer-shape Gamma (Erlang):
        # S(w) = e^{-x} * sum_{i=0}^{k-1} x^i / i!
        s = 0.0
        for i in range(self.k):
            s += (x ** i) / math.factorial(i)
        return float(np.exp(-x) * s)

    def cdf(self, w: float) -> float:
        if w < 0.0:
            return 0.0
        return float(1.0 - self.survival(w))

    def hazard(self, w: float) -> float:
        sw = self.survival(w)
        if sw <= 0.0:
            return float("inf")
        return float(self.pdf(w) / sw)


@dataclass(frozen=True)
class Weibull:
    shape: float
    scale: float

    def sample(self, rng: np.random.Generator) -> float:
        if self.shape <= 0 or self.scale <= 0:
            raise ValueError("shape and scale must be > 0")
        return float(rng.weibull(a=self.shape) * self.scale)

    def mean(self) -> Optional[float]:
        import math
        return self.scale * math.gamma(1.0 + 1.0 / self.shape)

    def survival(self, w: float) -> float:
        if w < 0.0:
            return 1.0
        if self.shape <= 0 or self.scale <= 0:
            raise ValueError("shape and scale must be > 0")
        x = w / self.scale
        return float(np.exp(-(x ** self.shape)))

    def cdf(self, w: float) -> float:
        if w < 0.0:
            return 0.0
        return float(1.0 - self.survival(w))

    def pdf(self, w: float) -> float:
        if w < 0.0:
            return 0.0
        if self.shape <= 0 or self.scale <= 0:
            raise ValueError("shape and scale must be > 0")
        if w == 0.0:
            if self.shape < 1.0:
                return float("inf")
            if self.shape == 1.0:
                return float(1.0 / self.scale)
            return 0.0
        x = w / self.scale
        return float((self.shape / self.scale) * (x ** (self.shape - 1.0)) * np.exp(-(x ** self.shape)))

    def hazard(self, w: float) -> float:
        if w < 0.0:
            return 0.0
        if self.shape <= 0 or self.scale <= 0:
            raise ValueError("shape and scale must be > 0")
        if w == 0.0:
            if self.shape < 1.0:
                return float("inf")
            if self.shape == 1.0:
                return float(1.0 / self.scale)
            return 0.0
        x = w / self.scale
        return float((self.shape / self.scale) * (x ** (self.shape - 1.0)))


@dataclass(frozen=True)
class LogNormal:
    meanlog: float
    sdlog: float

    def sample(self, rng: np.random.Generator) -> float:
        if self.sdlog <= 0:
            raise ValueError("sdlog must be > 0")
        return float(rng.lognormal(mean=self.meanlog, sigma=self.sdlog))

    def mean(self) -> Optional[float]:
        import math
        return math.exp(self.meanlog + 0.5 * self.sdlog * self.sdlog)

    def _phi(self, z: float) -> float:
        # Standard normal CDF using erf
        import math
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

    def pdf(self, w: float) -> float:
        if w <= 0.0:
            return 0.0
        if self.sdlog <= 0:
            raise ValueError("sdlog must be > 0")
        import math
        z = (math.log(w) - self.meanlog) / self.sdlog
        return float((1.0 / (w * self.sdlog * math.sqrt(2.0 * math.pi))) * math.exp(-0.5 * z * z))

    def cdf(self, w: float) -> float:
        if w <= 0.0:
            return 0.0
        if self.sdlog <= 0:
            raise ValueError("sdlog must be > 0")
        import math
        z = (math.log(w) - self.meanlog) / self.sdlog
        return float(self._phi(z))

    def survival(self, w: float) -> float:
        if w <= 0.0:
            return 1.0
        return float(1.0 - self.cdf(w))

    def hazard(self, w: float) -> float:
        sw = self.survival(w)
        if sw <= 0.0:
            return float("inf")
        return float(self.pdf(w) / sw)
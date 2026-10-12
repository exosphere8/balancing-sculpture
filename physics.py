"""
Physics model of the "impossible" balancing sculpture.

The sculpture is a rigid body resting on a single pivot (the figure's foot).
Every part is modelled as a point mass at (x, y), with the pivot at the origin
and y pointing up. Lengths in metres, masses in kilograms.

    total mass            M     = sum(m_i)
    centre of mass        r_cm  = sum(m_i r_i) / M
    depth below pivot     d     = -y_cm
    moment of inertia     I     = sum(m_i (x_i^2 + y_i^2))       (in-plane rocking)
    equation of motion    I θ'' = -M g d sin θ - c θ'
    small-angle period    T     = 2π sqrt(I / (M g d))
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict

import numpy as np
from scipy.integrate import solve_ivp

G = 9.81


@dataclass
class PointMass:
    name: str
    m: float  # kg
    x: float  # m (horizontal, along the arms)
    y: float  # m (vertical, + is up)


@dataclass
class Sculpture:
    parts: list[PointMass] = field(default_factory=lambda: [
        PointMass("figure", 0.160, 0.005, 0.08),
        PointMass("left weight", 0.240, -0.12, -0.28),
        PointMass("right weight", 0.200, 0.14, -0.16),
    ])
    damping: float = 0.004  # N·m·s/rad, air drag + friction at the foot

    # ---- static quantities -------------------------------------------------
    @property
    def M(self) -> float:
        return sum(p.m for p in self.parts)

    @property
    def com(self) -> tuple[float, float]:
        M = self.M
        return (sum(p.m * p.x for p in self.parts) / M,
                sum(p.m * p.y for p in self.parts) / M)

    @property
    def net_torque_moment(self) -> float:
        """Σ m x  (kg·m). Zero means no tipping torque at θ = 0."""
        return sum(p.m * p.x for p in self.parts)

    @property
    def d(self) -> float:
        """Depth of the centre of mass below the pivot (positive = stable)."""
        return -self.com[1]

    @property
    def I(self) -> float:
        return sum(p.m * (p.x ** 2 + p.y ** 2) for p in self.parts)

    @property
    def stiffness(self) -> float:
        """Restoring torque per radian for small angles, M g d (N·m)."""
        return self.M * G * self.d

    @property
    def stable(self) -> bool:
        return self.d > 0

    @property
    def omega(self) -> float:
        return math.sqrt(self.stiffness / self.I) if self.stable else float("nan")

    @property
    def period(self) -> float:
        return 2 * math.pi / self.omega if self.stable else float("nan")

    @property
    def equivalent_length(self) -> float:
        """Length of a simple pendulum with the same period: I / (M d)."""
        return self.I / (self.M * self.d) if self.stable else float("nan")

    @property
    def growth_rate(self) -> float:
        """For an unstable body (d < 0): θ grows like cosh(λ t)."""
        return math.sqrt(-self.stiffness / self.I) if not self.stable else 0.0

    # ---- dynamics -------------------------------------------------------------
    def rhs(self, t, state):
        theta, omega = state
        alpha = (-self.stiffness * math.sin(theta) - self.damping * omega) / self.I
        return [omega, alpha]

    def simulate(self, theta0_deg: float = 15.0, t_max: float = 12.0, fps: int = 60):
        t_eval = np.linspace(0, t_max, int(t_max * fps) + 1)
        sol = solve_ivp(self.rhs, (0, t_max), [math.radians(theta0_deg), 0.0],
                        t_eval=t_eval, rtol=1e-9, atol=1e-11)
        return sol.t, sol.y[0], sol.y[1]

    def potential(self, theta: np.ndarray) -> np.ndarray:
        """U(θ) = -M g d cos θ (zero reference at the pivot height)."""
        return -self.M * G * self.d * np.cos(theta)

    def summary(self) -> dict:
        xc, yc = self.com
        return {
            "parts": [asdict(p) for p in self.parts],
            "M": self.M,
            "com": [xc, yc],
            "sum_mx": self.net_torque_moment,
            "d": self.d,
            "I": self.I,
            "stiffness": self.stiffness,
            "omega": self.omega,
            "period": self.period,
            "equivalent_length": self.equivalent_length,
            "damping": self.damping,
        }


def without_weights() -> Sculpture:
    """The bare figure on its toe: centre of mass above the pivot."""
    return Sculpture(parts=[PointMass("figure", 0.160, 0.0, 0.08)])


def topple_time(s: Sculpture, theta0_deg=1.0, theta_end_deg=30.0) -> float:
    lam = s.growth_rate
    return math.acosh(theta_end_deg / theta0_deg) / lam


if __name__ == "__main__":
    s = Sculpture()
    info = s.summary()
    print(json.dumps(info, indent=2))
    bare = without_weights()
    print(f"\nWithout weights: λ = {bare.growth_rate:.2f} s⁻¹, "
          f"1° → 30° in {topple_time(bare):.2f} s")

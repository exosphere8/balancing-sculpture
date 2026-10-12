"""Sanity checks for the physics model. Run with:  pytest"""

import math

import numpy as np
import pytest

from physics import PointMass, Sculpture, topple_time, without_weights


@pytest.fixture
def s():
    return Sculpture()


def test_total_mass(s):
    assert s.M == pytest.approx(0.600)


def test_torques_balance_at_upright(s):
    # Σ m x = 0  ->  no tipping torque at θ = 0
    assert s.net_torque_moment == pytest.approx(0.0, abs=1e-12)
    assert s.com[0] == pytest.approx(0.0, abs=1e-12)


def test_centre_of_mass_below_pivot(s):
    assert s.com[1] == pytest.approx(-0.144)
    assert s.d == pytest.approx(0.144)
    assert s.stable


def test_moment_of_inertia(s):
    assert s.I == pytest.approx(0.03234, rel=1e-6)


def test_period_and_equivalent_length(s):
    assert s.stiffness == pytest.approx(0.8476, rel=1e-3)
    assert s.omega == pytest.approx(5.12, abs=0.01)
    assert s.period == pytest.approx(1.23, abs=0.01)
    assert s.equivalent_length == pytest.approx(0.374, abs=0.001)


def test_simulated_period_matches_formula():
    s = Sculpture(damping=0.0)
    t, theta, _ = s.simulate(theta0_deg=2, t_max=10, fps=2000)
    # upward zero crossings
    idx = np.where((theta[:-1] < 0) & (theta[1:] >= 0))[0]
    crossings = t[idx] - theta[idx] * (t[idx + 1] - t[idx]) / (theta[idx + 1] - theta[idx])
    measured = np.mean(np.diff(crossings))
    assert measured == pytest.approx(s.period, rel=1e-3)


def test_energy_conserved_without_damping():
    s = Sculpture(damping=0.0)
    _, theta, omega = s.simulate(theta0_deg=20, t_max=5, fps=200)
    energy = 0.5 * s.I * omega ** 2 + s.potential(theta)
    assert np.ptp(energy) < 1e-6 * abs(energy[0])


def test_damping_decays_motion():
    s = Sculpture(damping=0.01)
    _, theta, _ = s.simulate(theta0_deg=15, t_max=30, fps=60)
    assert abs(theta[-60:]).max() < math.radians(15) * 0.5


def test_bare_figure_is_unstable_and_falls_fast():
    bare = without_weights()
    assert not bare.stable
    assert math.isnan(bare.period)
    assert bare.growth_rate == pytest.approx(math.sqrt(9.81 / 0.08), rel=1e-6)
    assert topple_time(bare) == pytest.approx(0.37, abs=0.01)


def test_lopsided_weights_create_tipping_torque():
    s = Sculpture(parts=[
        PointMass("figure", 0.160, 0.005, 0.08),
        PointMass("left", 0.300, -0.12, -0.28),
        PointMass("right", 0.200, 0.14, -0.16),
    ])
    assert s.net_torque_moment < 0

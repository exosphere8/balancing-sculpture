# The physics, in full

This is the derivation behind `physics.py`, the Manim scene and the web app. The masses and positions are estimates read off the viral video, not measurements, so treat the numbers as a worked example rather than the real sculpture's specs.

## 1. Model

The sculpture is a rigid body resting on a single pivot, the figure's toe. Each part is a point mass. Put the pivot at the origin, with *x* horizontal along the arms and *y* pointing up.

| Part | Mass *m* | *x* | *y* |
|---|---|---|---|
| Figure | 160 g | +0.5 cm | +8 cm |
| Left weight | 240 g | −12 cm | −28 cm |
| Right weight | 200 g | +14 cm | −16 cm |

Total mass *M* = 600 g. The thin steel arms are ignored; their mass is small and sits mostly near the weights anyway.

## 2. Equilibrium: no net torque

Gravity pulls each mass straight down with force *mᵢg*. About the pivot, that force has lever arm *xᵢ*, so the total torque at θ = 0 is

$$
\tau_0 = -g\sum_i m_i x_i .
$$

Upright is an equilibrium only when this vanishes, which is the same as saying the centre of mass sits directly above or below the foot:

$$
\sum_i m_i x_i = 160(0.5) + 240(-12) + 200(14) = 80 - 2880 + 2800 = 0 .
$$

This is why the arms look lopsided. The heavier left weight sits closer in and the lighter right weight sits farther out; their moments cancel.

## 3. Stability: which side of the foot is the centre of mass?

$$
y_\text{cm} = \frac{\sum m_i y_i}{M} = \frac{160(8) - 240(28) - 200(16)}{600} = -14.4\ \text{cm}.
$$

So the centre of mass hangs a distance **d = 14.4 cm below the foot**. Equivalently, the weights' downward moment beats the figure's upward one:

$$
m_1 L_1 + m_2 L_2 > m_f h_f \quad\Longrightarrow\quad 240(28) + 200(16) = 9920 > 160(8) = 1280 .
$$

## 4. Energy and restoring torque

Tilt the rigid body by θ. The centre of mass moves on a circle of radius *d* about the pivot, so its height is −*d* cos θ and

$$
U(\theta) = -Mgd\cos\theta,
\qquad
\tau(\theta) = -\frac{dU}{d\theta} = -Mgd\sin\theta .
$$

*U* has its minimum at θ = 0. Any tilt lifts the centre of mass, and the torque always points back toward upright.

For a body that is *not* torque-balanced (centre of mass at $(x_c, y_c)$ with $x_c \neq 0$), the general forms used by the web app are

$$
U(\theta) = Mg\,(x_c\sin\theta + y_c\cos\theta),
\qquad
\tau(\theta) = -Mg\,(x_c\cos\theta - y_c\sin\theta),
$$

and the body settles at the tilt $\theta^*$ where the centre of mass is straight below the pivot, $x_c\cos\theta^* = y_c\sin\theta^*$. That is the "Unbalanced" preset.

## 5. Equation of motion

Newton's second law for rotation about the fixed pivot, with a linear damping term *c* for air drag and friction at the toe:

$$
I\,\ddot\theta = -Mgd\sin\theta - c\,\dot\theta,
\qquad
I = \sum_i m_i\,(x_i^2 + y_i^2).
$$

This is exactly the equation of a damped physical pendulum.

Moment of inertia, part by part (g·cm²):

| Part | *x² + y²* | *m (x² + y²)* |
|---|---|---|
| Figure | 64.25 | 10 280 |
| Left weight | 928 | 222 720 |
| Right weight | 452 | 90 400 |
| **Total** | | **323 400 g·cm² = 0.0323 kg·m²** |

For rocking front-to-back (out of the plane of the arms) the *x²* terms drop out, giving *I* ≈ 0.025 kg·m².

## 6. Period

For small angles, sin θ ≈ θ and the motion is simple harmonic:

$$
\omega = \sqrt{\frac{Mgd}{I}} = \sqrt{\frac{0.6 \times 9.81 \times 0.144}{0.0323}} = \sqrt{\frac{0.848}{0.0323}} \approx 5.12\ \text{rad/s},
\qquad
T = \frac{2\pi}{\omega} \approx 1.23\ \text{s}.
$$

A simple pendulum with the same period would be

$$
L_\text{eq} = \frac{I}{Md} \approx 37\ \text{cm}
$$

long, even though the centre of mass is only 14 cm down. Putting the mass far from the pivot inflates *I*, which is why the sway looks slow and floaty. Rocking front-to-back is a little quicker, *T* ≈ 1.08 s.

## 7. Remove the weights

The bare figure has its centre of mass *h* = 8 cm **above** the toe. The sign of the torque flips:

$$
\ddot\theta = +\frac{g}{h}\,\theta
\quad\Longrightarrow\quad
\theta(t) = \theta_0\cosh(\lambda t),
\qquad
\lambda = \sqrt{g/h} = \sqrt{9.81/0.08} \approx 11.1\ \text{s}^{-1}.
$$

(The figure is treated as a point mass at its centre of mass, so *I* = *mh²*.) A 1° wobble reaches 30° when cosh(λt) = 30:

$$
t = \frac{\operatorname{arcosh}(30)}{\lambda} \approx \frac{4.09}{11.1} \approx 0.37\ \text{s}.
$$

Without the weights it falls in about a third of a second.

## 8. Measuring the real sculpture

Rearrange the period formula to read the hidden depth straight from a stopwatch:

$$
d = \frac{4\pi^2 I}{MgT^2}.
$$

Time ten swings in the video, divide by ten, and plug in. The web app's last section does this for you.

## Where else this shows up

- **Balancing-bird toys** — the wingtips carry weights below the beak.
- **Tightrope walkers' poles** — a long, drooping pole adds a large moment of inertia and lowers the centre of mass, slowing any fall.
- **Ship stability** — ballast keeps a hull's centre of gravity low so heeling produces a righting moment.

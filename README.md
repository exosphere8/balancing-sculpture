# The Balancing Sculpture

A steel figure stands on one toe on a tiny plate, arms swept back to two hanging weights. It wobbles but never falls. It looks like it defies physics, but it is a physical pendulum in disguise: the weights pull the combined centre of mass **below** the foot, so upright is the position of minimum potential energy.

This repo explains it three ways:

- **`physics.py`** — the model: centre of mass, torque balance, moment of inertia, period, and an ODE simulation (`scipy.integrate.solve_ivp`).
- **`scene.py`** — a Manim animation built from the same model.
- **`web/`** — an interactive page (HTML/CSS/JS) with a live simulation you can drag, sliders for every mass and arm, θ(t) and U(θ) plots, and the full derivation.

## Run it

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt     # Manim also needs ffmpeg, LaTeX and Pango system libs
python render.py                    # renders the video (1080p30) + exports web/assets/data.json
python render.py --quick            # fast 480p preview
python -m http.server -d web 8000   # open http://localhost:8000
```

`python physics.py` prints the numbers on their own.

## The numbers

Estimated from the video: figure 160 g, weights 240 g and 200 g. Pivot at the origin, *y* up.

| Part | Mass | x | y |
|---|---|---|---|
| Figure | 160 g | +0.5 cm | +8 cm |
| Left weight | 240 g | −12 cm | −28 cm |
| Right weight | 200 g | +14 cm | −16 cm |

| Quantity | Formula | Value |
|---|---|---|
| Tipping moment | Σ m x | 0 (balanced) |
| CoM depth below foot | d = −Σ m y / M | 14.4 cm |
| Moment of inertia | I = Σ m (x² + y²) | 0.0323 kg·m² |
| Restoring stiffness | M g d | 0.848 N·m |
| Small-angle period | T = 2π √(I / M g d) | 1.23 s |
| Equivalent pendulum | I / (M d) | 37 cm |
| Without the weights | θ = θ₀ cosh(λt), λ = √(g/h) | 1° → 30° in 0.37 s |

Equation of motion: `I θ'' = −M g d sin θ − c θ'`.

## Layout

```
physics.py      physics model + simulation
scene.py        Manim scenes
render.py       one-command build: data export + video render
web/
  index.html    page
  style.css
  app.js        live RK4 simulation, plots, calculator
  assets/       rendered video, poster frame, data.json
```

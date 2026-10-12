# Web app

A static page — plain HTML, CSS and JavaScript, no build step — that explains the sculpture and lets you play with it.

## Run

```bash
# from the repo root
python -m http.server -d web 8000
# open http://localhost:8000
```

Serve it over HTTP rather than opening `index.html` directly, so the page can load `assets/data.json`. (It still works from `file://`, using built-in default values.)

## Files

| File | What it does |
|---|---|
| `index.html` | Page structure: animation, live lab, derivation, period calculator |
| `style.css` | Dark steel-and-amber theme, responsive down to phone width |
| `app.js` | Physics, RK4 integrator, canvas drawing, plots, controls |
| `assets/balancing_sculpture.mp4` | Manim render, produced by `render.py` |
| `assets/poster.jpg` | Poster frame for the video |
| `assets/data.json` | Model values and a reference trajectory exported from `physics.py` |

## The live lab

- **Drag** the sculpture to tip it, then let go.
- **Sliders** change the figure mass and each weight's mass, reach (*x*) and drop (*y*), plus damping.
- **Presets**
  - *The sculpture* — the estimated real configuration.
  - *No weights* — the bare figure; topples in about 0.4 s.
  - *Short arms* — weights too high, so the centre of mass ends up above the foot.
  - *Unbalanced* — a heavier left weight; still stable, but it settles leaning about 4°.
- **Readouts**: total mass, centre of mass, depth *d*, tipping moment Σ m·x, moment of inertia, stiffness *Mgd*, period and equivalent pendulum length.
- **Plots**: θ(t) over the last 10 s, and the potential energy U(θ) with a ball marking the current state. The shaded edges are angles the stand would block.

## How the simulation works

Each frame, `app.js` integrates

```
I θ'' = −M g (x_c cos θ − y_c sin θ) − c θ'
```

with fourth-order Runge–Kutta at 480 steps per second. This is the general rigid-body form, so it also handles configurations whose centre of mass isn't directly under the foot. Past ±77° the figure would hit the stand, so the simulation stops there and reports a topple.

## Third-party resources

Loaded from CDNs at runtime: [KaTeX](https://katex.org) (MIT) for equations, and Google Fonts (Instrument Serif, IBM Plex Sans, JetBrains Mono — all under the SIL Open Font License).

# Contributing

Ideas, fixes and better estimates of the real sculpture's masses are welcome.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Rendering the animation also needs ffmpeg, LaTeX with `dvisvgm`, and the Pango/Cairo dev libraries (see the [Manim install guide](https://docs.manim.community/en/stable/installation.html)).

## Guidelines

- **Keep one source of truth.** Numbers live in `physics.py`. If you change the model, run `python render.py` so the video and `web/assets/data.json` stay in sync, and update the tables in `README.md` and `docs/PHYSICS.md`.
- **Add a test** for any new physics in `tests/test_physics.py`.
- **The web app has no build step.** Keep it plain HTML/CSS/JS and check it at phone width.
- **Commits**: short imperative subject line (`Add front-to-back rocking mode`), with a body if the why isn't obvious.

## Reporting a problem

Open an issue with what you expected, what happened, and your OS / Python / Manim versions if it's a rendering problem.

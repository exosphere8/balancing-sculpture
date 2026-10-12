"""
One-command build: run the physics, export data for the web app, render the
Manim video, and copy everything into web/.

    python render.py            # 1080p
    python render.py --quick    # 480p preview
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from physics import Sculpture, without_weights, topple_time

ROOT = Path(__file__).parent
WEB = ROOT / "web"
ASSETS = WEB / "assets"


def export_data() -> Path:
    s = Sculpture()
    t, theta, omega = s.simulate(theta0_deg=15, t_max=12, fps=60)
    bare = without_weights()
    data = {
        "sculpture": s.summary(),
        "bare_figure": {
            "growth_rate": bare.growth_rate,
            "topple_1_to_30_deg_s": topple_time(bare),
        },
        "trajectory": {
            "t": [round(x, 4) for x in t],
            "theta_deg": [round(math.degrees(x), 4) for x in theta],
        },
    }
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / "data.json"
    out.write_text(json.dumps(data, indent=1))
    print(f"wrote {out}")
    return out


def render_video(quick: bool) -> None:
    quality = "-ql" if quick else "-qh"
    media = ROOT / "media"
    cmd = [sys.executable, "-m", "manim", quality, "--fps", "30", "--media_dir", str(media),
           str(ROOT / "scene.py"), "BalancingSculpture"]
    subprocess.run(cmd, check=True)
    folder = "480p15" if quick else "1080p30"
    video = media / "videos" / "scene" / folder / "BalancingSculpture.mp4"
    shutil.copy(video, ASSETS / "balancing_sculpture.mp4")
    # poster frame for the web page
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "40", "-i", str(video),
                    "-frames:v", "1", str(ASSETS / "poster.jpg")], check=True)
    print(f"copied video + poster into {ASSETS}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="low-quality preview render")
    ap.add_argument("--data-only", action="store_true", help="skip the video render")
    args = ap.parse_args()
    export_data()
    if not args.data_only:
        render_video(args.quick)

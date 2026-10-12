"""
Manim animation: why the "physics-defying" balancing sculpture stays upright.

Render with:
    python render.py              # renders the video and exports data for the web app
or directly:
    manim -qh scene.py BalancingSculpture
"""

from __future__ import annotations

import math

import numpy as np
from manim import *

from physics import Sculpture, without_weights, topple_time

# ----------------------------------------------------------------------------
# Palette
BG = "#14161a"
STEEL = "#c9ccd1"
STEEL_DARK = "#8a8f98"
WARM = "#ffb347"     # centre of mass / energy
COOL = "#5ec8e5"     # pivot / geometry
RED = "#ff6b6b"
GREEN = "#7fd88f"

SCALE = 10.0                      # manim units per metre
PIVOT = np.array([-3.6, 1.0, 0])  # screen position of the foot

config.background_color = BG


def P(x, y):
    """Sculpture-frame metres -> screen point (before rotation)."""
    return PIVOT + SCALE * np.array([x, y, 0.0])


def sculpture_body(s: Sculpture, with_weights: bool = True) -> VGroup:
    """Stick-figure sculpture drawn in the body frame (θ = 0)."""
    figure = VGroup(
        VMobject(stroke_color=STEEL, stroke_width=7).set_points_as_corners(
            [P(0, 0), P(-0.02, 0.035), P(0.012, 0.055)]).set_stroke(width=10),  # legs
        Line(P(0.012, 0.055), P(-0.006, 0.105), color=STEEL, stroke_width=16),  # torso
        Circle(radius=0.17, color=STEEL, fill_opacity=1)
        .move_to(P(-0.012, 0.125)),                                     # head
    )
    if not with_weights:
        return figure

    left, right = s.parts[1], s.parts[2]
    left_arm = CubicBezier(P(-0.006, 0.097), P(-0.07, 0.11), P(-0.135, 0.05),
                           P(left.x, left.y + 0.03), color=STEEL_DARK, stroke_width=4)
    right_arm = CubicBezier(P(-0.002, 0.097), P(0.08, 0.095), P(0.15, 0.01),
                            P(right.x, right.y + 0.025), color=STEEL_DARK, stroke_width=4)
    w_left = RoundedRectangle(corner_radius=0.05, width=0.24, height=0.62,
                              color=STEEL, fill_color="#3a3d44", fill_opacity=1
                              ).move_to(P(left.x, left.y))
    w_right = RoundedRectangle(corner_radius=0.05, width=0.22, height=0.5,
                               color=STEEL, fill_color="#3a3d44", fill_opacity=1
                               ).move_to(P(right.x, right.y))
    return VGroup(left_arm, right_arm, w_left, w_right, *figure)


def stand() -> VGroup:
    rod = Line(PIVOT + DOWN * 0.08, PIVOT + DOWN * 4.3, color="#55595f", stroke_width=6)
    plate = Rectangle(width=0.9, height=0.07, color="#6b7078", fill_opacity=1
                      ).move_to(PIVOT + DOWN * 0.04)
    base = Rectangle(width=1.6, height=0.12, color="#55595f", fill_opacity=1
                     ).move_to(PIVOT + DOWN * 4.36)
    return VGroup(rod, base, plate)


def com_point(s: Sculpture, theta: float) -> np.ndarray:
    xc, yc = s.com
    v = SCALE * np.array([xc, yc, 0.0])
    return PIVOT + rotate_vector(v, theta)


# ----------------------------------------------------------------------------
class BalancingSculpture(Scene):
    def construct(self):
        s = Sculpture()
        self.intro()
        self.build_and_find_com(s)
        self.equilibrium_math(s)
        self.oscillate(s)
        self.period_math(s)
        self.without_the_weights()
        self.outro(s)

    # -------------------------------------------------------------- 1. title
    def intro(self):
        title = Text("The sculpture that “defies” physics", font_size=46, color=STEEL)
        sub = Text("It doesn't. It's a pendulum in disguise.", font_size=30, color=WARM)
        sub.next_to(title, DOWN, buff=0.4)
        self.play(Write(title), run_time=1.6)
        self.play(FadeIn(sub, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(title), FadeOut(sub))

    # ------------------------------------------------- 2. where is the CoM?
    def build_and_find_com(self, s: Sculpture):
        self.stand = stand()
        self.body = sculpture_body(s)
        pivot_dot = Dot(PIVOT, color=COOL, radius=0.07)
        self.pivot_dot = pivot_dot

        self.play(FadeIn(self.stand), run_time=0.8)
        self.play(Create(self.body), run_time=2.5)
        self.play(GrowFromCenter(pivot_dot))
        pivot_lbl = Text("pivot (one foot)", font_size=22, color=COOL
                         ).next_to(pivot_dot, DR, buff=0.2).shift(RIGHT * 0.15)
        self.play(FadeIn(pivot_lbl))

        heading = Text("Where is the centre of mass?", font_size=32, color=STEEL
                       ).to_edge(UP).shift(RIGHT * 2.6)
        self.play(Write(heading))

        # part masses
        mass_dots, mass_labels = VGroup(), VGroup()
        for p, d in zip(s.parts, [UR, LEFT, RIGHT]):
            dot = Dot(P(p.x, p.y), radius=0.06 + 0.25 * p.m, color=WARM, fill_opacity=0.85)
            lbl = MathTex(f"{p.m * 1000:.0f}\\,\\text{{g}}", font_size=28, color=WARM
                          ).next_to(dot, d, buff=0.18)
            mass_dots.add(dot)
            mass_labels.add(lbl)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in mass_dots], lag_ratio=0.3),
                  LaggedStart(*[FadeIn(l) for l in mass_labels], lag_ratio=0.3))

        formula = MathTex(r"\vec r_{\text{cm}} = \frac{\sum m_i \vec r_i}{\sum m_i}",
                          font_size=40).next_to(heading, DOWN, buff=0.5)
        self.play(Write(formula))
        self.wait(0.5)

        com = com_point(s, 0)
        com_dot = Dot(com, radius=0.13, color=WARM)
        com_ring = Circle(radius=0.22, color=WARM).move_to(com)
        self.play(*[d.animate.move_to(com).set_opacity(0.0) for d in mass_dots],
                  FadeOut(mass_labels), run_time=1.6)
        self.play(GrowFromCenter(com_dot), Create(com_ring))
        com_lbl = Text("centre of mass", font_size=22, color=WARM
                       ).next_to(com_ring, RIGHT, buff=0.2).shift(DOWN * 0.75)

        brace = BraceBetweenPoints(PIVOT + LEFT * 0.35, com + LEFT * 0.35, direction=LEFT,
                                   color=COOL)
        d_lbl = MathTex(rf"d = {s.d * 100:.1f}\,\text{{cm}}", font_size=30, color=COOL
                        ).next_to(brace, LEFT, buff=0.1)
        self.play(FadeIn(com_lbl), GrowFromCenter(brace), Write(d_lbl))

        key = Text("It sits BELOW the foot.", font_size=30, color=WARM
                   ).next_to(formula, DOWN, buff=0.6)
        self.play(Write(key))
        self.wait(1.5)

        self.com_dot, self.com_ring = com_dot, com_ring
        self.play(FadeOut(VGroup(heading, formula, key, com_lbl, brace, d_lbl, pivot_lbl,
                                 mass_dots)))

    # -------------------------------------------------- 3. torque balance
    def equilibrium_math(self, s: Sculpture):
        heading = Text("1 · Equilibrium", font_size=32, color=STEEL).to_edge(UP).shift(RIGHT * 2.6)
        lines = VGroup(
            MathTex(r"\sum \tau = g\sum m_i x_i = 0", font_size=36),
            MathTex(r"160(0.5) + 240(-12) + 200(14)", font_size=30, color=STEEL_DARK),
            MathTex(r"= 80 - 2880 + 2800 = 0 \;\checkmark", font_size=30, color=GREEN),
            MathTex(r"y_{\text{cm}} = \frac{160(8) - 240(28) - 200(16)}{600}", font_size=30),
            MathTex(rf"= {s.com[1] * 100:.1f}\,\text{{cm}} \;\Rightarrow\; \text{{stable}}",
                    font_size=32, color=WARM),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.32).next_to(heading, DOWN, buff=0.5)
        lines.shift(RIGHT * 0.2)
        note = Text("lopsided arms, balanced torques", font_size=22, color=STEEL_DARK
                    ).next_to(lines, DOWN, buff=0.45)

        self.play(Write(heading))
        for ln in lines:
            self.play(Write(ln), run_time=1.0)
        self.play(FadeIn(note))
        self.wait(2)
        self.play(FadeOut(VGroup(heading, lines, note)))

    # ---------------------------------------------------- 4. the wobble
    def oscillate(self, s: Sculpture):
        t_max = 8.0
        ts, thetas, _ = s.simulate(theta0_deg=15, t_max=t_max, fps=120)
        theta_of = lambda t: float(np.interp(t, ts, thetas))

        clock = ValueTracker(0.0)
        self.remove(self.body, self.com_dot, self.com_ring)

        body = always_redraw(lambda: sculpture_body(s).rotate(
            theta_of(clock.get_value()), about_point=PIVOT))
        com_dot = always_redraw(lambda: Dot(com_point(s, theta_of(clock.get_value())),
                                            radius=0.13, color=WARM))
        gravity = always_redraw(lambda: Arrow(
            com_point(s, theta_of(clock.get_value())),
            com_point(s, theta_of(clock.get_value())) + DOWN * 1.1,
            buff=0, color=RED, stroke_width=5, max_tip_length_to_length_ratio=0.2))
        plumb = DashedLine(PIVOT, PIVOT + DOWN * 2.6, color=COOL, stroke_width=2,
                           dash_length=0.08)
        lever = always_redraw(lambda: Line(PIVOT, com_point(s, theta_of(clock.get_value())),
                                           color=WARM, stroke_width=3))

        self.add(body, com_dot)
        heading = Text("2 · Tip it", font_size=32, color=STEEL).to_edge(UP).shift(RIGHT * 2.6)
        self.play(Write(heading), Create(plumb), FadeIn(lever), FadeIn(gravity))

        # graph θ(t)
        axes = Axes(x_range=[0, t_max, 2], y_range=[-16, 16, 8], x_length=5.6, y_length=2.6,
                    axis_config={"color": STEEL_DARK, "include_tip": False},
                    x_axis_config={"numbers_to_include": [2, 4, 6, 8]},
                    y_axis_config={"numbers_to_include": [-8, 8]},
                    ).move_to(RIGHT * 2.9 + DOWN * 0.9)
        ax_lbls = VGroup(
            MathTex(r"t\,(\text{s})", font_size=26).next_to(axes.x_axis, DOWN + RIGHT, buff=0.1),
            MathTex(r"\theta\,(^\circ)", font_size=26).next_to(axes.y_axis, UP, buff=0.1),
        )
        eq = MathTex(r"I\,\ddot\theta = -Mgd\,\sin\theta - c\,\dot\theta", font_size=36
                     ).next_to(heading, DOWN, buff=0.45)
        torque_note = Text("gravity pulls the CoM back under the foot", font_size=22,
                           color=RED).next_to(eq, DOWN, buff=0.3)
        self.play(Create(axes), FadeIn(ax_lbls), Write(eq), FadeIn(torque_note))

        trace = always_redraw(lambda: axes.plot(
            lambda t: math.degrees(theta_of(t)), x_range=[0, max(clock.get_value(), 0.01), 0.02],
            color=WARM, stroke_width=3))
        self.add(trace)
        self.play(clock.animate.set_value(t_max), run_time=t_max, rate_func=linear)
        self.wait(0.5)

        self.clock_objs = VGroup(body, com_dot, gravity, lever, plumb, trace)
        self.play(FadeOut(VGroup(heading, eq, torque_note, axes, ax_lbls, trace, gravity,
                                 lever, plumb)))
        self.osc_body, self.osc_com = body, com_dot

    # ---------------------------------------------------- 5. the period
    def period_math(self, s: Sculpture):
        heading = Text("3 · Why the slow, floaty sway", font_size=32, color=STEEL
                       ).to_edge(UP).shift(RIGHT * 2.6)
        lines = VGroup(
            MathTex(r"T = 2\pi\sqrt{\frac{I}{Mgd}}", font_size=44),
            MathTex(r"I = \sum m_i (x_i^2 + y_i^2)", font_size=32),
            MathTex(rf"I \approx {s.I:.4f}\ \text{{kg m}}^2", font_size=32, color=STEEL_DARK),
            MathTex(rf"Mgd = {s.stiffness:.3f}\ \text{{N m}}", font_size=32, color=STEEL_DARK),
            MathTex(rf"T \approx {s.period:.2f}\ \text{{s}}", font_size=42, color=WARM),
        ).arrange(DOWN, buff=0.32).next_to(heading, DOWN, buff=0.45)
        note = Text(f"= a {s.equivalent_length * 100:.0f} cm simple pendulum",
                    font_size=24, color=COOL).next_to(lines, DOWN, buff=0.4)
        note2 = Text("far-out weights → big I → slow swing", font_size=22, color=STEEL_DARK
                     ).next_to(note, DOWN, buff=0.2)

        self.play(Write(heading))
        for ln in lines:
            self.play(Write(ln), run_time=0.9)
        self.play(FadeIn(note), FadeIn(note2))
        self.wait(2.2)
        self.play(FadeOut(VGroup(heading, lines, note, note2, self.osc_body, self.osc_com)))

    # ---------------------------------------------- 6. remove the weights
    def without_the_weights(self):
        bare = without_weights()
        heading = Text("4 · Now remove the weights", font_size=32, color=STEEL
                       ).to_edge(UP).shift(RIGHT * 2.6)
        theta = ValueTracker(0.0)

        body = always_redraw(lambda: sculpture_body(bare, with_weights=False).rotate(
            theta.get_value(), about_point=PIVOT))
        com = always_redraw(lambda: Dot(com_point(bare, theta.get_value()), radius=0.11,
                                        color=RED))
        self.play(Write(heading), FadeIn(body), FadeIn(com))

        lam = bare.growth_rate
        lines = VGroup(
            MathTex(r"y_{\text{cm}} = +8\ \text{cm} \;\Rightarrow\; d<0", font_size=34),
            MathTex(r"\theta(t) = \theta_0\cosh(\lambda t)", font_size=36),
            MathTex(rf"\lambda = \sqrt{{g/h}} \approx {lam:.1f}\ \text{{s}}^{{-1}}", font_size=32),
            MathTex(rf"1^\circ \to 30^\circ \text{{ in }} {topple_time(bare):.2f}\ \text{{s}}",
                    font_size=36, color=RED),
        ).arrange(DOWN, buff=0.35).next_to(heading, DOWN, buff=0.5)
        for ln in lines:
            self.play(Write(ln), run_time=0.9)

        # topple in (roughly) real time, slowed 4x so it is visible
        t_end = math.acosh(math.radians(80) / math.radians(1)) / lam
        self.play(UpdateFromAlphaFunc(
            theta, lambda m, a: m.set_value(math.radians(1) * math.cosh(lam * a * t_end))),
            run_time=4 * t_end, rate_func=linear)
        slow = Text("(shown 4× slower)", font_size=20, color=STEEL_DARK
                    ).next_to(PIVOT, DOWN, buff=2.8)
        self.play(FadeIn(slow))
        self.wait(1.4)
        self.play(FadeOut(VGroup(heading, lines, body, com, slow)))

    # ----------------------------------------------------------- 7. outro
    def outro(self, s: Sculpture):
        body = sculpture_body(s)
        com = Dot(com_point(s, 0), radius=0.13, color=WARM)
        self.play(FadeIn(body), FadeIn(com))
        summary = VGroup(
            Text("Centre of mass below the pivot", font_size=30, color=WARM),
            Text("→ upright is the energy minimum", font_size=28, color=STEEL),
            MathTex(r"U(\theta) = -Mgd\cos\theta", font_size=40),
            Text("Same trick as the balancing-bird toy", font_size=24, color=STEEL_DARK),
            Text("and a tightrope walker's pole.", font_size=24, color=STEEL_DARK),
        ).arrange(DOWN, buff=0.32).shift(RIGHT * 2.6)
        for item in summary:
            self.play(FadeIn(item, shift=UP * 0.15), run_time=0.7)
        rig = VGroup(body, com)
        self.play(Rotate(rig, angle=0.25, about_point=PIVOT), run_time=0.7)
        self.play(Rotate(rig, angle=-0.25, about_point=PIVOT), run_time=0.7)
        self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])

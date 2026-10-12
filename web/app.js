/* Balancing sculpture — live physical-pendulum simulation.
 *
 * Model: rigid body of point masses on a frictionless pivot at the origin.
 *   CoM in body frame (xc, yc). After rotating by θ (counter-clockwise),
 *   the CoM height is  y'(θ) = xc sinθ + yc cosθ
 *   U(θ)  = M g y'(θ)
 *   τ(θ)  = -dU/dθ = -M g (xc cosθ - yc sinθ)
 *   I θ'' = τ(θ) - c θ'
 * The sculpture can't rotate past ±LIMIT (the figure would hit the stand),
 * so passing it counts as toppling.
 */
(() => {
  "use strict";

  const G = 9.81;
  const LIMIT = 1.35;            // rad (~77°)
  const DT = 1 / 480;            // integrator step (s)
  const HISTORY_S = 10;

  const PRESETS = {
    sculpture: { mf: 160, ml: 240, xl: -12, yl: -28, mr: 200, xr: 14, yr: -16, damp: 0.004 },
    bare:      { mf: 160, ml: 0,   xl: -12, yl: -28, mr: 0,   xr: 14, yr: -16, damp: 0.004 },
    short:     { mf: 160, ml: 240, xl: -10, yl: -2,  mr: 200, xr: 11.6, yr: -1, damp: 0.004 },
    lopsided:  { mf: 160, ml: 300, xl: -12, yl: -28, mr: 200, xr: 14, yr: -16, damp: 0.004 },
  };
  const FIGURE_POS = { x: 0.005, y: 0.08 };   // m, figure's own centre of mass

  // ---------------------------------------------------------------- state
  const params = { ...PRESETS.sculpture };
  const state = { theta: 0, omega: 0, t: 0, toppled: false, dragging: false, running: true };
  let history = [];
  let model = null;

  const $ = (id) => document.getElementById(id);

  // ---------------------------------------------------------------- model
  function buildModel(p) {
    const parts = [
      { name: "figure", m: p.mf / 1000, x: FIGURE_POS.x, y: FIGURE_POS.y },
      { name: "left", m: p.ml / 1000, x: p.xl / 100, y: p.yl / 100 },
      { name: "right", m: p.mr / 1000, x: p.xr / 100, y: p.yr / 100 },
    ];
    const M = parts.reduce((s, q) => s + q.m, 0);
    const sumMx = parts.reduce((s, q) => s + q.m * q.x, 0);
    const sumMy = parts.reduce((s, q) => s + q.m * q.y, 0);
    const xc = sumMx / M, yc = sumMy / M;
    const I = parts.reduce((s, q) => s + q.m * (q.x * q.x + q.y * q.y), 0);
    const r = Math.hypot(xc, yc);

    // equilibrium with CoM straight below the pivot: φ + θ = -π/2
    const phi = Math.atan2(yc, xc);
    let thetaEq = -Math.PI / 2 - phi;
    thetaEq = Math.atan2(Math.sin(thetaEq), Math.cos(thetaEq));

    let kind;
    if (r < 1e-4) kind = "neutral";
    else if (Math.abs(thetaEq) < LIMIT * 0.95) kind = Math.abs(thetaEq) < 0.01 ? "stable" : "leans";
    else kind = "unstable";

    const k = M * G * r;                      // stiffness about the stable equilibrium
    const omega = Math.sqrt(k / I);
    return {
      parts, M, sumMx, xc, yc, I, r, d: -yc, thetaEq, kind,
      k, period: kind === "stable" || kind === "leans" ? (2 * Math.PI) / omega : NaN,
      Leq: I / (M * r),
      lambda: Math.sqrt(M * G * Math.max(yc, 0) / I),
    };
  }

  const torque = (m, th) => -m.M * G * (m.xc * Math.cos(th) - m.yc * Math.sin(th));
  const comHeight = (m, th) => m.xc * Math.sin(th) + m.yc * Math.cos(th);

  function accel(th, w) {
    return (torque(model, th) - params.damp * w) / model.I;
  }

  function step(dt) {
    // RK4
    const { theta: th, omega: w } = state;
    const k1t = w, k1w = accel(th, w);
    const k2t = w + 0.5 * dt * k1w, k2w = accel(th + 0.5 * dt * k1t, w + 0.5 * dt * k1w);
    const k3t = w + 0.5 * dt * k2w, k3w = accel(th + 0.5 * dt * k2t, w + 0.5 * dt * k2w);
    const k4t = w + dt * k3w, k4w = accel(th + dt * k3t, w + dt * k3w);
    state.theta += (dt / 6) * (k1t + 2 * k2t + 2 * k3t + k4t);
    state.omega += (dt / 6) * (k1w + 2 * k2w + 2 * k3w + k4w);
    state.t += dt;
    if (Math.abs(state.theta) >= LIMIT) {
      state.theta = Math.sign(state.theta) * LIMIT;
      state.omega = 0;
      state.toppled = true;
    }
  }

  // ---------------------------------------------------------------- canvas helpers
  function fitCanvas(c) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const r = c.getBoundingClientRect();
    const w = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    const ctx = c.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, W: r.width, H: r.height };
  }

  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const COL = {};
  function readColors() {
    for (const n of ["bg", "line", "line-2", "text", "muted", "faint", "steel", "warm", "cool", "red", "green"]) {
      COL[n] = css("--" + n);
    }
  }

  // ---------------------------------------------------------------- scene drawing
  const sim = $("sim");
  let view = { px: 0, py: 0, s: 1 };

  function toScreen(x, y, th) {
    const c = Math.cos(th), s = Math.sin(th);
    return [view.px + view.s * (x * c - y * s), view.py - view.s * (x * s + y * c)];
  }

  function drawScene() {
    const { ctx, W, H } = fitCanvas(sim);
    view.s = Math.min(H / 0.68, W / 0.72);
    view.px = W / 2;
    view.py = H * 0.25;
    const s = view.s, th = state.theta;

    ctx.clearRect(0, 0, W, H);

    // faint grid every 5 cm
    ctx.strokeStyle = COL.line; ctx.lineWidth = 1; ctx.globalAlpha = 0.45;
    for (let gx = -0.4; gx <= 0.4001; gx += 0.05) {
      const X = view.px + gx * s;
      ctx.beginPath(); ctx.moveTo(X, 0); ctx.lineTo(X, H); ctx.stroke();
    }
    for (let gy = -0.6; gy <= 0.3001; gy += 0.05) {
      const Y = view.py - gy * s;
      ctx.beginPath(); ctx.moveTo(0, Y); ctx.lineTo(W, Y); ctx.stroke();
    }
    ctx.globalAlpha = 1;

    // stand (fixed)
    ctx.fillStyle = "#4b5058";
    ctx.fillRect(view.px - 3, view.py + 4, 6, H - view.py);
    ctx.fillStyle = "#6b7078";
    ctx.fillRect(view.px - 0.045 * s, view.py, 0.09 * s, 5);

    // plumb line through the pivot
    ctx.setLineDash([5, 6]); ctx.strokeStyle = COL.cool; ctx.globalAlpha = 0.6;
    ctx.beginPath(); ctx.moveTo(view.px, view.py); ctx.lineTo(view.px, view.py + 0.42 * s); ctx.stroke();
    ctx.setLineDash([]); ctx.globalAlpha = 1;

    const P = (x, y) => toScreen(x, y, th);
    const line = (pts, width, color) => {
      ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineCap = "round"; ctx.lineJoin = "round";
      ctx.beginPath(); ctx.moveTo(...P(...pts[0]));
      for (const q of pts.slice(1)) ctx.lineTo(...P(...q));
      ctx.stroke();
    };

    // arms + weights
    const shoulder = [-0.006, 0.097];
    for (const side of ["left", "right"]) {
      const w = model.parts.find((q) => q.name === side);
      if (w.m <= 0) continue;
      const sign = Math.sign(w.x) || 1;
      const hgt = 0.02 + w.m * 0.12;
      const top = [w.x, w.y + hgt / 2];
      const c1 = [shoulder[0] + sign * 0.07, shoulder[1] + 0.015];
      const c2 = [w.x + sign * 0.015, Math.max(top[1], shoulder[1] - 0.02) + 0.04];
      ctx.strokeStyle = "#8a8f98"; ctx.lineWidth = Math.max(2, s * 0.004); ctx.lineCap = "round";
      ctx.beginPath(); ctx.moveTo(...P(...shoulder));
      ctx.bezierCurveTo(...P(...c1), ...P(...c2), ...P(...top));
      ctx.stroke();

      const hw = 0.012, hh = hgt / 2;
      const corners = [[w.x - hw, w.y - hh], [w.x + hw, w.y - hh], [w.x + hw, w.y + hh], [w.x - hw, w.y + hh]];
      ctx.beginPath(); ctx.moveTo(...P(...corners[0]));
      for (const q of corners.slice(1)) ctx.lineTo(...P(...q));
      ctx.closePath();
      ctx.fillStyle = "#3a3d44"; ctx.fill();
      ctx.strokeStyle = COL.steel; ctx.lineWidth = 1.5; ctx.stroke();
    }

    // figure
    const lw = Math.max(4, s * 0.012);
    line([[0, 0], [-0.02, 0.035], [0.012, 0.055]], lw, COL.steel);
    line([[0.012, 0.055], [-0.006, 0.105]], lw * 1.5, COL.steel);
    const [hx, hy] = P(-0.012, 0.125);
    ctx.fillStyle = COL.steel;
    ctx.beginPath(); ctx.arc(hx, hy, 0.016 * s, 0, Math.PI * 2); ctx.fill();

    // pivot
    ctx.fillStyle = COL.cool;
    ctx.beginPath(); ctx.arc(view.px, view.py, 5, 0, Math.PI * 2); ctx.fill();

    // centre of mass, lever arm, gravity
    const [cx, cy] = P(model.xc, model.yc);
    ctx.strokeStyle = COL.warm; ctx.lineWidth = 2; ctx.globalAlpha = 0.7;
    ctx.beginPath(); ctx.moveTo(view.px, view.py); ctx.lineTo(cx, cy); ctx.stroke();
    ctx.globalAlpha = 1;

    const arrowLen = 0.07 * s;
    ctx.strokeStyle = COL.red; ctx.fillStyle = COL.red; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx, cy + arrowLen - 8); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx, cy + arrowLen); ctx.lineTo(cx - 6, cy + arrowLen - 11); ctx.lineTo(cx + 6, cy + arrowLen - 11); ctx.closePath(); ctx.fill();

    ctx.fillStyle = COL.warm;
    ctx.beginPath(); ctx.arc(cx, cy, 7, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = COL.warm; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(cx, cy, 12, 0, Math.PI * 2); ctx.stroke();

    ctx.font = "500 12px " + css("--mono");
    ctx.fillStyle = COL.warm;
    ctx.fillText("CM", cx + 16, cy + 4);
    ctx.fillStyle = COL.red;
    ctx.fillText("Mg", cx + 10, cy + arrowLen - 4);

    // HUD
    ctx.fillStyle = COL.muted;
    ctx.font = "400 13px " + css("--mono");
    ctx.fillText(`θ = ${(state.theta * 180 / Math.PI).toFixed(1).padStart(6)}°`, 14, 24);
    ctx.fillText(`t = ${state.t.toFixed(1)} s`, 14, 44);
    if (state.toppled) {
      ctx.fillStyle = COL.red;
      ctx.font = "500 15px " + css("--mono");
      ctx.fillText("TOPPLED", 14, 70);
    }
    if (!state.running) {
      ctx.fillStyle = COL.faint;
      ctx.fillText("paused", W - 64, 24);
    }
  }

  // ---------------------------------------------------------------- plots
  function axesFrame(ctx, W, H, pad) {
    ctx.strokeStyle = COL.line; ctx.lineWidth = 1;
    ctx.strokeRect(pad.l, pad.t, W - pad.l - pad.r, H - pad.t - pad.b);
  }

  function drawThetaPlot() {
    const { ctx, W, H } = fitCanvas($("plot-theta"));
    ctx.clearRect(0, 0, W, H);
    const pad = { l: 40, r: 10, t: 10, b: 22 };
    axesFrame(ctx, W, H, pad);
    const maxAbs = Math.max(10, ...history.map((h) => Math.abs(h.th) * 180 / Math.PI));
    const yMax = Math.min(90, Math.ceil(maxAbs / 5) * 5);
    const t1 = Math.max(state.t, HISTORY_S), t0 = t1 - HISTORY_S;
    const X = (t) => pad.l + ((t - t0) / HISTORY_S) * (W - pad.l - pad.r);
    const Y = (deg) => pad.t + (1 - (deg + yMax) / (2 * yMax)) * (H - pad.t - pad.b);

    ctx.font = "400 11px " + css("--mono"); ctx.fillStyle = COL.faint;
    for (const v of [-yMax, 0, yMax]) {
      ctx.fillText(`${v}°`, 4, Y(v) + 4);
      ctx.strokeStyle = COL.line; ctx.beginPath(); ctx.moveTo(pad.l, Y(v)); ctx.lineTo(W - pad.r, Y(v)); ctx.stroke();
    }
    for (let t = Math.ceil(t0); t <= t1; t += 2) ctx.fillText(`${t}s`, X(t) - 8, H - 6);

    if (model.kind === "leans") {
      ctx.setLineDash([4, 5]); ctx.strokeStyle = COL.cool;
      const ye = Y(model.thetaEq * 180 / Math.PI);
      ctx.beginPath(); ctx.moveTo(pad.l, ye); ctx.lineTo(W - pad.r, ye); ctx.stroke(); ctx.setLineDash([]);
    }

    ctx.strokeStyle = COL.warm; ctx.lineWidth = 2;
    ctx.beginPath();
    history.forEach((h, i) => {
      const x = X(h.t), y = Y(h.th * 180 / Math.PI);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.stroke();
  }

  function drawEnergyPlot() {
    const { ctx, W, H } = fitCanvas($("plot-U"));
    ctx.clearRect(0, 0, W, H);
    const pad = { l: 40, r: 10, t: 10, b: 22 };
    axesFrame(ctx, W, H, pad);
    const N = 181, span = Math.PI / 2;
    const thetas = Array.from({ length: N }, (_, i) => -span + (2 * span * i) / (N - 1));
    const Us = thetas.map((t) => model.M * G * comHeight(model, t) * 1000);   // mJ
    let lo = Math.min(...Us), hi = Math.max(...Us);
    if (hi - lo < 1e-6) { lo -= 1; hi += 1; }
    const X = (t) => pad.l + ((t + span) / (2 * span)) * (W - pad.l - pad.r);
    const Y = (u) => pad.t + (1 - (u - lo) / (hi - lo)) * (H - pad.t - pad.b);

    // forbidden zones beyond the stand limit
    ctx.fillStyle = COL.red; ctx.globalAlpha = 0.08;
    ctx.fillRect(pad.l, pad.t, X(-LIMIT) - pad.l, H - pad.t - pad.b);
    ctx.fillRect(X(LIMIT), pad.t, W - pad.r - X(LIMIT), H - pad.t - pad.b);
    ctx.globalAlpha = 1;

    ctx.font = "400 11px " + css("--mono"); ctx.fillStyle = COL.faint;
    for (const d of [-90, -45, 0, 45, 90]) ctx.fillText(`${d}°`, X(d * Math.PI / 180) - 10, H - 6);
    ctx.fillText(`${(+hi.toFixed(0)) || 0}`, 4, Y(hi) + 4);
    ctx.fillText(`${(+lo.toFixed(0)) || 0}`, 4, Y(lo) + 4);
    ctx.fillText("mJ", 4, (pad.t + H - pad.b) / 2 + 4);

    ctx.strokeStyle = COL.cool; ctx.lineWidth = 2;
    ctx.beginPath();
    thetas.forEach((t, i) => (i ? ctx.lineTo(X(t), Y(Us[i])) : ctx.moveTo(X(t), Y(Us[i]))));
    ctx.stroke();

    const u = model.M * G * comHeight(model, state.theta) * 1000;
    ctx.fillStyle = COL.warm;
    ctx.beginPath(); ctx.arc(X(state.theta), Y(u) - 7, 7, 0, Math.PI * 2); ctx.fill();
  }

  // ---------------------------------------------------------------- UI
  const fmt = {
    g: (v) => `${v.toFixed(0)} g`,
    cm: (v) => `${v.toFixed(1)} cm`,
  };
  const UNITS = { mf: "g", ml: "g", mr: "g", xl: "cm", yl: "cm", xr: "cm", yr: "cm", damp: "c" };

  function syncInputs() {
    for (const key of Object.keys(UNITS)) {
      const el = $(key);
      el.value = params[key];
      updateOutput(key);
    }
  }
  function updateOutput(key) {
    const out = document.querySelector(`output[data-for="${key}"]`);
    const v = params[key];
    out.textContent = UNITS[key] === "g" ? fmt.g(v) : UNITS[key] === "cm" ? fmt.cm(v) : `${v.toFixed(3)} N·m·s`;
  }

  function updateReadouts() {
    const m = model;
    $("r-M").textContent = `${(m.M * 1000).toFixed(0)} g`;
    $("r-com").textContent = `(${(m.xc * 100).toFixed(1)}, ${(m.yc * 100).toFixed(1)}) cm`;
    const dEl = $("r-d");
    dEl.textContent = `${(m.d * 100).toFixed(1)} cm`;
    dEl.className = m.d > 0 ? "warm" : "bad";
    $("r-mx").textContent = `${(m.sumMx * 1e5).toFixed(0)} g·cm`;
    $("r-I").textContent = `${m.I.toFixed(4)} kg·m²`;
    $("r-k").textContent = m.d > 0 ? `${(m.M * G * m.d).toFixed(3)} N·m` : `${(m.M * G * m.d).toFixed(3)} N·m`;
    $("r-T").textContent = Number.isFinite(m.period) ? `${m.period.toFixed(2)} s` : "falls";
    $("r-L").textContent = Number.isFinite(m.period) ? `${(m.Leq * 100).toFixed(0)} cm` : "—";

    const badge = $("status");
    const label = {
      stable: ["Stable · CM below foot", "stable"],
      leans: [`Stable · leans ${(m.thetaEq * 180 / Math.PI).toFixed(0)}°`, "neutral"],
      unstable: [m.lambda > 0 ? `Unstable · λ ≈ ${m.lambda.toFixed(1)} s⁻¹` : "Unstable", "unstable"],
      neutral: ["Neutral · CM at the foot", "neutral"],
    }[m.kind];
    badge.textContent = label[0];
    badge.className = `badge ${label[1]}`;
  }

  function applyParams(resetMotion = false) {
    model = buildModel(params);
    updateReadouts();
    if (resetMotion) reset();
    else state.toppled = Math.abs(state.theta) >= LIMIT;
  }

  function reset(theta0 = 0) {
    state.theta = theta0; state.omega = 0; state.t = 0; state.toppled = false;
    history = [];
  }

  function kick(deg) {
    const base = model.kind === "leans" ? model.thetaEq : 0;
    reset(base + deg * Math.PI / 180);
    state.running = true;
    $("btn-play").textContent = "Pause";
  }

  for (const key of Object.keys(UNITS)) {
    $(key).addEventListener("input", (e) => {
      params[key] = parseFloat(e.target.value);
      updateOutput(key);
      document.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      applyParams(false);
    });
  }

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      Object.assign(params, PRESETS[chip.dataset.preset]);
      syncInputs();
      applyParams(true);
      kick(chip.dataset.preset === "bare" || chip.dataset.preset === "short" ? 1 : 15);
    });
  });

  $("btn-play").addEventListener("click", (e) => {
    state.running = !state.running;
    e.target.textContent = state.running ? "Pause" : "Play";
  });
  $("btn-kick").addEventListener("click", () => kick(15));
  $("btn-reset").addEventListener("click", () => {
    Object.assign(params, PRESETS.sculpture);
    document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c.dataset.preset === "sculpture"));
    syncInputs();
    applyParams(true);
    kick(15);
  });

  // drag to tilt
  let drag = null;
  const pointerAngle = (e) => {
    const r = sim.getBoundingClientRect();
    return Math.atan2(-(e.clientY - r.top - view.py), e.clientX - r.left - view.px);
  };
  sim.addEventListener("pointerdown", (e) => {
    sim.setPointerCapture(e.pointerId);
    drag = { a0: pointerAngle(e), th0: state.theta };
    state.dragging = true; state.toppled = false;
  });
  sim.addEventListener("pointermove", (e) => {
    if (!drag) return;
    let da = pointerAngle(e) - drag.a0;
    da = Math.atan2(Math.sin(da), Math.cos(da));
    state.theta = Math.max(-LIMIT * 0.98, Math.min(LIMIT * 0.98, drag.th0 + da));
    state.omega = 0;
  });
  const endDrag = () => {
    if (!drag) return;
    drag = null; state.dragging = false; history = []; state.t = 0;
    state.running = true; $("btn-play").textContent = "Pause";
  };
  sim.addEventListener("pointerup", endDrag);
  sim.addEventListener("pointercancel", endDrag);

  // period → depth calculator
  function calc() {
    const T = parseFloat($("calc-T").value), M = parseFloat($("calc-M").value) / 1000, I = parseFloat($("calc-I").value);
    const out = $("calc-d");
    if (!(T > 0 && M > 0 && I > 0)) { out.textContent = "—"; return; }
    const d = (4 * Math.PI * Math.PI * I) / (M * G * T * T);
    out.textContent = `${(d * 100).toFixed(1)} cm below the foot`;
  }
  ["calc-T", "calc-M", "calc-I"].forEach((id) => $(id).addEventListener("input", calc));

  // parts table from the Python export (with a built-in fallback)
  function fillPartsTable(parts) {
    $("parts-body").innerHTML = parts.map((p) =>
      `<tr><td>${p.name}</td><td>${(p.m * 1000).toFixed(0)} g</td><td>${(p.x * 100).toFixed(1)} cm</td><td>${(p.y * 100).toFixed(1)} cm</td></tr>`
    ).join("");
  }

  // ---------------------------------------------------------------- loop
  let last = performance.now();
  function frame(now) {
    const elapsed = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (state.running && !state.dragging && !state.toppled) {
      for (let t = 0; t < elapsed; t += DT) step(DT);
    }
    if (state.running && !state.dragging) {
      history.push({ t: state.t, th: state.theta });
      while (history.length && history[0].t < state.t - HISTORY_S) history.shift();
    }
    drawScene();
    drawThetaPlot();
    drawEnergyPlot();
    requestAnimationFrame(frame);
  }

  // ---------------------------------------------------------------- boot
  function init() {
    readColors();
    syncInputs();
    applyParams(true);
    kick(15);
    calc();
    fillPartsTable(model.parts.map((p, i) => ({ ...p, name: ["Figure", "Left weight", "Right weight"][i] })));
    fetch("assets/data.json").then((r) => r.ok ? r.json() : null).then((data) => {
      if (data) fillPartsTable(data.sculpture.parts.map((p) => ({ ...p, name: p.name[0].toUpperCase() + p.name.slice(1) })));
    }).catch(() => {});

    const renderMath = () => window.renderMathInElement && renderMathInElement(document.body, {
      delimiters: [{ left: "$$", right: "$$", display: true }, { left: "\\(", right: "\\)", display: false }],
      throwOnError: false,
    });
    if (window.renderMathInElement) renderMath(); else window.addEventListener("load", renderMath);

    requestAnimationFrame((t) => { last = t; frame(t); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

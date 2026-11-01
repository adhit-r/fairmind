// The release lock: a sectioned pin-tumbler cylinder. Each pin chamber is one release check.
// A check backed by measured evidence lifts its key pin exactly to the shear line; an attested
// check does too, in a paler material; an open check leaves its driver pin across the shear line,
// so the plug cannot turn. Writes lock.svg (the figure) and lock.json (pin anchors for the page).
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const KIT = "/Users/adhi/.claude/skills/anatomy/kit";
const k = await import(`${KIT}/iso-kit.mjs`);
const G = await import(`${KIT}/lathe.mjs`);
const HERE = dirname(fileURLToPath(import.meta.url));

const WIDTH = 760;
const HEIGHT = 330;

// Model: one entry per chamber, left to right, in the order the decision table lists them.
const CHECKS = [
  { id: "di-age", state: "measured" },
  { id: "di-gender", state: "measured" },
  { id: "eo-gender", state: "measured" },
  { id: "eo-age", state: "open", pin: 1 },
  { id: "calibration", state: "attested" },
  { id: "reason-codes", state: "attested" },
  { id: "oversight", state: "open", pin: 2 },
  { id: "consent", state: "measured" },
  { id: "energy", state: "measured" },
];

const PLATE = { x: -196, y: -54, w: 392, d: 108, r: 8 };
const PLATE_H = 10;
const FOOT_H = 5;
const X0 = -124; // housing length along x
const X1 = 124;
const BACK = -28; // housing runs from y = BACK to the cut plane y = 0
const Z0 = 16; // housing underside
const ZTOP = 100;
const PLUG = { lo: 20, hi: 56 }; // plug band in the section; hi is the shear line
const SHEAR = PLUG.hi;
const CHAMBER_TOP = 92;
const PIN_R = 3.1;
const BORE_R = 6;
const STEP = 24;
const CX = CHECKS.map((_, i) => -96 + STEP * i);
const KEY_BOTTOM = 25;
// Key bitting: depth of each cut. Set pins: key pin + cut reaches the shear line exactly.
const CUT = [9, 5, 12, 7, 4, 11, 6, 13, 5];
const KEY_PIN = CHECKS.map((c, i) => SHEAR - (KEY_BOTTOM + CUT[i]) - (c.state === "open" ? 8 : 0));
const DRIVER = 15;

const P = k.fitProjection(
  [...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [X0, BACK, ZTOP], [X1, 0, ZTOP], [X1 + 14, 0, 70], [-200, 0, 54]],
  WIDTH,
  HEIGHT,
  { pad: 10, azimuth: 58 },
);

const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (points, style) => k.dotsSvg(points, style);
const face = (pts) => k.pathOf(pts.map(([x, z]) => at([x, 0, z])), true); // a polygon on the cut plane
const seg = (a, b) => k.pathOf([at(a), at(b)]);
const byDepth = (points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const ALONG_X = (o) => G.frameOf(o, [1, 0, 0], [0, 1, 0], [0, 0, 1]);
const ALONG_Y = (o) => G.frameOf(o, [0, 1, 0], [1, 0, 0], [0, 0, 1]);
const V = G.viewOf(P);

function base() {
  const out = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  for (const [x, y] of byDepth(k.corners(PLATE, 22))) {
    out.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  out.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "faint" }));
  const screws = k.corners(PLATE, 10);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  // Chamber scale along the front edge: a tick every 4, a major tick under each chamber.
  const strip = { x: X0, y: PLATE.y + PLATE.d - 17, w: X1 - X0, d: 9, r: 1 };
  out.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const ticks = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 4, 6, strip.y + 0.8, 0.6, [2.2, 4.2], P);
  out.push(L(ticks.minor, { tone: "lo" }), L(ticks.major, { tone: "mid" }));
  CX.forEach((x, i) => out.push(k.faceTextSvg(k.topMatrix([x, strip.y + 7.6], 0.6, P, "x"), String(i + 1), { size: 2.6, tone: "mid", anchor: "middle" })));
  out.push(D([at([strip.x + 2, strip.y + 4.5, 0.6]), at([strip.x + strip.w - 2, strip.y + 4.5, 0.6])], { size: 0.45 }));
  // Label plate, front right: three rule lines and two screws.
  const label = { x: X1 + 22, y: PLATE.y + PLATE.d - 30, w: 44, d: 22, r: 1.5 };
  out.push(S(k.slabOf(label, 0, 0.8, P, 3, 0.3), { tone: "lo", crease: "none" }));
  out.push(k.faceTextSvg(k.topMatrix([label.x + 4, label.y + 7], 0.8, P, "x"), "RELEASE LOCK", { size: 2.4, tone: "mid" }));
  [12, 16].forEach((dy) => out.push(L(k.lineOnTop([label.x + 4, label.y + dy], [label.x + label.w - 10, label.y + dy], 0.8, P), { tone: "faint", free: "both" })));
  out.push(D([at([label.x + label.w - 4, label.y + 4, 0.8]), at([label.x + label.w - 4, label.y + label.d - 4, 0.8])], { size: 0.42 }));
  return out.join("");
}

function saddles() {
  const out = [];
  for (const x of [-92, 52]) {
    const plan = { x, y: BACK - 4, w: 40, d: -BACK + 8, r: 2 };
    out.push(`<path class="iso-halo" d="${k.haloOf(plan, 0, Z0, P)}" style="filter:blur(5px)"/>`);
    out.push(S(k.slabOf(plan, 0, Z0, P, 4, 0.6), { tone: "mid" }));
    out.push(L(k.planOutline(k.insetPlan(plan, 3), Z0, P, 3), { tone: "faint" }));
    out.push(D([[x + 6, 2], [x + 34, 2]].map(([px, py]) => at([px, py, Z0])), { size: 0.45 }));
  }
  return out.join("");
}

function housing() {
  const out = [];
  const profile = [[0, Z0], [BACK + 4, Z0], [BACK, Z0 + 4], [BACK, ZTOP - 4], [BACK + 4, ZTOP], [0, ZTOP]];
  out.push(S(G.prismOf(ALONG_X([X0, 0, 0]), profile, 0, X1 - X0, P), { tone: "hi", crease: "faint" }));
  // Top face: chamber caps (plugged bores) and the two fixing screws.
  CX.forEach((x) => {
    out.push(L(k.ring(x, -12, BORE_R + 1, ZTOP, P, 20), { tone: "lo" }));
    out.push(D([at([x, -12, ZTOP])], { size: 0.35, tone: "lo" }));
  });
  out.push(L(k.lineOnTop([X0, -24], [X1, -24], ZTOP, P), { tone: "faint" }));
  // Right end face: the plug's turning quadrant, LOCKED at 0, OPEN at 90 degrees.
  const END = ALONG_X([X1, 0, 0]);
  const centre = [0, -14, 38];
  const quadrant = [];
  for (let i = 0; i <= 18; i++) {
    const a = (Math.PI / 2) * (i / 18);
    const r0 = i % 9 === 0 ? 10.5 : 11.8;
    const p = (r) => at([X1, centre[1] - Math.sin(a) * r, centre[2] + Math.cos(a) * r]);
    quadrant.push(k.pathOf([p(r0), p(13.2)]));
  }
  out.push(L(quadrant.join(""), { tone: "mid" }));
  return { body: out.join(""), END };
}

// Section: what the cut plane at y = 0 shows. Housing and plug are hatched in opposite directions.
function section() {
  const out = [];
  const defs = [];
  const hatch = (id, region, dir, step) => {
    defs.push(`<clipPath id="${id}"><path d="${region}"/></clipPath>`);
    const lines = [];
    for (let t = -260; t <= 260; t += step) {
      const a = [t - 140 * dir, 0, Z0 - 20];
      const b = [t + 140 * dir, 0, ZTOP + 120];
      lines.push(seg(a, b));
    }
    return `<g clip-path="url(#${id})">${L(lines.join(""), { tone: "faint" })}</g>`;
  };
  const housingFace = face([[X0, Z0], [X1, Z0], [X1, ZTOP], [X0, ZTOP]]) + face([[X0 - 8, 8], [X0, 8], [X0, 68], [X0 - 8, 68]]);
  out.push(`<path class="fm-cut" d="${housingFace}"/>`);
  out.push(hatch("fm-h-housing", housingFace, 1, 5));
  const plugFace = face([[X0 - 6, PLUG.lo], [X1 - 2, PLUG.lo], [X1 - 2, PLUG.hi], [X0 - 6, PLUG.hi]]);
  out.push(`<path class="fm-cut fm-cut-plug" d="${plugFace}"/>`);
  out.push(hatch("fm-h-plug", plugFace, -1, 4));
  out.push(L(plugFace, { tone: "mid" }));
  // Pin chambers: bores through the housing and the plug down to the key, back wall in shade.
  const anchors = [];
  CX.forEach((x, i) => {
    const bottom = KEY_BOTTOM + CUT[i];
    const bore = face([[x - BORE_R, bottom], [x + BORE_R, bottom], [x + BORE_R, CHAMBER_TOP], [x - BORE_R, CHAMBER_TOP]]);
    out.push(`<path class="fm-bore" d="${bore}"/>`);
    out.push(`<path class="fm-bore-shade" d="${face([[x - BORE_R, bottom], [x - BORE_R + 2.2, bottom], [x - BORE_R + 2.2, CHAMBER_TOP], [x - BORE_R, CHAMBER_TOP]])}"/>`);
    out.push(L(bore, { tone: "lo" }));
  });
  // The key, sectioned: blade along the keyway with its bitting cut to each chamber.
  const blade = [[X0 - 30, KEY_BOTTOM], [X1 - 22, KEY_BOTTOM], [X1 - 14, KEY_BOTTOM + 8]];
  for (let i = CX.length - 1; i >= 0; i--) {
    const x = CX[i];
    const top = KEY_BOTTOM + CUT[i];
    blade.push([x + 7, top + 4], [x + 2.6, top], [x - 2.6, top], [x - 7, top + 4]);
  }
  blade.push([X0 - 30, KEY_BOTTOM + 14]);
  out.push(`<path class="fm-key" d="${face(blade)}"/>`);
  out.push(L(face(blade), { tone: "hi" }));
  out.push(L(seg([X0 - 26, 0, KEY_BOTTOM + 6], [X1 - 30, 0, KEY_BOTTOM + 6]), { tone: "faint" }));
  // Shear line: where plug meets housing. A driver pin across it stops the plug turning.
  out.push(`<path class="fm-shear" d="${seg([X0, 0, SHEAR], [X1, 0, SHEAR])}"/>`);
  out.push(L(face([[X0, Z0], [X1, Z0], [X1, ZTOP], [X0, ZTOP]]) + face([[X0 - 8, 8], [X0, 8], [X0, 68], [X0 - 8, 68]]), { tone: "hi" }));
  return { body: out.join(""), defs: defs.join(""), anchors };
}

function vcoil(cx, cy, z0, z1, r, turns) {
  const count = Math.round(turns * 24);
  const back = [];
  const front = [];
  let run = [];
  let near = null;
  for (let i = 0; i <= count; i++) {
    const share = i / count;
    const angle = share * turns * Math.PI * 2;
    const point = at([cx + r * Math.cos(angle), cy + r * Math.sin(angle), z0 + (z1 - z0) * share]);
    const facing = Math.cos(angle) * V[0] + Math.sin(angle) * V[1] > 0;
    if (near === null) near = facing;
    if (facing !== near) {
      run.push(point);
      (near ? front : back).push(k.pathOf(run));
      run = [point];
      near = facing;
      continue;
    }
    run.push(point);
  }
  if (run.length > 1) (near ? front : back).push(k.pathOf(run));
  return { back: back.join(""), front: front.join("") };
}

function pins() {
  const out = [];
  const anchors = [];
  CX.forEach((x, i) => {
    const c = CHECKS[i];
    const bottom = KEY_BOTTOM + CUT[i];
    const keyTop = bottom + KEY_PIN[i];
    const driverTop = keyTop + DRIVER;
    const accent = c.state === "open";
    const keyTone = c.state === "attested" ? "mid" : "hi";
    const wrap = (svg, part) => (accent && part === "driver" ? `<g class="fm-accent">${svg}</g>` : part === "key" && c.state === "attested" ? `<g class="fm-attested">${svg}</g>` : svg);
    const spring = vcoil(x, 0, driverTop + 0.6, CHAMBER_TOP - 0.6, 2.6, 5);
    out.push(L(spring.back, { tone: "lo" }));
    out.push(wrap(S(k.cylinder(x, 0, PIN_R, bottom + 0.4, KEY_PIN[i] - 0.8, P, 24, 0.7), { tone: keyTone, crease: "faint" }), "key"));
    out.push(wrap(S(k.cylinder(x, 0, PIN_R, keyTop + 0.4, DRIVER - 0.8, P, 24, 0.5), { tone: accent ? "hi" : "mid", crease: "faint" }), "driver"));
    out.push(L(spring.front, { tone: "mid" }));
    if (c.state === "attested") out.push(L(k.sideArc(x, 0, PIN_R, bottom + KEY_PIN[i] * 0.5, P, 16), { tone: "lo" }));
    anchors.push({ id: c.id, state: c.state, pin: c.pin ?? null, chamber: i + 1, at: at([x, PIN_R, driverTop + 2]), top: at([x, -12, ZTOP]) });
  });
  return { body: out.join(""), anchors };
}

function keyBow() {
  const out = [];
  // Shank from the bow to the lock face, then the bow: a flat plate on the cut plane.
  out.push(S(G.prismOf(ALONG_Y([0, -1.6, 0]), [[X0 - 30, KEY_BOTTOM], [X0 - 4, KEY_BOTTOM], [X0 - 4, KEY_BOTTOM + 14], [X0 - 30, KEY_BOTTOM + 14]], 0, 3.2, P), { tone: "hi" }));
  const bow = [[-206, 22], [-196, 10], [-164, 10], [-152, 22], [-152, 52], [-164, 64], [-196, 64], [-206, 52]];
  out.push(S(G.prismOf(ALONG_Y([0, -1.6, 0]), bow, 0, 3.2, P), { tone: "hi" }));
  const ring = [];
  for (let i = 0; i <= 32; i++) {
    const a = (i / 32) * Math.PI * 2;
    ring.push(at([-188 + Math.cos(a) * 6, 1.6, 37 + Math.sin(a) * 6]));
  }
  out.push(L(k.pathOf(ring, true), { tone: "mid" }));
  out.push(k.faceTextSvg(k.sideMatrix([-174, 1.6], 48, P, "y"), "R-0412", { size: 2.6, tone: "mid", anchor: "middle" }));
  return out.join("");
}

function face_plate() {
  // The lock face at the left end: a turned bezel around the plug.
  // Sectioned like the housing: only the half behind the cut plane remains.
  const F = ALONG_X([X0 - 8, 0, 38]);
  const half = [];
  for (let i = 0; i <= 16; i++) {
    const a = (i / 16) * Math.PI;
    half.push([-Math.sin(a) * 30, Math.cos(a) * 30]);
  }
  return S(G.prismOf(F, half, 0, 8, P), { tone: "hi", crease: "faint" });
}

function tail(END) {
  const out = [];
  const F = ALONG_X([X1, -14, 38]);
  out.push(S(G.disc(0, 4, 8.6, F, P), { tone: "mid" }));
  out.push(D(G.dotsOf(F, 4, 6.4, 6, P, { all: true }), { size: 0.38 }));
  // Tailpiece cam, pointing at LOCKED.
  out.push(S(G.prismOf(F, [[-1.8, 0], [1.8, 0], [1.8, 9.6], [-1.8, 9.6]], 4, 7, P), { tone: "hi", lit: true }));
  return out.join("");
}

const H = housing();
const SEC = section();
const PINS = pins();
const svg = k.figureSvg({
  width: WIDTH,
  height: HEIGHT,
  label:
    "A sectioned pin-tumbler release lock on a base plate. Nine pin chambers stand for nine release checks. Seven key pins reach the shear line; two driver pins, chambers 4 and 7, cross it, so the plug stays locked.",
  body: [
    `<defs>${SEC.defs}</defs>`,
    base(),
    saddles(),
    face_plate(),
    H.body,
    SEC.body,
    PINS.body,
    tail(H.END),
    keyBow(),
  ],
});

writeFileSync(join(HERE, "lock.svg"), svg);
writeFileSync(join(HERE, "lock.json"), JSON.stringify({ width: WIDTH, height: HEIGHT, anchors: PINS.anchors }, null, 2));
const page = k.pageHtml({
  title: "Release lock",
  theme: "light",
  body: k.plateHtml({ fig: "Fig. 1", title: "Release lock, Loan scoring v4", hint: "Each chamber is one check", readout: "Plug locked · 2 pins across the shear line", fig: "Fig. 1", body: svg }),
  width: 820,
});
writeFileSync(join(HERE, "lock.html"), page.replace("</head>", `<link rel="stylesheet" href="lock.css"></head>`));
console.log("wrote lock.svg, lock.json, lock.html", PINS.anchors.length, "anchors");

// Generate HyperFrames compositions for the FairMind short videos from specs.mjs.
// node build.mjs            -> cuts missing clips, composes missing music, writes out/<video>-<format>/index.html
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { VIDEOS, REC } from "./specs.mjs";

const AR = 1.29; // card aspect in every format
const LAYOUTS = {
  "16x9": { W: 1920, H: 1080, card: [700, 96, 1124], copy: "left:112px;width:520px;top:300px;", head: 58, big: 104, foot: "left:112px;width:520px;bottom:104px;flex-direction:column;align-items:flex-start;gap:10px;" },
  "4x5": { W: 1080, H: 1350, card: [48, 452, 984], copy: "left:72px;right:72px;top:64px;height:352px;justify-content:flex-end;", head: 60, big: 92, foot: "left:72px;right:72px;bottom:56px;" },
  "1x1": { W: 1080, H: 1080, card: [150, 336, 780], copy: "left:72px;right:72px;top:40px;height:270px;justify-content:flex-end;", head: 50, big: 80, foot: "left:72px;right:72px;bottom:36px;" },
  "9x16": { W: 1080, H: 1920, card: [130, 780, 820], copy: "left:130px;right:260px;top:360px;height:400px;justify-content:flex-end;", head: 58, big: 80, pad: "0 300px 0 130px", foot: "left:130px;right:260px;top:290px;" },
};

const sh = (cmd, args) => execFileSync(cmd, args, { stdio: ["ignore", "inherit", "inherit"] });
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

function cutClip(name, rec, from, speed, len) {
  const out = `assets/clips/${name}.mp4`;
  if (fs.existsSync(out)) return;
  const to = from + len * speed;
  sh("ffmpeg", ["-y", "-v", "error", "-ss", String(from), "-to", String(to.toFixed(3)), "-i", `${REC}/${rec}/video.mp4`, "-an",
    "-vf", `setpts=(PTS-STARTPTS)/${speed},fps=30,format=yuv420p,tpad=stop_mode=clone:stop_duration=2`, "-t", String(len),
    "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-movflags", "+faststart", out]);
}

function music(name, T, anchor, resolve) {
  const mp3 = `assets/music/${name}.mp3`;
  if (fs.existsSync(mp3)) return;
  const wav = `assets/music/${name}.wav`;
  sh("uv", ["run", "-q", "--with", "numpy", "--with", "scipy", "python", "compose.py", "--duration", String(T), "--anchor", String(anchor), "--resolve", String(resolve), "--out", wav]);
  sh("ffmpeg", ["-y", "-v", "error", "-i", wav, "-af", "loudnorm=I=-18:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "256k", mp3]);
  fs.rmSync(wav);
}

function build(v, fmt) {
  const L = LAYOUTS[fmt];
  let t = 0;
  const scenes = v.scenes.map((s, i) => { const o = { ...s, i, start: +t.toFixed(3) }; t += s.dur; o.end = +t.toFixed(3); return o; });
  const T = +t.toFixed(3);
  const firstProduct = scenes.find((s) => s.type === "product");
  const outro = scenes[scenes.length - 1];
  music(v.name, T, firstProduct.start, outro.start);

  // runs of consecutive product scenes share the card
  const runs = [];
  scenes.forEach((s) => {
    if (s.type !== "product") return;
    const last = runs[runs.length - 1];
    if (last && last.end === s.start) last.end = s.end; else runs.push({ start: s.start, end: s.end });
  });

  let html = "", js = "";
  const products = scenes.filter((s) => s.type === "product");
  products.forEach((s) => {
    const name = `${v.name}-${s.i}`;
    const vs = Math.max(0, s.start - 0.3), vd = s.end + 0.3 - vs;
    cutClip(name, s.rec, s.from, s.speed || 1, +(vd + 0.2).toFixed(2));
    s.v = { name, vs: +vs.toFixed(3), vd: +vd.toFixed(3) };
  });
  const cardHtml = products.map((s, k) => `<div class="vwrap" data-layout-ignore id="w${s.i}"><video id="v${s.i}" src="assets/clips/${s.v.name}.mp4" muted playsinline data-start="${s.v.vs}" data-duration="${s.v.vd}" data-track-index="${2 + (k % 2)}"></video></div>`).join("\n");

  scenes.forEach((s) => {
    const isLast = s === outro;
    if (s.type === "statement") {
      const inner = [
        s.mark !== undefined ? `<img class="mark-lg" data-t="${s.mark}" src="assets/logo-mark.svg" alt="FairMind" />` : "",
        s.word !== undefined ? `<p class="wordmark" data-t="${s.word}">FairMind</p>` : "",
        ...(s.lines || []).map((l) => `<h1 class="big ${l.tone || ""}" data-t="${l.t}">${esc(l.text)}</h1>`),
        s.lede ? `<p class="lede" data-t="${s.lede.t}">${s.lede.text}</p>` : "",
        s.cta ? `<div class="cta" data-t="${s.cta}"><span class="pill">Try the live demo: app.fairmind.xyz</span><span class="fine">Open source, AGPL-3.0</span><span class="fine">github.com/adhit-r/fairmind</span></div>` : "",
      ].join("");
      html += `<section id="s${s.i}" class="clip statement" data-start="${s.start}" data-duration="${s.dur}" data-track-index="1">${inner}</section>\n`;
      js += `enter("#s${s.i}", ${s.start}); ${isLast ? "" : `tl.to("#s${s.i} > *", { opacity: 0, duration: 0.4, ease: "power2.in" }, ${(s.end - 0.45).toFixed(3)});`}\n`;
      if (s.start === 0) js += `tl.fromTo("#s${s.i}", { scale: 1 }, { scale: 1.035, duration: ${s.dur}, ease: "none" }, 0);\n`;
    } else {
      html += `<section id="s${s.i}" class="clip copy" data-start="${s.start}" data-duration="${s.dur}" data-track-index="4"><div class="label"><i></i>${esc(s.label)}</div><h2 class="head">${esc(s.head)}</h2><p class="sub">${esc(s.sub)}</p></section>\n`;
      js += `copy("#s${s.i}", ${s.start}, ${s.end});\nshot("#w${s.i}", ${s.v.vs}, ${JSON.stringify(s.keys)}, ${s === products[0] || runs.some((r) => r.start === s.start) ? "true" : "false"});\n`;
    }
  });
  runs.forEach((r) => {
    js += `tl.fromTo("#card", { opacity: 0, y: 30, scale: 0.98 }, { opacity: 1, y: 0, scale: 1, duration: 0.7, ease: "power3.out" }, ${(r.start - 0.2).toFixed(3)});\n`;
    js += `tl.to("#card", { opacity: 0, y: 16, duration: 0.45, ease: "power2.in" }, ${(r.end - 0.45).toFixed(3)});\n`;
    js += `tl.fromTo("#footer", { opacity: 0 }, { opacity: 1, duration: 0.5 }, ${(r.start + 0.1).toFixed(3)}); tl.to("#footer", { opacity: 0, duration: 0.4 }, ${(r.end - 0.45).toFixed(3)});\n`;
  });

  const [cx, cy, cw] = L.card;
  const doc = `<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=${L.W}, height=${L.H}" />
<title>FairMind ${esc(v.title)}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face { font-family: "Figtree"; src: url("assets/figtree.woff2") format("woff2"); font-weight: 300 900; }
:root { --bg:#f4f4f2; --ink:#15171a; --ink2:#5a5f68; --ink3:#666c76; --line:rgba(21,23,26,.08); --brand:#ff6b35; }
body { margin:0; background:var(--bg); color:var(--ink); font-family:"Figtree",system-ui,sans-serif; -webkit-font-smoothing:antialiased; }
#root { position:relative; width:100%; height:100%; overflow:hidden; background:var(--bg); }
.statement { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:${L.pad || "0 " + Math.round(L.W * 0.08) + "px"}; }
.big { margin:0; font-size:${L.big}px; line-height:1.04; font-weight:600; letter-spacing:-0.035em; display:block; }
.big.soft { color:var(--ink2); margin-top:${Math.round(L.big * 0.3)}px; }
.mark-lg { width:${Math.round(L.big * 1.4)}px; height:${Math.round(L.big * 1.4)}px; display:block; }
.wordmark { margin:${Math.round(L.big * 0.3)}px 0 0; font-size:${Math.round(L.big * 0.7)}px; font-weight:600; letter-spacing:-0.03em; }
.lede { margin:${Math.round(L.big * 0.36)}px 0 0; font-size:${Math.round(L.big * 0.44)}px; line-height:1.25; font-weight:500; letter-spacing:-0.015em; color:var(--ink2); max-width:${Math.round(L.W * 0.78)}px; }
.lede strong { color:var(--ink); font-weight:600; }
.cta { margin-top:${Math.round(L.big * 0.6)}px; display:flex; flex-direction:column; align-items:center; gap:10px; }
.pill { display:block; background:var(--ink); color:#fff; font-size:34px; font-weight:600; padding:20px 40px; border-radius:999px; }
.fine { display:block; white-space:nowrap; font-size:28px; color:var(--ink3); font-weight:500; }
.copy { position:absolute; display:flex; flex-direction:column; ${L.copy} }
.label { display:flex; align-items:center; gap:14px; font-size:28px; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:var(--ink3); }
.label i { display:block; width:10px; height:10px; border-radius:50%; background:var(--brand); }
.head { margin:22px 0 0; font-size:${L.head}px; line-height:1.07; font-weight:600; letter-spacing:-0.03em; }
.sub { margin:18px 0 0; font-size:30px; line-height:1.3; font-weight:500; color:var(--ink2); }
#card { position:absolute; left:${cx}px; top:${cy}px; width:${cw}px; height:${Math.round(cw / AR)}px; border-radius:22px; overflow:hidden; background:#fff; box-shadow:0 1px 2px rgba(21,23,26,.06),0 12px 40px rgba(21,23,26,.1); outline:1px solid var(--line); opacity:0; }
.vwrap { position:absolute; left:0; top:0; width:1440px; height:900px; transform-origin:0 0; }
.vwrap video { position:absolute; left:0; top:0; width:1440px; height:900px; display:block; }
#footer { position:absolute; display:flex; align-items:center; justify-content:space-between; opacity:0; ${L.foot} }
.brand { display:flex; align-items:center; gap:14px; font-size:28px; font-weight:600; letter-spacing:-0.02em; }
.brand img { width:44px; height:44px; display:block; }
.url { font-size:28px; font-weight:500; color:var(--ink3); }
</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="${L.W}" data-height="${L.H}" data-duration="${T}">
${html}<div id="card">
${cardHtml}
</div>
<div id="footer"><div class="brand"><img src="assets/logo-mark.svg" alt="" />FairMind</div><div class="url">app.fairmind.xyz</div></div>
<audio id="music" src="assets/music/${v.name}.mp3" data-start="0" data-duration="${T}" data-track-index="6" data-volume="1" data-automation='{"version":1,"lanes":[{"target":"volume","points":[{"t":0,"v":0},{"t":0.4,"v":1},{"t":${(T - 2.5).toFixed(2)},"v":1},{"t":${T},"v":0}]}]}'></audio>
</div>
<script>
const CARD_W = ${cw}, AR = ${AR};
const tl = gsap.timeline({ paused: true });
function cam(x, y, w) { const h = w / AR; x = Math.max(0, Math.min(x, 1440 - w)); y = Math.max(0, Math.min(y, 900 - h)); const s = CARD_W / w; return { x: -x * s, y: -y * s, scale: s }; }
function enter(sel, st) {
  document.querySelectorAll(sel + " [data-t]").forEach((el) => {
    const at = st + parseFloat(el.dataset.t);
    if (at === 0) tl.set(el, { opacity: 1 }, 0); // on screen at frame 0 (thumbnail)
    else tl.fromTo(el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }, at);
  });
}
function copy(sel, st, en) {
  tl.fromTo(sel + " .label", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, st + 0.15);
  tl.fromTo(sel + " .head", { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }, st + 0.25);
  tl.fromTo(sel + " .sub", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, st + 0.75);
  tl.to(sel + " > *", { opacity: 0, duration: 0.35, ease: "power2.in" }, en - 0.4);
}
function shot(w, vs, keys, first) {
  const k0 = keys[0];
  tl.set(w, { opacity: first ? 1 : 0, ...cam(k0[1], k0[2], k0[3]) }, 0);
  if (!first) tl.to(w, { opacity: 1, duration: 0.6, ease: "none" }, vs);
  for (let j = 1; j < keys.length; j++) { const a = keys[j - 1], b = keys[j]; tl.to(w, { ...cam(b[1], b[2], b[3]), duration: b[0] - a[0], ease: "power1.inOut" }, vs + a[0]); }
}
${js}
window.__timelines["main"] = tl;
</script>
</body></html>
`;
  const dir = `out/${v.name}-${fmt}`;
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(`${dir}/index.html`, doc);
  const link = `${dir}/assets`;
  if (!fs.existsSync(link)) fs.symlinkSync(path.relative(dir, "assets"), link);
  console.log(`${dir}  ${T}s`);
}

const only = process.argv[2];
for (const v of VIDEOS) if (!only || only === v.name) for (const f of v.formats) build(v, f);

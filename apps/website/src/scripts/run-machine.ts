import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';

// The release gate, taken apart: a white maquette of one real workflow from the catalogue.
// Evidence tiles ride the line, each station opens while it works, and everything stops at
// the gate until a person decides. One simulation drives the tiles, the stations, the panels
// and the ledger, so nothing on screen can disagree with the motion.

export interface RunStep {
  id: string;
  kind: string;
  type: string;
  title: string;
  detail: string;
  permission: string;
  output: string;
  failure: string | null;
  auto: string;
  manualToday: boolean;
}

export interface RunData {
  id: string;
  name: string;
  autonomy: string;
  approver: string;
  separationOfDuties: string;
  steps: RunStep[];
}

export type Decision = 'approved' | 'edited' | 'changes' | 'rejected' | 'escalated';

export interface RunEvent {
  run: string;
  decision: Decision;
  round: number;
  hash: string;
  prev: string;
}

type PathKey = 'main' | 'return' | 'reject';
type Phase = 'move' | 'dwell' | 'wait' | 'filed';

interface Tile {
  n: number;
  group: THREE.Group;
  top: THREE.Mesh;
  ctx: CanvasRenderingContext2D;
  tex: THREE.CanvasTexture;
  dirty: boolean;
  path: PathKey;
  s: number;
  stop: number;
  phase: Phase;
  t: number;
  round: number;
  items: number;
  checked: boolean;
  proposal: boolean;
  token: boolean;
  verified: boolean;
  decision: Decision | null;
  sla: number;
  escalated: boolean;
  stackIndex: number;
  stackT: number;
  from: THREE.Vector3;
}

const GAP = 1.15;
const SPEED = 2.1;
const SPACING = 2.55;
const DECK_Y = 0.44;
const SLA = 45;
const IDLE_RESUME = 25;
// How long each station works on a tile, in seconds. The gate has no dwell: it waits.
const DWELL = [0.9, 2.4, 2.6, 1.9, 2.0, 0, 1.5, 1.6, 1.4];
const GATE = 5;
const FILE = 8;
const SUGGEST = 3;
// 14 collected items: 12 pass, 1 fails, 1 cannot conclude.
const CHECKS = ['p', 'p', 'p', 'f', 'p', 'p', 'p', 'p', 'c', 'p', 'p', 'p', 'p', 'p'];

// Short names for the bench labels and the step list.
export const SHORT: Record<string, string> = {
  trigger: 'Start', collect: 'Collect', check: 'Check', suggest: 'Suggest', preflight: 'Dry run',
  ask: 'You', act: 'Act', verify: 'Verify', file: 'File',
};

const C = {
  white: 0xf8f8f6,
  deck: 0xc4c5bf,
  steel: 0xb4b8bd,
  ink: 0x15171a,
  orange: 0xff6b35,
  teal: 0x1f9d7a,
};

const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const clamp01 = (x: number) => Math.min(1, Math.max(0, x));

async function sha256(text: string) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, '0')).join('');
}

export function mountRunMachine(root: HTMLElement, data: RunData) {
  const canvas = root.querySelector<HTMLCanvasElement>('[data-rm-canvas]')!;
  const stage = canvas.parentElement!;
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarse = matchMedia('(pointer: coarse)').matches;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, coarse ? 1.5 : 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;
  scene.environmentIntensity = 0.5;

  const camera = new THREE.PerspectiveCamera(28, 1, 0.5, 200);

  const key = new THREE.DirectionalLight(0xffffff, 1.7);
  key.position.set(-8, 16, 10);
  key.castShadow = true;
  key.shadow.mapSize.set(coarse ? 1024 : 2048, coarse ? 1024 : 2048);
  key.shadow.camera.left = -15;
  key.shadow.camera.right = 15;
  key.shadow.camera.top = 8;
  key.shadow.camera.bottom = -8;
  key.shadow.camera.near = 1;
  key.shadow.camera.far = 50;
  key.shadow.bias = -0.0004;
  key.shadow.normalBias = 0.02;
  scene.add(key);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xd8d6d0, 0.35));

  // The one accent: an orange light that sits on the station working right now.
  const accentLight = new THREE.PointLight(C.orange, 0, 4.5, 2);
  accentLight.position.set(0, 1.6, 0.9);
  scene.add(accentLight);

  const mat = {
    white: new THREE.MeshStandardMaterial({ color: C.white, roughness: 0.62, metalness: 0 }),
    deck: new THREE.MeshStandardMaterial({ color: C.deck, roughness: 0.75, metalness: 0 }),
    steel: new THREE.MeshStandardMaterial({ color: 0x8d9298, roughness: 0.45, metalness: 0.6, envMapIntensity: 0.5 }),
    glass: new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.08, metalness: 0, transparent: true, opacity: 0.14, depthWrite: false }),
    accent: new THREE.MeshStandardMaterial({ color: C.orange, emissive: C.orange, emissiveIntensity: 0.6, roughness: 0.5 }),
    teal: new THREE.MeshStandardMaterial({ color: C.teal, roughness: 0.5 }),
    inkLine: new THREE.LineBasicMaterial({ color: C.ink, transparent: true, opacity: 0.4 }),
    scan: new THREE.MeshBasicMaterial({ color: C.orange, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide }),
  };

  const world = new THREE.Group();
  scene.add(world);

  function part(geo: THREE.BufferGeometry, m: THREE.Material, edges = true) {
    const mesh = new THREE.Mesh(geo, m);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    if (edges) mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 25), mat.inkLine));
    return mesh;
  }
  const box = (w: number, h: number, d: number, m = mat.white, edges = true) => part(new THREE.BoxGeometry(w, h, d), m, edges);
  const cyl = (r: number, h: number, m = mat.white, seg = 32, edges = true) => part(new THREE.CylinderGeometry(r, r, h, seg), m, edges);

  // Floor that only shows the shadows; the section's own background is the studio.
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.ShadowMaterial({ opacity: 0.16 }));
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  world.add(floor);

  const N = data.steps.length;
  const X = (i: number) => (i - (N - 1) / 2) * SPACING;
  const x0 = X(0);
  const xEnd = X(N - 1);

  const deck = part(new RoundedBoxGeometry(xEnd - x0 + 4.4, 0.3, 4.6, 4, 0.12), mat.deck, false);
  deck.position.set((x0 + xEnd) / 2 + 0.6, 0.15, 0);
  world.add(deck);

  // Rails: the main line, the return loop behind (request changes) and the reject line in front.
  const railY = 0.34;
  function rail(points: [number, number][]) {
    for (let k = 0; k < points.length - 1; k++) {
      const [ax, az] = points[k];
      const [bx, bz] = points[k + 1];
      const len = Math.hypot(bx - ax, bz - az);
      for (const off of [-0.2, 0.2]) {
        const r = cyl(0.025, len, mat.steel, 10, false);
        const nx = -(bz - az) / len;
        const nz = (bx - ax) / len;
        r.rotation.z = Math.PI / 2;
        r.rotation.y = -Math.atan2(bz - az, bx - ax);
        r.position.set((ax + bx) / 2 + nx * off, railY, (az + bz) / 2 + nz * off);
        world.add(r);
      }
    }
  }

  const gx = X(GATE);
  const paths: Record<PathKey, THREE.Vector2[]> = {
    main: [new THREE.Vector2(x0, 0), new THREE.Vector2(xEnd, 0)],
    return: [new THREE.Vector2(gx, 0), new THREE.Vector2(gx - 0.7, -1.55), new THREE.Vector2(X(SUGGEST) + 0.7, -1.55), new THREE.Vector2(X(SUGGEST), 0)],
    reject: [new THREE.Vector2(gx, 0), new THREE.Vector2(gx + 0.7, 1.55), new THREE.Vector2(xEnd - 0.7, 1.55), new THREE.Vector2(xEnd, 0)],
  };
  const lengths = Object.fromEntries(
    Object.entries(paths).map(([k, pts]) => [k, pts.slice(1).reduce((a, p, i) => a + p.distanceTo(pts[i]), 0)]),
  ) as Record<PathKey, number>;
  rail(paths.main.map((p) => [p.x, p.y]));
  rail(paths.return.map((p) => [p.x, p.y]));
  rail(paths.reject.map((p) => [p.x, p.y]));

  function pointOn(path: PathKey, s: number) {
    const pts = paths[path];
    let rest = s;
    for (let k = 0; k < pts.length - 1; k++) {
      const seg = pts[k].distanceTo(pts[k + 1]);
      if (rest <= seg || k === pts.length - 2) {
        const f = clamp01(rest / seg);
        const p = pts[k].clone().lerp(pts[k + 1], f);
        const dir = pts[k + 1].clone().sub(pts[k]).normalize();
        return { x: p.x, z: p.y, angle: Math.atan2(dir.y, dir.x) };
      }
      rest -= seg;
    }
    const last = pts[pts.length - 1];
    return { x: last.x, z: last.y, angle: 0 };
  }
  const stopS = data.steps.map((_, i) => X(i) - x0);

  // ---------- Stations: each has a mechanism that works while a tile dwells there. ----------
  interface Station {
    led: THREE.Mesh;
    work: (p: number, active: boolean, time: number) => void;
  }
  const stations: Station[] = [];
  let gateParts: { pivot: THREE.Group; stripe: THREE.Mesh; disc: THREE.Mesh } | null = null;

  function station(i: number) {
    const g = new THREE.Group();
    g.position.x = X(i);
    world.add(g);
    const plinth = part(new RoundedBoxGeometry(1.9, 0.12, 0.7, 3, 0.05), mat.white, false);
    plinth.position.set(0, 0.36, -1.25);
    g.add(plinth);
    const led = cyl(0.07, 0.04, mat.white.clone(), 20, false);
    led.position.set(0.72, 0.44, -1.25);
    g.add(led);
    return { g, led };
  }

  for (let i = 0; i < N; i++) {
    const kind = data.steps[i].kind;
    const { g, led } = station(i);
    let work: Station['work'] = () => {};

    if (kind === 'trigger') {
      const tower = box(0.55, 1.0, 0.55);
      tower.position.set(0, 0.8, -1.2);
      const button = cyl(0.16, 0.12, mat.accent.clone(), 32);
      button.position.set(0, 1.36, -1.2);
      g.add(tower, button);
      work = (p, active) => {
        button.position.y = 1.36 - (active ? Math.sin(Math.PI * clamp01(p * 2)) * 0.06 : 0);
        (button.material as THREE.MeshStandardMaterial).emissiveIntensity = active ? 0.9 : 0.15;
      };
    } else if (kind === 'collect') {
      const postA = box(0.12, 1.75, 0.12);
      const postB = box(0.12, 1.75, 0.12);
      postA.position.set(-0.75, 1.17, -1.25);
      postB.position.set(0.75, 1.17, -1.25);
      const beam = box(1.62, 0.12, 0.16);
      beam.position.set(0, 2.0, -1.25);
      const boom = box(0.16, 0.1, 1.6);
      boom.position.set(0, 1.92, -0.45);
      const carriage = box(0.26, 0.22, 0.26);
      const rod = cyl(0.03, 0.9, mat.steel, 10, false);
      const head = cyl(0.11, 0.06, mat.steel, 20);
      g.add(postA, postB, beam, boom, carriage, rod, head);
      const bins = [-0.5, 0, 0.5].map((bx) => {
        const b = box(0.36, 0.22, 0.36);
        b.position.set(bx, 0.53, -1.55);
        g.add(b);
        return b;
      });
      work = (p, active, time) => {
        // Three trips: bin to tile and back.
        const cycle = active ? (p * 3) % 1 : 0;
        const bin = active ? bins[Math.min(2, Math.floor(p * 3))].position.x : 0;
        const toTile = active ? Math.sin(Math.PI * cycle) : 0;
        const z = -1.55 + (0 + 1.55) * toTile;
        const x = bin * (1 - toTile);
        carriage.position.set(x, 1.78, z);
        const drop = active ? 0.22 + 0.28 * Math.abs(Math.sin(Math.PI * cycle * 2)) : 0.1;
        rod.position.set(x, 1.6 - drop, z);
        head.position.set(x, 1.6 - drop * 2 - 0.28, z);
        bins.forEach((b, k) => (b.position.y = 0.53 + (active && Math.floor(p * 3) === k ? 0.03 * Math.sin(time * 20) : 0)));
      };
    } else if (kind === 'check' || kind === 'verify') {
      const big = kind === 'check';
      const r = big ? 0.78 : 0.66;
      const arch = part(new THREE.TorusGeometry(r, 0.07, 14, 48, Math.PI), mat.white);
      arch.position.set(0, railY + 0.02, 0);
      g.add(arch);
      const scan = new THREE.Mesh(new THREE.PlaneGeometry(1.25, r * 0.95), mat.scan.clone());
      scan.rotation.y = Math.PI / 2;
      scan.position.set(0, DECK_Y + r * 0.45, 0);
      g.add(scan);
      const pins: THREE.Mesh[] = [];
      if (big) {
        for (let k = 0; k < 3; k++) {
          const pin = cyl(0.035, 0.32, mat.steel, 10, false);
          pin.position.set(0, railY + r + 0.1, -0.3 + k * 0.3);
          g.add(pin);
          pins.push(pin);
        }
        const lens = part(new THREE.TorusGeometry(0.16, 0.035, 10, 32), mat.white);
        lens.position.set(0, railY + r + 0.08, 0.55);
        g.add(lens);
        pins.push(lens);
      }
      work = (p, active) => {
        const m = scan.material as THREE.MeshBasicMaterial;
        m.opacity = active ? 0.22 * Math.sin(Math.PI * p) : 0;
        scan.position.x = active ? -0.55 + 1.1 * ((p * 2) % 1) : 0;
        // Rules first, model second: the pins drop in the first half, the lens turns in the second.
        pins.forEach((pin, k) => {
          if (k < 3) pin.position.y = railY + r + 0.1 - (active && p < 0.5 ? 0.12 * Math.sin(Math.PI * clamp01(p * 2 - k * 0.15)) : 0);
          else pin.rotation.x = active && p >= 0.5 ? (p - 0.5) * 12 : 0;
        });
      };
    } else if (kind === 'suggest' || kind === 'act') {
      const isAct = kind === 'act';
      const post = box(0.2, 1.7, 0.2);
      post.position.set(0, 1.15, -1.25);
      const arm = box(0.22, 0.16, 1.4);
      arm.position.set(0, 1.92, -0.6);
      const head = isAct ? cyl(0.13, 0.36, mat.teal, 24) : box(0.5, 0.18, 0.36);
      const shaft = cyl(0.04, 0.6, mat.steel, 10, false);
      g.add(post, arm, head, shaft);
      work = (p, active) => {
        const press = active ? Math.sin(Math.PI * clamp01((p - 0.2) / 0.6)) : 0;
        const y = 1.55 - press * 0.8;
        head.position.set(0, y, 0);
        shaft.position.set(0, y + 0.42, 0);
        if (isAct) head.visible = !(active && p > 0.55);
      };
    } else if (kind === 'preflight') {
      const cabinet = part(new THREE.BoxGeometry(1.5, 0.95, 1.2), mat.glass);
      cabinet.castShadow = false;
      cabinet.position.set(0, DECK_Y + 0.5, 0);
      g.add(cabinet);
      const ghost = new THREE.Mesh(new THREE.BoxGeometry(0.86, 0.05, 0.58), new THREE.MeshBasicMaterial({ color: C.orange, transparent: true, opacity: 0 }));
      ghost.position.set(0, DECK_Y + 0.55, 0);
      g.add(ghost);
      const ring = new THREE.Mesh(new THREE.RingGeometry(0.98, 1.0, 64), new THREE.MeshBasicMaterial({ color: C.orange, transparent: true, opacity: 0, side: THREE.DoubleSide }));
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(0, 0.31, 0);
      g.add(ring);
      work = (p, active) => {
        const gm = ghost.material as THREE.MeshBasicMaterial;
        gm.opacity = active ? 0.35 * Math.sin(Math.PI * p) : 0;
        ghost.position.x = active ? Math.sin(p * Math.PI * 2) * 0.25 : 0;
        // Blast radius: one record.
        const rm = ring.material as THREE.MeshBasicMaterial;
        rm.opacity = active ? 0.6 * (1 - ((p * 2) % 1)) : 0;
        const s = active ? 0.4 + 0.6 * ((p * 2) % 1) : 1;
        ring.scale.set(s, s, s);
      };
    } else if (kind === 'ask') {
      const postA = box(0.26, 1.2, 0.26);
      const postB = box(0.26, 1.2, 0.26);
      postA.position.set(0, 0.9, -0.85);
      postB.position.set(0, 0.9, 0.85);
      const pivot = new THREE.Group();
      pivot.position.set(0, 1.18, -0.85);
      const bar = box(0.16, 0.16, 1.85);
      bar.position.set(0, 0, 0.85);
      const stripe = box(0.17, 0.05, 0.9, mat.accent);
      stripe.position.set(0, 0.06, 1.05);
      pivot.add(bar, stripe);
      const disc = cyl(0.62, 0.04, mat.white, 48);
      disc.position.set(0, 0.32, 0);
      g.add(postA, postB, pivot, disc);
      gateParts = { pivot, stripe, disc };
      work = () => {};
    } else if (kind === 'file') {
      const column = cyl(0.03, 3.4, mat.steel, 10, false);
      column.position.set(1.65, 2.0, 0);
      const foot = cyl(0.55, 0.08, mat.white, 40);
      foot.position.set(1.65, 0.34, 0);
      const slot = box(1.2, 0.5, 0.18);
      slot.position.set(0, 0.6, -0.9);
      g.add(column, foot, slot);
      work = () => {};
    }
    stations.push({ led, work });
  }

  // ---------- Tiles ----------
  const tileGeo = new RoundedBoxGeometry(1.12, 0.09, 0.78, 2, 0.025);
  const topGeo = new THREE.PlaneGeometry(1.08, 0.74);
  const tokenGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.1, 20);
  const tiles: Tile[] = [];
  let runCounter = 41;
  let filedCount = 0;

  function makeTile(): Tile {
    const group = new THREE.Group();
    const body = new THREE.Mesh(tileGeo, mat.white);
    body.castShadow = true;
    body.receiveShadow = true;
    group.add(body);
    const cv = document.createElement('canvas');
    cv.width = 360;
    cv.height = 244;
    const ctx = cv.getContext('2d')!;
    const tex = new THREE.CanvasTexture(cv);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 4;
    const top = new THREE.Mesh(topGeo, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.7 }));
    top.rotation.x = -Math.PI / 2;
    top.position.y = 0.0455;
    top.receiveShadow = true;
    group.add(top);
    const token = new THREE.Mesh(tokenGeo, mat.teal);
    token.position.set(0.38, 0.11, -0.22);
    token.visible = false;
    token.name = 'token';
    token.castShadow = true;
    group.add(token);
    world.add(group);
    runCounter += 1;
    const t: Tile = {
      n: runCounter, group, top, ctx, tex, dirty: true, path: 'main', s: 0, stop: 0, phase: 'dwell', t: 0, round: 0,
      items: 0, checked: false, proposal: false, token: false, verified: false, decision: null, sla: SLA, escalated: false,
      stackIndex: -1, stackT: 0, from: new THREE.Vector3(),
    };
    tiles.push(t);
    return t;
  }

  function drawTile(t: Tile) {
    const { ctx } = t;
    const W = 360;
    const H = 244;
    const rejected = t.decision === 'rejected';
    const approved = t.verified;
    ctx.fillStyle = approved ? '#1f9d7a' : rejected ? '#e9e8e4' : '#fbfbfa';
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = approved ? '#0f6e56' : '#15171a';
    ctx.lineWidth = 6;
    ctx.strokeRect(3, 3, W - 6, H - 6);
    const ink = approved ? '#ffffff' : '#15171a';
    const dim = approved ? 'rgba(255,255,255,0.7)' : '#8a9099';
    ctx.font = '600 24px Inter, system-ui, sans-serif';
    ctx.fillStyle = ink;
    ctx.fillText(`RUN ${String(t.n).padStart(4, '0')}`, 22, 40);
    ctx.font = '500 18px ui-monospace, Menlo, monospace';
    ctx.fillStyle = dim;
    ctx.fillText(t.round ? `round ${t.round + 1}` : 'release gate', 22, 66);
    // Collected items, then their check result.
    for (let k = 0; k < 14; k++) {
      const x = 22 + (k % 7) * 46;
      const y = 92 + Math.floor(k / 7) * 34;
      const has = k < t.items;
      const r = t.checked ? CHECKS[k] : 'p';
      if (!has) {
        ctx.strokeStyle = approved ? 'rgba(255,255,255,0.35)' : 'rgba(21,23,26,0.14)';
        ctx.lineWidth = 2;
        ctx.strokeRect(x + 1, y + 1, 32, 22);
        continue;
      }
      if (t.checked && r === 'f') ctx.fillStyle = '#ff6b35';
      else if (t.checked && r === 'c') {
        ctx.strokeStyle = ink;
        ctx.lineWidth = 2.5;
        ctx.strokeRect(x + 1, y + 1, 32, 22);
        continue;
      } else ctx.fillStyle = approved ? 'rgba(255,255,255,0.92)' : '#15171a';
      ctx.fillRect(x, y, 34, 24);
    }
    ctx.font = '500 19px ui-monospace, Menlo, monospace';
    ctx.fillStyle = ink;
    if (t.proposal) ctx.fillText('GO 5% → 25% → ALL · conf 0.81', 22, 196);
    if (t.decision && t.decision !== 'changes' && t.decision !== 'escalated') {
      const label = { approved: 'APPROVED', edited: 'APPROVED WITH EDITS', rejected: 'REJECTED · REASON FILED', changes: '', escalated: '' }[t.decision];
      ctx.font = '600 19px Inter, system-ui, sans-serif';
      ctx.fillText(label, 22, 228);
    }
    if (rejected) {
      ctx.strokeStyle = '#15171a';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(18, 30);
      ctx.lineTo(W - 18, 30);
      ctx.stroke();
    }
    t.tex.needsUpdate = true;
    t.dirty = false;
  }

  function ahead(t: Tile) {
    let best: Tile | null = null;
    for (const o of tiles) {
      if (o === t || o.phase === 'filed' || o.path !== t.path || o.s <= t.s) continue;
      if (!best || o.s < best.s) best = o;
    }
    return best;
  }
  const occupiedNear = (s: number) => tiles.some((o) => o.path === 'main' && o.phase !== 'filed' && Math.abs(o.s - s) < GAP);

  const stack: Tile[] = [];
  const front = () => tiles.find((t) => t.phase === 'wait' && t.stop === GATE) ?? null;

  let gateOpen = 0;
  let gateOpenTarget = 0;
  let discTurn = 0;
  let discTarget = 0;
  let spawnClock = 0;
  let prevHash = '0'.repeat(64);
  let slaRunning = false;

  // ---------- The panels around the machine ----------
  const q = <T extends Element>(sel: string) => root.querySelector<T>(sel);
  const stationButtons = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-rm-station]'));
  const labelsLayer = q<HTMLElement>('[data-rm-labels]');
  const labels = data.steps.map((s, i) => {
    const el = document.createElement('div');
    el.className = 'rm-label';
    el.innerHTML = `<span>${String(i + 1).padStart(2, '0')}</span>${SHORT[s.kind] ?? s.type}`;
    labelsLayer?.appendChild(el);
    return el;
  });
  const readout = {
    index: q<HTMLElement>('[data-rm-r="index"]'),
    title: q<HTMLElement>('[data-rm-r="title"]'),
    detail: q<HTMLElement>('[data-rm-r="detail"]'),
    permission: q<HTMLElement>('[data-rm-r="permission"]'),
    output: q<HTMLElement>('[data-rm-r="output"]'),
    failure: q<HTMLElement>('[data-rm-r="failure"]'),
    who: q<HTMLElement>('[data-rm-r="who"]'),
  };
  const gateBar = q<HTMLElement>('[data-rm-gate]');
  const proposal = q<HTMLElement>('[data-rm-proposal]');
  const slaEl = q<HTMLElement>('[data-rm-sla]');
  const statusEl = q<HTMLElement>('[data-rm-status]');
  const filedEl = q<HTMLElement>('[data-rm-filed]');
  const headEl = q<HTMLElement>('[data-rm-head]');
  const runEl = q<HTMLElement>('[data-rm-run]');
  const decideButtons = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-rm-decide]'));
  const modeButtons = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-rm-mode]'));
  const cursor = q<HTMLElement>('[data-rm-cursor]');
  const caption = q<HTMLElement>('[data-rm-caption]');

  let mode: 'designed' | 'today' = 'designed';
  let shown = -1;
  let follow = true;

  function who(i: number) {
    const s = data.steps[i];
    if (s.kind === 'ask') return 'A person decides. Deny by default.';
    if (mode === 'today') return s.manualToday ? 'Today a person completes this step. The ledger records it as manual.' : 'Runs itself today.';
    if (s.auto === 'Yes, after approval') return 'Runs itself, only after approval.';
    return s.auto === 'Yes' ? 'Runs itself.' : 'Waits for a person.';
  }

  function show(i: number) {
    shown = i;
    const s = data.steps[i];
    if (readout.index) readout.index.textContent = `${String(i + 1).padStart(2, '0')} / ${String(N).padStart(2, '0')} · ${s.type}`;
    if (readout.title) readout.title.textContent = s.title;
    if (readout.detail) readout.detail.textContent = s.kind === 'ask' ? `Sends ${data.approver} a decision card: what would change, why, the risk if approved, the agent's confidence band and links to the evidence. ${data.separationOfDuties}.` : s.detail.replace(/;\s*\.\.\.$/, '.').replace(/ Also files.*$/, ' Also files the agent trace, hashed, against every requirement it maps to.');
    if (readout.permission) readout.permission.textContent = s.permission;
    if (readout.output) readout.output.textContent = s.output;
    if (readout.failure) readout.failure.textContent = s.failure ?? 'None';
    if (readout.who) readout.who.textContent = who(i);
    stationButtons.forEach((b, k) => b.setAttribute('aria-pressed', String(k === i)));
  }

  function setMode(m: 'designed' | 'today') {
    mode = m;
    modeButtons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.rmMode === m)));
    root.dataset.mode = m;
    stationButtons.forEach((b, i) => {
      const w = b.querySelector<HTMLElement>('[data-rm-who]');
      if (w) w.textContent = data.steps[i].kind === 'ask' ? 'You' : mode === 'today' && data.steps[i].manualToday ? 'Person' : 'Agent';
    });
    if (shown >= 0) show(shown);
  }

  function announce(text: string) {
    if (statusEl) statusEl.textContent = text;
  }

  // Records hash one after another, so each links to the head before it.
  let chain = Promise.resolve();
  function record(t: Tile, decision: Decision) {
    const run = `run-${String(t.n).padStart(4, '0')}`;
    const round = t.round;
    chain = chain.then(() => write(run, decision, round));
    return chain;
  }

  async function write(run: string, decision: Decision, round: number) {
    const prev = prevHash;
    const hash = await sha256(`${prev}|${data.id}|${run}|${decision}|${round}`);
    prevHash = hash;
    if (decision !== 'changes' && decision !== 'escalated') {
      filedCount += 1;
      if (filedEl) filedEl.textContent = String(filedCount);
    }
    if (headEl) headEl.textContent = `${hash.slice(0, 4)}…${hash.slice(-4)}`;
    const detail: RunEvent = { run, decision, round, hash, prev };
    window.dispatchEvent(new CustomEvent<RunEvent>('fm:run', { detail }));
  }

  function updateGateBar() {
    const f = front();
    const has = !!f;
    gateBar?.toggleAttribute('data-waiting', has);
    decideButtons.forEach((b) => (b.disabled = !has));
    if (!proposal) return;
    if (!f) {
      proposal.textContent = 'No proposal at the gate yet. The next run is on its way.';
      if (slaEl) slaEl.textContent = '';
      return;
    }
    const rnd = f.round ? ` Round ${f.round + 1} of 4, revised from your comments.` : '';
    proposal.textContent = `Release credit-scoring v2.4 to a 5% cohort, then 25%, then everyone. 12 of 14 checks pass, 1 fails, 1 cannot conclude. Confidence 0.78 to 0.84.${rnd}`;
  }

  function decide(d: 'approve' | 'edits' | 'changes' | 'reject') {
    const f = front();
    if (!f) return;
    if (d === 'approve' || d === 'edits') {
      f.decision = d === 'approve' ? 'approved' : 'edited';
      f.stop = GATE + 1;
      f.phase = 'move';
      gateOpenTarget = 1;
      announce(d === 'approve' ? `Run ${f.n} approved. Act, verify and file run now.` : `Run ${f.n} approved with your edits. The edits are filed with the decision.`);
    } else if (d === 'changes') {
      if (f.round >= 3) {
        f.escalated = true;
        announce(`Round 4 reached. Run ${f.n} escalates to the Head of AI governance. Nothing is recorded or changed.`);
        void record(f, 'escalated');
        updateGateBar();
        return;
      }
      f.round += 1;
      f.decision = 'changes';
      f.proposal = false;
      f.path = 'return';
      f.s = 0;
      f.phase = 'move';
      f.sla = SLA;
      f.dirty = true;
      discTarget += Math.PI / 2;
      announce(`Changes requested on run ${f.n}. It goes back to suggest, round ${f.round + 1} of 4.`);
      void record(f, 'changes');
    } else {
      f.decision = 'rejected';
      f.path = 'reject';
      f.s = 0;
      f.phase = 'move';
      f.dirty = true;
      discTarget -= Math.PI / 2;
      announce(`Run ${f.n} rejected. Act and verify never run. The rejection is filed with its reason.`);
    }
    updateGateBar();
  }

  decideButtons.forEach((b) =>
    b.addEventListener('click', () => {
      userActed();
      decide(b.dataset.rmDecide as 'approve' | 'edits' | 'changes' | 'reject');
    }),
  );
  stationButtons.forEach((b, i) =>
    b.addEventListener('click', () => {
      userActed();
      follow = false;
      focus = i;
      show(i);
    }),
  );
  modeButtons.forEach((b) => b.addEventListener('click', () => setMode(b.dataset.rmMode as 'designed' | 'today')));

  // ---------- Simulation ----------
  function step(dt: number) {
    spawnClock += dt;
    if (spawnClock > 6.5 && !occupiedNear(0) && tiles.filter((t) => t.phase !== 'filed').length < 7) {
      spawnClock = 0;
      makeTile();
    }

    // Front tiles first so the ones behind see where they stopped.
    const order = tiles.filter((t) => t.phase !== 'filed').sort((a, b) => b.s - a.s);
    for (const t of order) {
      if (t.phase === 'move') {
        const target = t.path === 'main' ? stopS[t.stop] : lengths[t.path];
        let max = target;
        const a = ahead(t);
        if (a) max = Math.min(max, a.s - GAP);
        if (t.path === 'main' && t.stop > GATE && t.s < stopS[GATE] + 0.01) max = Math.min(max, gateOpen > 0.85 ? target : stopS[GATE]);
        t.s = Math.min(t.s + SPEED * dt, Math.max(t.s, max));
        if (t.s >= target - 1e-3) {
          if (t.path === 'return') {
            if (occupiedNear(stopS[SUGGEST])) continue;
            t.path = 'main';
            t.s = stopS[SUGGEST];
            t.stop = SUGGEST;
          } else if (t.path === 'reject') {
            if (occupiedNear(stopS[FILE])) continue;
            t.path = 'main';
            t.s = stopS[FILE];
            t.stop = FILE;
          }
          t.phase = t.stop === GATE ? 'wait' : 'dwell';
          t.t = 0;
          if (t.stop === GATE) {
            t.sla = SLA;
            t.escalated = false;
            updateGateBar();
            if (follow) focus = GATE;
          }
        }
      } else if (t.phase === 'dwell') {
        t.t += dt;
        const p = clamp01(t.t / DWELL[t.stop]);
        const kind = data.steps[t.stop].kind;
        if (kind === 'collect' && t.items !== Math.ceil(14 * p)) {
          t.items = Math.ceil(14 * p);
          t.dirty = true;
        }
        if (kind === 'check' && p > 0.55 && !t.checked) {
          t.checked = true;
          t.dirty = true;
        }
        if (kind === 'suggest' && p > 0.6 && !t.proposal) {
          t.proposal = true;
          t.dirty = true;
        }
        if (kind === 'act' && p > 0.55 && !t.token) {
          t.token = true;
          t.group.getObjectByName('token')!.visible = true;
        }
        if (kind === 'verify' && p > 0.6 && !t.verified && t.decision !== 'rejected') {
          t.verified = true;
          t.dirty = true;
        }
        if (p >= 1) {
          if (t.stop === FILE) {
            t.phase = 'filed';
            t.from.copy(t.group.position);
            t.stackIndex = stack.length;
            t.stackT = 0;
            stack.push(t);
            void record(t, t.decision ?? 'approved');
          } else {
            t.stop += 1;
            t.phase = 'move';
            if (t.stop === GATE + 2) gateOpenTarget = 0;
          }
        }
      } else if (t.phase === 'wait' && slaRunning) {
        t.sla -= dt;
        if (t.sla <= 0 && !t.escalated) {
          t.escalated = true;
          announce(`No decision on run ${t.n} within the SLA. Escalated to the approver's delegate. The run stays paused; nothing is recorded or changed.`);
          void record(t, 'escalated');
        }
      }
    }

    gateOpen += (gateOpenTarget - gateOpen) * Math.min(1, dt * 3.2);
    discTurn += (discTarget - discTurn) * Math.min(1, dt * 3);

    // Keep the ledger column short: the oldest plates sink away.
    while (stack.length > 9) {
      const old = stack.shift()!;
      world.remove(old.group);
      tiles.splice(tiles.indexOf(old), 1);
      stack.forEach((s, k) => (s.stackIndex = k));
    }
  }

  // ---------- Camera ----------
  let focus: number | null = null;
  const camPos = new THREE.Vector3();
  const camLook = new THREE.Vector3();
  const wantPos = new THREE.Vector3();
  const wantLook = new THREE.Vector3();
  const overviewPos = new THREE.Vector3(12.1, 15.9, 27.5);
  const overviewLook = new THREE.Vector3(0, 0.4, 0);
  let yaw = 0;
  let pitch = 0;
  let narrow = false;
  let blockers: { l: number; r: number; t: number; b: number }[] = [];
  let floorY = 99999;

  function pose(i: number | null) {
    if (i === null && narrow) {
      // A phone cannot hold the whole bench legibly: frame the middle, where the gate is.
      wantPos.set(X(GATE) + 8, 9.5, 14);
      wantLook.set(X(GATE) - 1.2, -0.2, 0.4);
    } else if (i === null) {
      wantPos.copy(overviewPos);
      wantLook.copy(overviewLook);
    } else {
      const x = X(i) + (i === FILE ? 0.8 : 0);
      if (narrow) {
        wantPos.set(x + 6.5, 9, 16.25);
        wantLook.set(x + 1.6, -0.6, 1.2);
      } else {
        wantLook.set(x, 0.9, 0.2);
        wantPos.set(x + 2.9, 7.1, 9.6);
      }
    }
    // Drag orbits around the look point.
    const off = wantPos.clone().sub(wantLook);
    off.applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
    const right = new THREE.Vector3().crossVectors(off, new THREE.Vector3(0, 1, 0)).normalize();
    off.applyAxisAngle(right, pitch);
    wantPos.copy(wantLook).add(off);
  }

  // ---------- Tour: left alone, the page shows itself. It never presses Approve. ----------
  const TOUR: { at: number | null; hold: number; gate?: boolean }[] = [
    { at: null, hold: 3.5 },
    { at: 1, hold: 3.4 },
    { at: 2, hold: 3.6 },
    { at: 3, hold: 3.0 },
    { at: 4, hold: 3.0 },
    { at: GATE, hold: 6.5, gate: true },
    { at: 7, hold: 3.0 },
    { at: FILE, hold: 3.2 },
  ];
  let touring = !reduceMotion;
  let tourIdx = 0;
  let tourClock = 0;
  let entered = false;
  let idleClock = 0;

  function userActed() {
    touring = false;
    idleClock = 0;
    cursor?.removeAttribute('data-on');
    caption?.removeAttribute('data-on');
    decideButtons.forEach((b) => b.classList.remove('is-hover'));
  }
  root.addEventListener('pointerdown', userActed);
  root.addEventListener('keydown', userActed);

  function moveCursorTo(el: Element | null) {
    if (!cursor || !el || coarse) return;
    const r = el.getBoundingClientRect();
    const rr = stage.getBoundingClientRect();
    cursor.style.transform = `translate3d(${r.left - rr.left + r.width * 0.55}px, ${r.top - rr.top + r.height * 0.6}px, 0)`;
    cursor.setAttribute('data-on', '');
  }

  function tour(dt: number) {
    if (!touring) {
      idleClock += dt;
      if (idleClock > IDLE_RESUME && !reduceMotion) {
        touring = true;
        follow = true;
        yaw = 0;
        pitch = 0;
        tourClock = 0;
        entered = false;
      }
      return;
    }
    tourClock += dt;
    const beat = TOUR[tourIdx];
    if (!entered) {
      entered = true;
      focus = beat.at;
      if (beat.at !== null) show(beat.at);
      moveCursorTo(beat.at === null ? null : stationButtons[beat.at]);
      if (beat.at === null) cursor?.removeAttribute('data-on');
    }
    if (beat.gate && tourClock > 2.2 && tourClock - dt <= 2.2) {
      const approve = decideButtons.find((b) => b.dataset.rmDecide === 'approve') ?? null;
      moveCursorTo(approve);
      approve?.classList.add('is-hover');
      caption?.setAttribute('data-on', '');
    }
    if (tourClock > beat.hold) {
      decideButtons.forEach((b) => b.classList.remove('is-hover'));
      caption?.removeAttribute('data-on');
      tourIdx = (tourIdx + 1) % TOUR.length;
      tourClock = 0;
      entered = false;
    }
  }

  // Drag to orbit. The wheel stays with the page.
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  canvas.addEventListener('pointerdown', (e) => {
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    yaw = Math.max(-0.7, Math.min(0.7, yaw - (e.clientX - lastX) * 0.005));
    pitch = Math.max(-0.25, Math.min(0.35, pitch - (e.clientY - lastY) * 0.004));
    lastX = e.clientX;
    lastY = e.clientY;
  });
  const endDrag = () => (dragging = false);
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', endDrag);

  // ---------- Frame ----------
  const v = new THREE.Vector3();
  let time = 0;
  let frames = 0;
  function frame(dt: number) {
    time += dt;
    if (frames++ % 30 === 0) {
      if (canvas.clientWidth !== sizeW || canvas.clientHeight !== sizeH) resize();
      measureClear();
    }
    step(dt);
    tour(dt);

    // Which station is working right now, for the accent and the readout.
    const activeStops = new Map<number, number>();
    for (const t of tiles) {
      if (t.phase === 'dwell') activeStops.set(t.stop, clamp01(t.t / DWELL[t.stop]));
      if (t.phase === 'wait') activeStops.set(GATE, 1);
    }
    const f = front();
    if (follow && !touring && f) focus = GATE;
    if (!touring && follow && focus !== null && shown !== focus) show(focus);

    stations.forEach((st, i) => {
      const active = activeStops.has(i);
      const p = activeStops.get(i) ?? 0;
      st.work(p, active, time);
      const ledMat = st.led.material as THREE.MeshStandardMaterial;
      const isGate = i === GATE && !!f;
      ledMat.color.set(active || isGate ? C.orange : C.white);
      ledMat.emissive.set(active || isGate ? C.orange : 0x000000);
      ledMat.emissiveIntensity = isGate ? 0.6 + 0.4 * Math.sin(time * 4) : active ? 0.8 : 0;
      labels[i].classList.toggle('is-active', active || isGate);
      stationButtons[i]?.classList.toggle('is-working', active || isGate);
    });

    // Accent light follows the gate when someone is needed, otherwise the working station.
    const accentAt = f ? GATE : [...activeStops.keys()].pop();
    if (accentAt !== undefined) {
      accentLight.position.x += (X(accentAt) - accentLight.position.x) * Math.min(1, dt * 4);
      accentLight.intensity += ((f ? 5 + 2 * Math.sin(time * 4) : 3) - accentLight.intensity) * Math.min(1, dt * 4);
    } else accentLight.intensity *= 1 - Math.min(1, dt * 3);

    // The gate: the bar lifts only after a decision.
    const g = gateParts;
    if (g) {
      g.pivot.rotation.x = -ease(clamp01(gateOpen)) * 1.35;
      (g.stripe.material as THREE.MeshStandardMaterial).emissiveIntensity = f ? 0.7 + 0.5 * Math.sin(time * 4) : 0.25;
      g.disc.rotation.y = discTurn;
    }

    for (const t of tiles) {
      if (t.dirty) drawTile(t);
      if (t.phase === 'filed') {
        t.stackT = Math.min(1, t.stackT + dt * 1.4);
        const target = v.set(X(FILE) + 1.65, 0.46 + t.stackIndex * 0.12, 0);
        const e = ease(t.stackT);
        t.group.position.lerpVectors(t.from, target, e);
        t.group.position.y += Math.sin(Math.PI * e) * 0.6;
        t.group.rotation.y = 0;
        continue;
      }
      const pt = pointOn(t.path, t.s);
      t.group.position.set(pt.x, DECK_Y, pt.z);
      t.group.rotation.y = -pt.angle;
    }

    // Camera eases to its pose; labels follow the projection.
    pose(focus);
    const k = Math.min(1, dt * (reduceMotion ? 20 : 2.4));
    camPos.lerp(wantPos, k);
    camLook.lerp(wantLook, k);
    camera.position.copy(camPos);
    camera.lookAt(camLook);

    const rect = { width: sizeW, height: sizeH };
    labels.forEach((el, i) => {
      v.set(X(i), i === GATE ? 1.85 : 2.35, -1.25).project(camera);
      const x = (v.x * 0.5 + 0.5) * rect.width;
      const y = (-v.y * 0.5 + 0.5) * rect.height;
      el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0) translate(-50%, -100%)`;
      const hidden = v.z > 1 || y > floorY || blockers.some((b) => x > b.l && x < b.r && y > b.t && y < b.b + 30);
      el.style.opacity = hidden ? '0' : '';
    });

    if (f && slaEl) {
      const left = Math.max(0, Math.ceil(f.sla));
      slaEl.textContent = f.escalated ? 'Escalated. Still paused, still waiting on a person.' : `Decision due in 0:${String(left).padStart(2, '0')}`;
    }

    renderer.render(scene, camera);
  }

  // Labels hide where the side panels sit over the bench.
  function measureClear() {
    const sr = stage.getBoundingClientRect();
    const overlay = getComputedStyle(q<HTMLElement>('.rm-hud')!).position === 'absolute';
    const rel = (el: HTMLElement | null) => {
      const r = el?.getBoundingClientRect();
      return r && overlay ? { l: r.left - sr.left - 70, r: r.right - sr.left + 70, t: r.top - sr.top - 12, b: r.bottom - sr.top + 12 } : null;
    };
    blockers = [rel(q('.rm-readout')), rel(q('.rm-run')), rel(q('.rm-stations')), rel(q('.rm-gate'))].filter(Boolean) as typeof blockers;
    // Everything below the step strip belongs to the panels.
    const strip = rel(q('.rm-stations'));
    floorY = strip ? strip.t : sr.height + 40;
    // Centre the projection on the part of the stage the panels leave clear.
    const ro = rel(q('.rm-readout'));
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (w && h) camera.setViewOffset(w, h, ro ? w / 2 - (ro.l + 70) / 2 : 0, strip ? h / 2 - strip.t / 2 : 0, w, h);
  }

  let sizeW = 0;
  let sizeH = 0;
  function resize() {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    sizeW = w;
    sizeH = h;
    if (!w || !h) return;
    measureClear();
    narrow = w < 760;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.fov = narrow ? 34 : 23;
    camera.updateProjectionMatrix();
    // setSize clears the canvas; draw straight away in case no animation frame is coming.
    renderer.render(scene, camera);
  }
  new ResizeObserver(resize).observe(canvas);
  resize();

  // Warm up: run the line until a proposal is waiting at the gate, so the first frame shows it.
  makeTile();
  for (let k = 0; k < 60 * 40 && !front(); k++) step(1 / 60);
  for (let k = 0; k < 60 * 9; k++) step(1 / 60);
  pose(null);
  camPos.copy(wantPos);
  camLook.copy(wantLook);
  runEl && (runEl.textContent = `run-${String(front()?.n ?? runCounter).padStart(4, '0')}`);
  setMode('designed');
  show(GATE);
  updateGateBar();
  renderer.compile(scene, camera);

  let visible = false;
  let last = 0;
  let raf = 0;
  function loop(now: number) {
    raf = requestAnimationFrame(loop);
    const dt = Math.min(0.05, (now - last) / 1000 || 0);
    last = now;
    frame(dt);
  }
  new IntersectionObserver(
    ([e]) => {
      visible = e.isIntersecting;
      slaRunning = visible;
      if (visible && !document.hidden) {
        last = performance.now();
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(loop);
      } else cancelAnimationFrame(raf);
    },
    { threshold: 0.15 },
  ).observe(root);
  document.addEventListener('visibilitychange', () => {
    cancelAnimationFrame(raf);
    if (visible && !document.hidden) {
      last = performance.now();
      raf = requestAnimationFrame(loop);
    }
  });
  frame(0);
}

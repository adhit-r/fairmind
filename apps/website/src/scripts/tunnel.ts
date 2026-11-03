import * as THREE from 'three';

// The hero: a tunnel of evidence tiles the agent already checked. They stay grey
// until the visitor's cursor approves them. Scroll flies the camera down the run.
export function mountTunnel(story: HTMLElement, stage: HTMLElement, canvas: HTMLCanvasElement, counterEl: HTMLElement) {
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarse = matchMedia('(pointer: coarse)').matches;
  const narrow = innerWidth < 900;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, narrow ? 1.5 : 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(58, 1, 0.1, 120);

  const N = narrow ? 9000 : 24000;
  const COLS = narrow ? 44 : 60;
  const R = 5.2;
  const LEN = 120;
  const geo = new THREE.PlaneGeometry(0.4, 0.22);
  const seedAttr = new Float32Array(N);
  const approvedAttr = new Float32Array(N);
  geo.setAttribute('aSeed', new THREE.InstancedBufferAttribute(seedAttr, 1));
  const approvedBuf = new THREE.InstancedBufferAttribute(approvedAttr, 1);
  approvedBuf.setUsage(THREE.DynamicDrawUsage);
  geo.setAttribute('aApproved', approvedBuf);

  const uniforms = {
    uRayO: { value: new THREE.Vector3() },
    uRayD: { value: new THREE.Vector3(0, 0, -1) },
    uTime: { value: 0 },
    uRadius: { value: 1.5 },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexShader: `
      attribute float aSeed; attribute float aApproved;
      uniform vec3 uRayO, uRayD; uniform float uTime, uRadius;
      varying float vLens, vApproved, vFog, vShade; varying vec2 vUv;
      void main(){
        vec4 c = instanceMatrix * vec4(0.,0.,0.,1.);
        vec3 toC = c.xyz - uRayO; float tp = max(dot(toC, uRayD), 0.); vec3 closest = uRayO + uRayD * tp;
        float lens = 1.0 - smoothstep(0., uRadius, distance(c.xyz, closest));
        float a = max(lens, aApproved);
        vec3 pos = position * (1.0 + a * 0.9 + 0.08 * sin(uTime * 1.3 + aSeed * 6.283));
        vec4 w = instanceMatrix * vec4(pos, 1.);
        w.xy += -normalize(c.xy) * a * 0.45;
        vec4 mv = modelViewMatrix * w;
        vFog = clamp((-mv.z - 2.0) / 26.0, 0., 1.);
        vLens = lens; vApproved = aApproved; vUv = uv;
        vec3 n = normalize(mat3(instanceMatrix) * normal);
        vShade = 0.5 + 0.5 * dot(n, normalize(vec3(0.2, 0.9, 0.4)));
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      varying float vLens, vApproved, vFog, vShade; varying vec2 vUv;
      void main(){
        float a = max(vLens, vApproved);
        vec3 grey = vec3(0.90, 0.90, 0.88) * (0.92 + 0.08 * vShade);
        vec2 pb = abs(vUv - 0.5) * 2.0; float edge = smoothstep(0.78, 0.86, max(pb.x, pb.y));
        grey = mix(grey, grey * 0.9, edge);
        vec3 teal = mix(vec3(0.10, 0.58, 0.45), vec3(0.55, 0.88, 0.78), vShade * 0.7);
        vec3 col = mix(grey, teal, a) + vLens * 0.12;
        float r = 0.42; vec2 q = max(pb - (1.0 - r), 0.0);
        float alpha = 1.0 - smoothstep(0.88, 1.0, length(q) / r);
        col = mix(col, vec3(1.0), vFog);
        gl_FragColor = vec4(col, alpha * (1.0 - vFog * 0.92));
      }`,
  });

  const tiles = new THREE.InstancedMesh(geo, mat, N);
  const dummy = new THREE.Object3D();
  const centers = new Float32Array(N * 3);
  const ROWS = N / COLS;
  for (let i = 0; i < N; i++) {
    const row = Math.floor(i / COLS);
    const col = i % COLS;
    const th = ((col + (row % 2) * 0.5) / COLS) * Math.PI * 2 + (Math.random() - 0.5) * 0.02;
    const rr = R + (Math.random() - 0.5) * 0.25;
    const z = 6 - (row / ROWS) * LEN - Math.random() * 0.12;
    dummy.position.set(Math.cos(th) * rr, Math.sin(th) * rr, z);
    dummy.lookAt(0, 0, z);
    dummy.rotateZ((Math.random() - 0.5) * 0.12);
    dummy.rotateY((Math.random() - 0.5) * 0.25);
    const sc = 0.85 + Math.random() * 0.3;
    dummy.scale.set(sc, sc * (0.8 + Math.random() * 0.5), 1);
    dummy.updateMatrix();
    tiles.setMatrixAt(i, dummy.matrix);
    centers[i * 3] = dummy.position.x;
    centers[i * 3 + 1] = dummy.position.y;
    centers[i * 3 + 2] = z;
    seedAttr[i] = Math.random();
  }
  scene.add(tiles);

  const pointer = new THREE.Vector2(0, 0);
  let hasPointer = false;
  const onPoint = (clientX: number, clientY: number) => {
    const r = stage.getBoundingClientRect();
    if (clientY > r.bottom || clientY < r.top) {
      hasPointer = false;
      return;
    }
    pointer.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    hasPointer = true;
  };
  addEventListener('pointermove', (e) => onPoint(e.clientX, e.clientY), { passive: true });
  if (coarse) {
    addEventListener('touchmove', (e) => onPoint(e.touches[0].clientX, e.touches[0].clientY), { passive: true });
    addEventListener('touchend', () => (hasPointer = false));
  }

  const resize = () => {
    const w = stage.clientWidth;
    const h = stage.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  addEventListener('resize', resize);
  resize();

  let scroll = 0;
  const onScroll = () => {
    const r = story.getBoundingClientRect();
    scroll = THREE.MathUtils.clamp(-r.top / (r.height - innerHeight), 0, 1);
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const clock = new THREE.Clock();
  let visible = true;
  let approvedCount = 0;
  let shown = -1;
  new IntersectionObserver(([e]) => (visible = e.isIntersecting)).observe(stage);
  const ray = new THREE.Raycaster();
  const centre = new THREE.Vector2(0, 0);

  const render = () => {
    const t = reduceMotion ? 0 : clock.getElapsedTime();
    const camZ = 5 - scroll * (LEN - 22);
    camera.position.set(
      (hasPointer ? pointer.x * 0.5 : 0) + Math.sin(t * 0.3) * 0.25,
      -0.3 + (hasPointer ? pointer.y * 0.3 : 0) + Math.cos(t * 0.4) * 0.2,
      camZ,
    );
    camera.lookAt(camera.position.x * 0.3, camera.position.y * 0.3, camZ - 10);
    camera.rotateZ(scroll * 0.35 + Math.sin(t * 0.2) * 0.04);

    ray.setFromCamera(hasPointer ? pointer : centre, camera);
    uniforms.uRayO.value.copy(ray.ray.origin);
    uniforms.uRayD.value.copy(ray.ray.direction);
    uniforms.uTime.value = t;
    uniforms.uRadius.value = hasPointer ? 1.5 : 0;

    // Remember approvals: tiles the cursor ray actually touched stay teal.
    if (hasPointer && !reduceMotion) {
      const o = ray.ray.origin;
      const d = ray.ray.direction;
      const r2 = 0.81;
      let changed = false;
      for (let i = 0; i < N; i++) {
        if (approvedAttr[i] > 0) continue;
        const cz = centers[i * 3 + 2];
        if (cz > o.z || cz < o.z - 40) continue;
        const cx = centers[i * 3] - o.x;
        const cy = centers[i * 3 + 1] - o.y;
        const czz = cz - o.z;
        const tp = cx * d.x + cy * d.y + czz * d.z;
        if (tp < 0) continue;
        const px = cx - d.x * tp;
        const py = cy - d.y * tp;
        const pz = czz - d.z * tp;
        if (px * px + py * py + pz * pz < r2) {
          approvedAttr[i] = 1;
          approvedCount++;
          changed = true;
        }
      }
      if (changed) approvedBuf.needsUpdate = true;
    }
    if (shown !== approvedCount) {
      shown = approvedCount;
      counterEl.textContent = shown.toLocaleString();
    }
    renderer.render(scene, camera);
  };

  if (reduceMotion) {
    render();
    addEventListener('scroll', render, { passive: true });
    return;
  }
  const frame = () => {
    requestAnimationFrame(frame);
    if (visible) render();
  };
  frame();
}

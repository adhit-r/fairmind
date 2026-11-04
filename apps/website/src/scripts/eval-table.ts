// The evaluation table: every catalogue evaluation as one cell. The cursor works as a lens,
// like the hero tunnel; hover or focus reads a cell, click pins it, filters dim what does not apply.

interface Item {
  id: string;
  code: string;
  name: string;
  measures: string;
  metric: string;
  threshold: string;
  thresholdSource: string;
  appliesTo: string;
  pillar: string;
  engine: 'exists' | 'partial' | 'none';
  tests: string[];
}

const group: Record<string, string> = { SECURE: 'Security', EVALUATE: 'Behaviour and fairness', GOVERN: 'Governance', COMPLY: 'Compliance' };

export function mountEvalTable(root: HTMLElement, data: { items: Item[]; featured: number; engineLabel: Record<string, string> }) {
  const cells = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-et-cell]'));
  const grid = root.querySelector<HTMLElement>('[data-et-grid]')!;
  const detail = root.querySelector<HTMLElement>('[data-et-detail]')!;
  const field = (k: string) => detail.querySelector<HTMLElement>(`[data-et="${k}"]`)!;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let pinned = data.featured;

  function show(i: number) {
    const e = data.items[i];
    detail.classList.remove('is-swap');
    void detail.offsetWidth;
    detail.classList.add('is-swap');
    field('code').textContent = `${e.id} · ${group[e.pillar] ?? e.pillar}`;
    field('name').textContent = e.name;
    field('measures').textContent = e.measures;
    field('threshold').textContent = e.threshold.replace(/>=/g, '≥').replace(/<=/g, '≤');
    field('source').textContent = `Threshold source: ${e.thresholdSource}`;
    field('metric').textContent = e.metric;
    field('applies').textContent = e.appliesTo;
    field('engine').textContent = data.engineLabel[e.engine];
    field('engine').dataset.engine = e.engine;
    const tests = field('tests');
    tests.replaceChildren(...e.tests.map((t) => Object.assign(document.createElement('li'), { textContent: t })));
  }

  cells.forEach((c) => {
    const i = Number(c.dataset.etCell);
    c.addEventListener('pointerenter', () => show(i));
    c.addEventListener('focus', () => show(i));
    c.addEventListener('click', () => {
      pinned = i;
      cells.forEach((o) => o.setAttribute('aria-pressed', String(o === c)));
      show(i);
    });
  });
  grid.addEventListener('pointerleave', () => show(pinned));

  // Filters.
  const filters = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-et-filter]'));
  filters.forEach((f) =>
    f.addEventListener('click', () => {
      filters.forEach((o) => o.setAttribute('aria-pressed', String(o === f)));
      const re = new RegExp(f.dataset.match ?? '.', 'i');
      cells.forEach((c) => {
        const applies = c.dataset.applies ?? '';
        const on = f.dataset.etFilter === 'all' || re.test(applies) || /^any$/i.test(applies);
        c.classList.toggle('is-out', !on);
        c.tabIndex = on ? 0 : -1;
      });
    }),
  );

  // Lens: cells near the cursor swell a little, as in the hero.
  if (!reduce && matchMedia('(pointer: fine)').matches) {
    let centers: { x: number; y: number }[] = [];
    let raf = 0;
    let px = -1e4;
    let py = -1e4;
    const measure = () => {
      centers = cells.map((c) => {
        const r = c.getBoundingClientRect();
        return { x: r.left + r.width / 2 + scrollX, y: r.top + r.height / 2 + scrollY };
      });
    };
    const paint = () => {
      raf = 0;
      cells.forEach((c, k) => {
        const d = Math.hypot(centers[k].x - px, centers[k].y - py);
        const p = Math.max(0, 1 - d / 150);
        c.style.setProperty('--p', p.toFixed(3));
      });
    };
    grid.addEventListener('pointerenter', measure);
    addEventListener('resize', measure);
    grid.addEventListener('pointermove', (e) => {
      px = e.pageX;
      py = e.pageY;
      if (!raf) raf = requestAnimationFrame(paint);
    });
    grid.addEventListener('pointerleave', () => {
      px = py = -1e4;
      if (!raf) raf = requestAnimationFrame(paint);
    });
  }

  // Cells fill in once, in reading order, when the table scrolls into view.
  new IntersectionObserver(
    ([e], obs) => {
      if (!e.isIntersecting) return;
      root.dataset.in = '';
      obs.disconnect();
    },
    { threshold: 0.2 },
  ).observe(grid);

  show(pinned);
}

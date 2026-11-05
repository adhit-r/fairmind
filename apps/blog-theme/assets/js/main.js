(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reveal = (el, text) => { el.textContent = text; el.closest('[hidden]')?.removeAttribute('hidden'); };
  const day = 864e5;
  const today = new Date(); today.setHours(0, 0, 0, 0);

  // Sources = items in the list under a post's "Sources" heading.
  const sourcesList = root => {
    const h = $$('h2', root).find(h => /^sources$/i.test(h.textContent.trim()));
    let el = h?.nextElementSibling;
    while (el && !/^(UL|OL)$/.test(el.tagName)) el = el.nextElementSibling;
    return el ? { h, list: el } : null;
  };

  $$('.row, .lead').forEach(row => {
    const t = $('template', row);
    const s = t && sourcesList(t.content);
    if (s) reveal($('[data-sources]', row), s.list.children.length);
  });

  const prose = $('.prose[data-post]');
  if (prose) {
    const s = sourcesList(prose);
    if (s) {
      s.h.classList.add('sources-h');
      s.list.classList.add('sources-list');
      $$('[data-sources]').forEach(el => reveal(el, s.list.children.length));
    }
  }

  // "New" label for guides published in the last 14 days.
  $$('[data-new]').forEach(el => {
    const d = new Date(el.dataset.new + 'T00:00:00');
    if (today - d <= 14 * day) el.hidden = false;
  });

  // Deadlines come from the "docket" page: list items written as
  // "<strong>13 Nov 2026</strong> Title: note".
  const src = $('#docket-src');
  if (src) {
    const months = 'jan feb mar apr may jun jul aug sep oct nov dec'.split(' ');
    const items = $$('li', src.content).map(li => {
      const when = $('strong', li)?.textContent.trim() || '';
      const m = when.match(/^(\d{1,2})\s+([a-z]{3})[a-z]*\s+(\d{4})$/i);
      if (!m) return null;
      const date = new Date(+m[3], months.indexOf(m[2].toLowerCase()), +m[1]);
      const rest = li.textContent.trim().slice(when.length).trim();
      const i = rest.indexOf(': ');
      return { date, when, title: i < 0 ? rest : rest.slice(0, i), note: i < 0 ? '' : rest.slice(i + 2) };
    }).filter(x => x && x.date >= today).sort((a, b) => a.date - b.date);

    $$('[data-due]').forEach(mod => {
      const list = items.slice(0, +mod.dataset.due || 5);
      if (!list.length) return;
      const ol = $('ol', mod);
      list.forEach(x => {
        const n = Math.round((x.date - today) / day);
        const li = document.createElement('li');
        if (n <= 30) li.className = 'soon';
        li.innerHTML = '<div class="days"></div><div><b></b><span></span></div>';
        li.querySelector('.days').innerHTML = `${n}<small>${n === 1 ? 'day' : 'days'}</small>`;
        li.querySelector('b').textContent = x.title;
        const span = li.querySelector('span');
        const time = document.createElement('time');
        time.dateTime = x.date.toISOString().slice(0, 10);
        time.textContent = x.when;
        span.append(time, x.note ? ` · ${x.note}` : '');
        ol.append(li);
      });
      mod.hidden = false;
    });

    // Next date per framework: the docket title names the framework, or its acronym (DPDP, OWASP).
    $$('[data-topic]').forEach(a => {
      const name = a.dataset.topic;
      const keys = [name, ...name.split(/\s+/).filter(w => /^[A-Z]{4,}$/.test(w))];
      const hit = items.find(x => keys.some(k => x.title.includes(k)));
      const el = $('.next', a);
      if (hit && el) { el.textContent = hit.when.replace(/\s\d{4}$/, ''); el.hidden = false; el.title = `${hit.title}, ${hit.when}`; }
    });

    const soon = items.filter(x => x.date - today <= 30 * day).length;
    const badge = $('[data-due-badge]');
    if (badge && soon) { badge.textContent = soon; badge.hidden = false; badge.closest('a')?.setAttribute('aria-label', `Deadlines, ${soon} in the next 30 days`); }
  }

  // Contents from the guide's h2s.
  const toc = $('.toc');
  const tocM = $('.toc-m');
  tocM?.addEventListener('click', e => { if (e.target.closest('a')) tocM.open = false; });
  const heads = prose ? $$('h2', prose) : [];
  heads.forEach((h, i) => { if (!h.id) h.id = 'section-' + (i + 1); });
  if (heads.length > 1) {
    [toc, $('.toc-m')].filter(Boolean).forEach(box => {
      const ol = document.createElement('ol');
      heads.forEach(h => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = '#' + h.id;
        a.textContent = h.textContent;
        li.append(a);
        ol.append(li);
      });
      box.append(ol);
      box.hidden = false;
    });
  }
  const links = toc ? $$('a', toc) : [];
  const progress = $('.progress');

  const tick = () => {
    if (progress) {
      const d = document.documentElement;
      progress.style.width = Math.min(100, d.scrollTop / Math.max(1, d.scrollHeight - innerHeight) * 100) + '%';
    }
    if (links.length) {
      let cur = heads[0];
      heads.forEach(h => { if (h.getBoundingClientRect().top < innerHeight * 0.25) cur = h; });
      links.forEach(a => a.classList.toggle('cur', a.hash === '#' + cur.id));
    }
  };
  addEventListener('scroll', tick, { passive: true });
  tick();
})();

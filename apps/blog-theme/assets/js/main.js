(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const day = 864e5;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const months = 'jan feb mar apr may jun jul aug sep oct nov dec'.split(' ');

  // Docket items are list entries written as "<strong>13 Nov 2026</strong> Title: note".
  const parse = li => {
    const when = $('strong', li)?.textContent.trim() || '';
    const m = when.match(/^(\d{1,2})\s+([a-z]{3})[a-z]*\s+(\d{4})$/i);
    const month = m ? months.indexOf(m[2].toLowerCase()) : -1;
    if (month < 0) return null;
    const date = new Date(+m[3], month, +m[1]);
    const rest = li.textContent.trim().slice(when.length).trim();
    const i = rest.indexOf(': ');
    return { date, when, days: Math.round((date - today) / day), title: i < 0 ? rest : rest.slice(0, i) };
  };
  const daysText = n => (n === 0 ? 'today' : n === 1 ? 'in 1 day' : `in ${n} days`);
  const src = $('#docket-src');
  const items = src ? $$('li', src.content).map(parse).filter(x => x && x.days >= 0).sort((a, b) => a.date - b.date) : [];
  const docketUrl = `${location.origin}/docket/`;

  const line = (el, label, x) => {
    el.textContent = '';
    const days = document.createElement('span');
    days.className = 'days' + (x.days <= 30 ? ' soon' : '');
    days.textContent = daysText(x.days);
    const title = document.createElement('strong');
    title.textContent = x.title;
    const link = document.createElement('a');
    link.href = docketUrl;
    link.textContent = 'All deadlines';
    el.append(`${label} `, title, `, ${x.when}, `, days, '. ', link);
    el.hidden = false;
  };

  const next = $('[data-next-due]');
  if (next && items[0]) line(next, 'Next deadline:', items[0]);

  // A framework's next date: the docket title names it, or its acronym (DPDP, OWASP).
  const forTopic = name => {
    const keys = [name, ...name.split(/\s+/).filter(w => /^[A-Z]{4,}$/.test(w))];
    return items.find(x => keys.some(k => x.title.includes(k)));
  };
  $$('[data-topic-due]').forEach(el => {
    const hit = forTopic(el.dataset.topicDue);
    if (hit) line(el, `Next date for ${el.dataset.topicDue}:`, hit);
  });
  $$('[data-topic-next]').forEach(el => {
    const hit = forTopic(el.dataset.topicNext);
    if (!hit) return;
    el.textContent = `Next date ${hit.when}`;
    if (hit.days <= 30) el.classList.add('soon');
    el.hidden = false;
  });

  // Deadlines page: keep the authored list and add days left to each entry.
  $$('.docket-page .prose li').forEach(li => {
    const x = parse(li);
    if (!x) return;
    const span = document.createElement('span');
    span.className = 'days' + (x.days >= 0 && x.days <= 30 ? ' soon' : '');
    span.textContent = x.days < 0 ? 'passed' : daysText(x.days);
    if (x.days < 0) li.classList.add('past');
    li.append(span);
  });

  // Guide page: sources count, contents, progress, citation.
  const prose = $('.prose[data-post]');
  if (!prose) return;

  const heads = $$('h2', prose);
  const sourcesHead = heads.find(h => /^(primary\s+)?sources$/i.test(h.textContent.trim()));
  let list = sourcesHead?.nextElementSibling;
  while (list && !/^(UL|OL|H2|H3)$/.test(list.tagName)) list = list.nextElementSibling;
  if (list && /^(UL|OL)$/.test(list.tagName)) {
    sourcesHead.classList.add('sources-h');
    list.classList.add('sources-list');
    $$('[data-sources]').forEach(el => { el.textContent = list.children.length; el.closest('[hidden]')?.removeAttribute('hidden'); });
  }

  heads.forEach((h, i) => { if (!h.id) h.id = 'section-' + (i + 1); });
  const boxes = [$('.toc'), $('.toc-m')].filter(Boolean);
  if (heads.length > 1) {
    boxes.forEach(box => {
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
    const tocM = $('.toc-m');
    tocM?.addEventListener('click', e => { if (e.target.closest('a')) tocM.open = false; });

    const links = $$('.toc a');
    const io = new IntersectionObserver(() => {
      const cur = [...heads].reverse().find(h => h.getBoundingClientRect().top < innerHeight * 0.3) || heads[0];
      links.forEach(a => a.classList.toggle('cur', a.hash === '#' + cur.id));
    }, { rootMargin: '0px 0px -70% 0px' });
    heads.forEach(h => io.observe(h));
  }

  const bar = $('.progress i');
  if (bar) {
    let queued = false;
    const draw = () => {
      queued = false;
      const d = document.documentElement;
      bar.style.transform = `scaleX(${Math.min(1, d.scrollTop / Math.max(1, d.scrollHeight - innerHeight))})`;
    };
    addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(draw); } }, { passive: true });
    draw();
  }

  const copy = $('[data-copy]');
  if (copy && navigator.clipboard) {
    const status = $('.copied');
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText($('[data-cite]').textContent.trim());
        status.textContent = 'Citation copied.';
      } catch {
        status.textContent = 'Copy failed. Select the text above instead.';
      }
    });
  } else if (copy) {
    copy.hidden = true;
  }
})();

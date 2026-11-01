/* FairMind mockups v1: shared rail and the Interlock figure. */
(function () {
  var q = new URLSearchParams(location.search).get('theme');
  if (q) document.documentElement.dataset.theme = q;

  var ICON = {
    today: '<path d="M4 11l8-6 8 6v8H4z"/><path d="M10 19v-5h4v5"/>',
    needs: '<path d="M4 13l2-7h12l2 7v5H4z"/><path d="M4 13h5l1 2h4l1-2h5"/>',
    systems: '<rect x="4" y="4" width="16" height="6"/><rect x="4" y="14" width="16" height="6"/><path d="M7 7h2M7 17h2"/>',
    tests: '<path d="M9 4h6M10 4v6l-5 9h14l-5-9V4"/><path d="M7.5 15h9"/>',
    frameworks: '<path d="M5 5h6v14H5zM13 5h6v14h-6z"/><path d="M7 9h2M15 9h2"/>',
    evidence: '<circle cx="12" cy="12" r="8"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    watch: '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
    settings: '<path d="M5 7h14M5 12h14M5 17h14"/><circle cx="9" cy="7" r="1.6"/><circle cx="15" cy="12" r="1.6"/><circle cx="8" cy="17" r="1.6"/>'
  };
  var NAV = [['today', 'Today', 'today.html'], ['needs', 'Needs you', 'needs-you.html', 4], ['systems', 'Systems', 'systems.html'],
    ['tests', 'Tests', '#'], ['frameworks', 'Frameworks', '#'], ['evidence', 'Evidence', '#'], ['watch', 'Watch', '#']];

  var rail = document.querySelector('.rail');
  if (rail) {
    var page = document.body.dataset.page, ic = function (k) { return '<svg class="i" viewBox="0 0 24 24" aria-hidden="true">' + ICON[k] + '</svg>'; };
    rail.innerHTML =
      '<a class="word" href="index.html" aria-label="FairMind home"><svg viewBox="0 0 30 30" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4" y="6" width="22" height="4"/><path d="M9 10v13M15 10v13M21 10v13M5 24h20"/><rect x="13" y="15" width="4" height="4" fill="var(--cobalt)" stroke="none"/></svg>FairMind</a>' +
      NAV.map(function (n) {
        return '<a href="' + n[2] + '"' + (n[0] === page ? ' aria-current="page"' : '') + '>' + ic(n[0]) + n[1] + (n[3] ? '<span class="n">' + n[3] + '</span>' : '') + '</a>';
      }).join('') +
      '<div class="foot"><a href="#">' + ic('settings') + 'Settings</a><button class="theme" type="button">Dark</button><span class="who" aria-label="Signed in as Meera">M</span></div>';
    var btn = rail.querySelector('.theme'), root = document.documentElement;
    var isDark = function () { return root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; };
    var label = function () { btn.textContent = isDark() ? 'Light' : 'Dark'; };
    btn.onclick = function () { root.dataset.theme = isDark() ? 'light' : 'dark'; label(); };
    label();
  }
  var tag = document.createElement('div');
  tag.className = 'mock-label';
  tag.textContent = 'Mockup - illustrative data';
  document.body.appendChild(tag);

  /* Interlock bench, true isometric. Each lane is one release gate: nine pins under a gate bar.
     Pin state: ok = seated on measured evidence (green cap), need = waiting for a person (cobalt lamp,
     numbered), att = attested only (half seated, steel), hold = held (violet), open = no evidence (down).
     The bar lifts only when every pin is seated. Painter's order: plate, then lanes back to front,
     within a lane posts and pins by x, then the bar, then number plates. */
  window.interlock = function (svg, lanes, o) {
    o = o || {};
    var S = 0.866, out = [], b = [1e9, 1e9, -1e9, -1e9];
    var P = function (x, y, z) { var a = (x - y) * S, c = (x + y) / 2 - z; b[0] = Math.min(b[0], a); b[1] = Math.min(b[1], c); b[2] = Math.max(b[2], a); b[3] = Math.max(b[3], c); return [a, c]; };
    var f = function (n) { return n.toFixed(1); };
    var poly = function (pts, cls) { out.push('<polygon class="' + cls + '" points="' + pts.map(function (p) { return P(p[0], p[1], p[2]).map(f).join(','); }).join(' ') + '"/>'); };
    var box = function (x, y, z, w, d, h, m) {
      m = m || ''; var X = x + w, Y = y + d, Z = z + h;
      poly([[x, Y, z], [X, Y, z], [X, Y, Z], [x, Y, Z]], 'fl ' + m);
      poly([[X, y, z], [X, Y, z], [X, Y, Z], [X, y, Z]], 'fr ' + m);
      poly([[x, y, Z], [X, y, Z], [X, Y, Z], [x, Y, Z]], 'ft ' + m);
    };
    var text = function (x, y, z, s, cls, mid, face) {
      var p = P(x, y, z), m = face ? [S, .5, 0, 1] : [S, .5, -S, .5];
      out.push('<text class="' + cls + '"' + (mid ? ' text-anchor="middle"' : '') + ' transform="matrix(' + m.join(',') + ',' + f(p[0]) + ',' + f(p[1]) + ')">' + s + '</text>');
    };
    var line = function (a, c) { var p = P(a[0], a[1], a[2]), q = P(c[0], c[1], c[2]); out.push('<line class="groove" x1="' + f(p[0]) + '" y1="' + f(p[1]) + '" x2="' + f(q[0]) + '" y2="' + f(q[1]) + '"/>'); };

    var LD = o.laneDepth || 110, W = 548, D = lanes.length * LD + 14, labels = o.labels !== false, plates = [];
    box(0, 0, -6, W, D, 6, 'foot');
    box(6, 6, 0, W - 12, D - 12, 10, 'plate');
    [[16, 14], [W - 16, 14], [16, D - 14], [W - 16, D - 14]].forEach(function (s) {
      var p = P(s[0], s[1], 10); out.push('<ellipse class="screw" cx="' + f(p[0]) + '" cy="' + f(p[1]) + '" rx="3.4" ry="2"/>');
    });
    for (var t = 60; t < W - 40; t += 26) line([t, D - 9, 10], [t, D - (t % 52 ? 13 : 16), 10]); // ruler ticks on the front edge

    lanes.forEach(function (g, li) {
      // Seated pins pass through the bar and show their cap on top of it; the bar sits on the posts,
      // and floats clear of them when the gate has lifted.
      var y = li * LD + 24, top = g.go ? 80 : 62, post = 52, seated = [];
      if (li) line([20, y - 14, 10], [W - 20, y - 14, 10]);
      if (g.pins.length) {
        box(14, y, 10, 22, 26, post);
        g.pins.forEach(function (p, i) {
          var x = 54 + i * 51, st = p[1];
          var rod = st === 'ok' ? top + 10 - 24 : st === 'open' ? 3 : 16;
          var cap = st === 'ok' ? 'm-ok' : st === 'need' ? 'm-co' : st === 'hold' ? 'm-hold' : '';
          box(x, y, 10, 26, 26, 14);
          box(x + 10, y + 10, 24, 6, 6, rod);
          if (st === 'ok') seated.push(x); else box(x + 6, y + 6, 24 + rod, 14, 14, 6, cap);
          if (labels) text(x + 13, y + 40, 10, p[0], 'eng', 1);
          if (p[2]) plates.push([x + 20, y + 6, 30 + rod, p[2]]);
        });
        box(W - 36, y, 10, 22, 26, post);
        if (g.go) { box(18, y + 6, 62, 14, 14, top - 62); box(W - 32, y + 6, 62, 14, 14, top - 62); }
        box(10, y + 5, top, W - 44, 16, 10);
        text(30, y + 21, top + 2.5, 'RELEASE', 'eng', 0, 1);
        seated.forEach(function (x) { box(x + 6, y + 6, top + 10, 14, 14, 6, 'm-ok'); });
      }
      text(18, y + (labels ? 62 : 42), 10, g.name.toUpperCase(), 'eng big');
    });
    plates.forEach(function (p) {
      var a = P(p[0], p[1], p[2]);
      out.push('<rect class="numplate" x="' + f(a[0] + 3) + '" y="' + f(a[1] - 15) + '" width="14" height="14"/><text class="numplate-t" x="' + f(a[0] + 10) + '" y="' + f(a[1] - 4.6) + '" text-anchor="middle">' + p[3] + '</text>');
    });
    svg.setAttribute('viewBox', [f(b[0] - 12), f(b[1] - 22), f(b[2] - b[0] + 24), f(b[3] - b[1] + 30)].join(' '));
    svg.innerHTML = out.join('');
  };

  window.PINS = ['DATA', 'DI RATIO', 'EO GAP', 'CALIB', 'EXPLAIN', 'OVERSIGHT', 'CONSENT', 'CARD', 'MONITOR'];
  window.gate = function (states, lamps) { // states: 9 chars o/n/a/h/x ; lamps: {index: number}
    var map = { o: 'ok', n: 'need', a: 'att', h: 'hold', x: 'open' };
    return states.split('').map(function (c, i) { return [window.PINS[i], map[c], lamps && lamps[i]]; });
  };
})();

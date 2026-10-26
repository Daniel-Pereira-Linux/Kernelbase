/* Notícias da KernelBase.
   Fonte manual: noticias.json (você edita). Fonte automática: news.json (feeds do Kernel).
   Uso: <div id="kb-news" data-mode="home|page"></div> */
(function () {
  'use strict';
  var root = document.getElementById('kb-news');
  if (!root) return;
  var MODE = root.getAttribute('data-mode') || 'page';
  var PAGE = 9;
  var CATS = { curso: 'Curso', lpic1: 'LPIC-1', lab: 'Laboratório', novidade: 'Novidades', comunidade: 'Comunidade', kernel: 'Kernel e Linux' };

  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt !== undefined && txt !== null) n.textContent = txt;
    return n;
  }
  function safeUrl(u) {
    if (typeof u !== 'string') return '';
    u = u.trim();
    if (/^https?:\/\//i.test(u)) return u;
    if (/^(#|[a-z0-9_\-\/]+\.html(#[\w\-]*)?|index\.html#[\w\-]*)$/i.test(u)) return u;
    return '';
  }
  function parseDate(s) {
    if (!s) return null;
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s));
    var d = m ? new Date(+m[1], +m[2] - 1, +m[3]) : new Date(s);
    return isNaN(d.getTime()) ? null : d;
  }
  function fmtDate(d) {
    if (!d) return '';
    var days = Math.floor((new Date().setHours(0, 0, 0, 0) - new Date(d).setHours(0, 0, 0, 0)) / 86400000);
    if (days === 0) return 'hoje';
    if (days === 1) return 'ontem';
    if (days > 1 && days <= 30) return 'há ' + days + ' dias';
    return d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' });
  }
  function clean(s) { return String(s || '').replace(/\s+/g, ' ').trim(); }

  function normManual(p) {
    if (!p || !p.titulo) return null;
    var cat = CATS[p.categoria] && p.categoria !== 'kernel' ? p.categoria : 'novidade';
    return {
      id: String(p.id || p.titulo).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
      titulo: clean(p.titulo), resumo: clean(p.resumo), texto: String(p.texto || ''),
      date: parseDate(p.data), cat: cat, pin: !!p.destaque, auto: false,
      link: safeUrl(p.link), linkTxt: clean(p.link_texto) || 'Saiba mais'
    };
  }
  function normAuto(p, i) {
    var t = clean(p.title_pt || p.title_en);
    if (!t) return null;
    var s = clean(p.summary_pt || p.summary_en);
    if (s.length > 220) s = s.slice(0, 217).replace(/\s+\S*$/, '') + '...';
    return {
      id: 'auto-' + i, titulo: t, resumo: s, texto: '', date: parseDate(p.date), cat: 'kernel', pin: false, auto: true,
      source: clean(p.source), link: safeUrl(p.link), linkTxt: 'Ler em ' + (clean(p.source) || 'fonte original')
    };
  }
  function load(url, norm) {
    return fetch(url, { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (a) {
      var out = [];
      (Array.isArray(a) ? a : []).forEach(function (x, i) { var n = norm(x, i); if (n) out.push(n); });
      return out;
    }).catch(function () { return []; });
  }
  function byDate(a, b) { return (b.date ? b.date.getTime() : 0) - (a.date ? a.date.getTime() : 0); }

  function card(p, opts) {
    opts = opts || {};
    var art = el('article', 'news-card t-' + p.cat + (opts.feature ? ' news-feature' : ''));
    art.id = 'p-' + p.id;
    var main = opts.feature ? el('div', 'news-main') : art;
    if (opts.feature) main.appendChild(el('span', 'news-pin', 'Em destaque'));
    var meta = el('div', 'news-meta');
    meta.appendChild(el('span', 'news-tag', CATS[p.cat]));
    if (p.date) { var tm = el('time', null, fmtDate(p.date)); tm.setAttribute('datetime', p.date.toISOString().slice(0, 10)); meta.appendChild(tm); }
    if (p.auto && p.source) meta.appendChild(el('span', null, p.source));
    main.appendChild(meta);
    var h = el('h3'); var href = p.auto ? p.link : (MODE === 'home' ? 'noticias.html#p-' + p.id : '');
    if (href) { var a = el('a', null, p.titulo); a.href = href; if (/^https?:/i.test(href)) { a.target = '_blank'; a.rel = 'noopener'; } h.appendChild(a); } else { h.textContent = p.titulo; }
    main.appendChild(h);
    if (p.resumo) main.appendChild(el('p', null, p.resumo));
    var body = null;
    if (p.texto && MODE === 'page') {
      body = el('div', 'news-body');
      p.texto.split(/\n\s*\n/).forEach(function (par) { if (par.trim()) body.appendChild(el('p', null, par.trim())); });
      main.appendChild(body);
    }
    var act = el('div', 'news-actions');
    if (body) {
      var more = el('button', 'news-more', 'Ler mais'); more.type = 'button'; more.setAttribute('aria-expanded', 'false');
      more.addEventListener('click', function () { toggle(art, more); });
      act.appendChild(more);
    }
    if (p.link && (p.auto || MODE === 'page')) {
      var l = el('a', 'news-link', p.linkTxt); l.href = p.link;
      if (/^https?:/i.test(p.link)) { l.target = '_blank'; l.rel = 'noopener'; }
      act.appendChild(l);
    }
    if (act.childNodes.length) main.appendChild(act);
    if (opts.feature) art.appendChild(main);
    return art;
  }
  function toggle(art, btn, force) {
    var open = force === undefined ? !art.classList.contains('open') : force;
    art.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.textContent = open ? 'Mostrar menos' : 'Ler mais';
  }

  function skeleton(n) {
    var g = el('div', 'news-grid'); g.setAttribute('aria-hidden', 'true');
    for (var i = 0; i < n; i++) g.appendChild(el('div', 'news-skel'));
    return g;
  }

  Promise.resolve().then(function () { root.appendChild(skeleton(MODE === 'home' ? 3 : 6)); });

  Promise.all([load('noticias.json', normManual), root.getAttribute('data-kernel') === '1' ? load('news.json', normAuto) : Promise.resolve([])]).then(function (r) {
    var manual = r[0].sort(byDate), auto = r[1].sort(byDate);
    while (root.firstChild) root.removeChild(root.firstChild);
    if (MODE === 'home') return home(manual, auto);
    return page(manual, auto);
  });

  function home(manual, auto) {
    var list = manual.slice().sort(function (a, b) { return (b.pin ? 1 : 0) - (a.pin ? 1 : 0) || byDate(a, b); }).slice(0, 3);
    if (list.length < 3) list = list.concat(auto.slice(0, 3 - list.length));
    var sec = root.closest('section');
    if (!list.length) { if (sec) sec.hidden = true; return; }
    var g = el('div', 'news-grid');
    list.forEach(function (p) { g.appendChild(card(p)); });
    root.appendChild(g);
    var f = el('div', 'news-foot'); var a = el('a', 'btn btn-ghost', 'Ver todas as notícias'); a.href = 'noticias.html'; f.appendChild(a); root.appendChild(f);
  }

  function page(manual, auto) {
    var all = manual.concat(auto).sort(byDate);
    if (!all.length) {
      var e = el('p', 'news-empty', 'Ainda não há notícias por aqui. Volte em breve.');
      root.appendChild(e); return;
    }
    var state = { cat: 'todas', q: '', shown: PAGE };
    var counts = { todas: all.length };
    all.forEach(function (p) { counts[p.cat] = (counts[p.cat] || 0) + 1; });

    var tools = el('div', 'news-tools');
    var search = el('input', 'news-search'); search.type = 'search'; search.placeholder = 'Buscar notícias'; search.setAttribute('aria-label', 'Buscar notícias');
    tools.appendChild(search);
    var chips = el('div', 'news-chips'); chips.setAttribute('role', 'group'); chips.setAttribute('aria-label', 'Filtrar por categoria');
    var order = ['todas', 'curso', 'lpic1', 'lab', 'novidade', 'comunidade', 'kernel'];
    var btns = {};
    order.forEach(function (c) {
      if (c !== 'todas' && !counts[c]) return;
      var b = el('button', 'chip', c === 'todas' ? 'Todas' : CATS[c]); b.type = 'button';
      b.appendChild(el('small', null, String(counts[c] || 0)));
      b.setAttribute('aria-pressed', c === 'todas' ? 'true' : 'false');
      b.addEventListener('click', function () { state.cat = c; state.shown = PAGE; sync(); draw(); });
      chips.appendChild(b); btns[c] = b;
    });
    tools.appendChild(chips);
    root.appendChild(tools);
    var count = el('p', 'news-count'); count.setAttribute('aria-live', 'polite'); root.appendChild(count);
    var host = el('div'); root.appendChild(host);
    function sync() { Object.keys(btns).forEach(function (c) { btns[c].setAttribute('aria-pressed', c === state.cat ? 'true' : 'false'); }); }

    var timer;
    search.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(function () { state.q = search.value; state.shown = PAGE; draw(); }, 150); });

    function draw() {
      var q = state.q.trim().toLowerCase();
      var rows = all.filter(function (p) {
        if (state.cat !== 'todas' && p.cat !== state.cat) return false;
        return !q || (p.titulo + ' ' + p.resumo + ' ' + p.texto).toLowerCase().indexOf(q) !== -1;
      });
      while (host.firstChild) host.removeChild(host.firstChild);
      count.textContent = rows.length + (rows.length === 1 ? ' notícia' : ' notícias');
      var g = el('div', 'news-grid'); host.appendChild(g);
      if (!rows.length) { g.appendChild(el('p', 'news-empty', 'Nenhuma notícia encontrada. Tente outra busca ou categoria.')); return; }
      var rest = rows;
      if (state.cat === 'todas' && !q) {
        var pin = rows.filter(function (p) { return p.pin; })[0];
        if (pin) { g.appendChild(card(pin, { feature: true })); rest = rows.filter(function (p) { return p !== pin; }); }
      }
      rest.slice(0, state.shown).forEach(function (p) { g.appendChild(card(p)); });
      if (rest.length > state.shown) {
        var f = el('div', 'news-foot'); var m = el('button', 'btn btn-ghost', 'Mostrar mais'); m.type = 'button';
        m.addEventListener('click', function () { state.shown += PAGE; draw(); });
        f.appendChild(m); host.appendChild(f);
      }
      openFromHash();
    }
    function openFromHash() {
      var id = location.hash.replace(/^#/, '');
      if (!/^p-/.test(id)) return;
      var t = document.getElementById(id);
      if (!t) return;
      var b = t.querySelector('.news-more');
      if (b) toggle(t, b, true);
      t.classList.add('is-target');
    }
    window.addEventListener('hashchange', function () { draw(); var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView({ block: 'center' }); });
    draw();
    var first = document.getElementById(location.hash.slice(1));
    if (first && /^p-/.test(location.hash.slice(1))) first.scrollIntoView({ block: 'center' });
  }
})();

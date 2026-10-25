/* KernelBase — interatividade do site (tabs, tema, som, dados) */
(() => {
	'use strict';

	/* ---------------- tema ---------------- */
	const THEMES = [
		{ id: 'dark', label: 'Kernel Dark', swatch: '#f5c445' },
		{ id: 'nord', label: 'Nord', swatch: '#88c0d0' },
		{ id: 'gruvbox', label: 'Gruvbox', swatch: '#fabd2f' },
		{ id: 'light', label: 'Claro', swatch: '#b8860b' },
	];

	function applyTheme(id) {
		if (id === 'dark') {
			document.documentElement.removeAttribute('data-theme');
		} else {
			document.documentElement.setAttribute('data-theme', id);
		}
		try { localStorage.setItem('kb-theme', id); } catch (e) {}
		document.dispatchEvent(new CustomEvent('kb:theme-changed'));
	}

	function initTheme() {
		let saved = 'dark';
		try { saved = localStorage.getItem('kb-theme') || 'dark'; } catch (e) {}
		applyTheme(saved);

		const dropdown = document.getElementById('theme-dropdown');
		THEMES.forEach(t => {
			const btn = document.createElement('button');
			btn.innerHTML = `<span class="theme-swatch" style="background:${t.swatch}"></span>${t.label}`;
			btn.onclick = () => { applyTheme(t.id); dropdown.classList.remove('open'); playBlip(); };
			dropdown.appendChild(btn);
		});

		document.getElementById('theme-toggle-btn').onclick = (e) => {
			e.stopPropagation();
			dropdown.classList.toggle('open');
		};
		document.addEventListener('click', () => dropdown.classList.remove('open'));
	}

	/* ---------------- som (opcional, via Web Audio, sem arquivos externos) ---------------- */
	let audioCtx = null;
	let soundOn = false;

	function ensureCtx() {
		if (!audioCtx) {
			const AC = window.AudioContext || window.webkitAudioContext;
			if (AC) audioCtx = new AC();
		}
		return audioCtx;
	}

	function tone(freq, start, dur, gainPeak = 0.05, type = 'sine') {
		const ctx = ensureCtx();
		if (!ctx) return;
		const osc = ctx.createOscillator();
		const gain = ctx.createGain();
		osc.type = type;
		osc.frequency.value = freq;
		gain.gain.setValueAtTime(0, ctx.currentTime + start);
		gain.gain.linearRampToValueAtTime(gainPeak, ctx.currentTime + start + 0.015);
		gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + start + dur);
		osc.connect(gain).connect(ctx.destination);
		osc.start(ctx.currentTime + start);
		osc.stop(ctx.currentTime + start + dur + 0.05);
	}

	function playBlip() {
		if (!soundOn) return;
		tone(720, 0, 0.08, 0.04, 'square');
	}

	function playChime() {
		if (!soundOn) return;
		tone(523.25, 0, 0.18, 0.05);
		tone(659.25, 0.09, 0.18, 0.045);
		tone(783.99, 0.18, 0.28, 0.05);
	}

	function initSound() {
		const btn = document.getElementById('sound-toggle-btn');
		if (!btn) return;
		try { soundOn = localStorage.getItem('kb-sound') === '1'; } catch (e) {}
		btn.classList.toggle('active', soundOn);
		btn.textContent = soundOn ? '🔊' : '🔈';
		btn.onclick = () => {
			soundOn = !soundOn;
			try { localStorage.setItem('kb-sound', soundOn ? '1' : '0'); } catch (e) {}
			btn.classList.toggle('active', soundOn);
			btn.textContent = soundOn ? '🔊' : '🔈';
			if (soundOn) playChime();
		};
	}

	/* ---------------- boot intro ---------------- */
	function initBoot() {
		const screen = document.getElementById('boot-screen');
		if (!screen) return;
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
			screen.remove();
			return;
		}
		let seen = false;
		try { seen = sessionStorage.getItem('kb-booted') === '1'; } catch (e) {}
		if (seen) { screen.remove(); return; }

		const lines = [
			'kernelbase-init: iniciando assistentes de atendimento...',
			'kernelbase-init: montando documentação em pt_BR...',
			'kernelbase-init: conectando ao lore.kernel.org...',
			'kernelbase-init: pronto.',
		];
		const out = document.getElementById('boot-lines');
		let i = 0;
		function next() {
			if (i >= lines.length) {
				setTimeout(() => {
					screen.classList.add('hidden');
					try { sessionStorage.setItem('kb-booted', '1'); } catch (e) {}
					setTimeout(() => screen.remove(), 600);
				}, 250);
				return;
			}
			const p = document.createElement('div');
			p.textContent = '$ ' + lines[i];
			out.appendChild(p);
			i++;
			setTimeout(next, 220);
		}
		next();
	}

	/* ---------------- tabs ---------------- */
	let allPatches = [];

	const TABS = ['home', 'docs', 'patches'];
	// hash da URL -> [aba, seção para rolar]
	const HASH_ROUTES = {
		'': ['docs'], inicio: ['docs'],
		docs: ['docs'], patches: ['patches'],
	};

	function showTab(tabName, scrollTo) {
		if (!TABS.includes(tabName)) tabName = 'home';
		const changed = !document.getElementById(tabName).classList.contains('active');
		document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
		document.querySelectorAll('nav.tabs a').forEach(el => el.classList.remove('active-tab'));
		document.getElementById(tabName).classList.add('active');
		document.getElementById('nav-' + tabName).classList.add('active-tab');
		if (changed) playBlip();

		const hash = scrollTo || (tabName === 'home' ? 'inicio' : tabName);
		if (location.hash.slice(1) !== hash) history.replaceState(null, '', '#' + hash);

		if (scrollTo) {
			const target = document.getElementById(scrollTo);
			if (target) requestAnimationFrame(() => target.scrollIntoView({ behavior: 'smooth', block: 'start' }));
		} else if (changed) {
			window.scrollTo({ top: 0 });
		}

		if (tabName === 'patches' && allPatches.length === 0) loadPatches();
		if (tabName === 'home') initReveal();
	}
	window.showTab = showTab;

	function routeFromHash() {
		const route = HASH_ROUTES[location.hash.slice(1)] || ['docs'];
		showTab(route[0], route[1]);
	}

	function initLinks() {
		document.addEventListener('click', (e) => {
			const a = e.target.closest('[data-tab], [data-scroll]');
			if (!a) return;
			e.preventDefault();
			if (a.dataset.interest) setInterest(a.dataset.interest);
			showTab(a.dataset.tab || 'home', a.dataset.scroll);
		});
		window.addEventListener('hashchange', routeFromHash);

		// brilho que segue o cursor nos cards de serviço
		document.querySelectorAll('.svc-card').forEach(card => {
			card.addEventListener('pointermove', (e) => {
				const r = card.getBoundingClientRect();
				card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
				card.style.setProperty('--my', (e.clientY - r.top) + 'px');
			});
		});
	}

	/* ---------------- início: conversa de demonstração ---------------- */
	function initHeroChat() {
		const box = document.getElementById('hero-chat');
		const status = document.getElementById('chat-status');
		if (!box) return;
		const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

		const SCRIPT = [
			{ from: 'user', at: '03:11', text: 'Oi! Vocês atendem sábado?' },
			{ from: 'bot', at: '03:11', text: 'Oi, Ana! 😊 Atendemos sim, sábado das 9h às 13h. Quer que eu reserve um horário pra você?' },
			{ from: 'user', at: '03:12', text: 'Quero! Tem às 10h?' },
			{ from: 'bot', at: '03:12', text: 'Tem sim. Reservei sábado às 10h no seu nome e mandei a confirmação aqui e no seu e-mail. ✅' },
			{ from: 'sys', text: '✓ agendamento criado · ✓ cliente salvo no CRM · 03:12 da manhã' },
			{ from: 'user', at: '03:13', text: 'Perfeito, obrigada!' },
			{ from: 'bot', at: '03:13', text: 'Imagina! Te mando um lembrete na sexta. Até sábado! 👋' },
		];

		function bubble(m) {
			const el = document.createElement('div');
			el.className = 'msg ' + m.from;
			el.innerHTML = m.from === 'sys'
				? escapeHtml(m.text)
				: `${escapeHtml(m.text)}<span class="msg-time">${m.at}${m.from === 'user' ? '' : ' ✓✓'}</span>`;
			box.appendChild(el);
			box.scrollTop = box.scrollHeight;
			return el;
		}

		if (reduce) { SCRIPT.forEach(bubble); return; }

		function typing() {
			const el = document.createElement('div');
			el.className = 'msg bot typing';
			el.innerHTML = '<span></span><span></span><span></span>';
			box.appendChild(el);
			box.scrollTop = box.scrollHeight;
			if (status) status.textContent = 'digitando...';
			return el;
		}

		let i = 0;
		function next() {
			if (i >= SCRIPT.length) {
				// reinicia a demonstração depois de uma pausa
				setTimeout(() => { box.innerHTML = ''; i = 0; next(); }, 7000);
				return;
			}
			const m = SCRIPT[i++];
			if (m.from === 'bot') {
				const t = typing();
				setTimeout(() => {
					t.remove();
					if (status) status.textContent = 'online';
					bubble(m);
					setTimeout(next, 1100);
				}, 900 + Math.min(m.text.length * 12, 1300));
			} else {
				bubble(m);
				if (m.from === 'user') playBlip();
				setTimeout(next, m.from === 'sys' ? 1200 : 900);
			}
		}
		setTimeout(next, 500);
	}

	/* ---------------- início: revelar ao rolar ---------------- */
	let revealObserver = null;
	function initReveal() {
		const items = document.querySelectorAll('.reveal:not(.in)');
		if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
			items.forEach(el => el.classList.add('in'));
			return;
		}
		if (!revealObserver) {
			revealObserver = new IntersectionObserver((entries) => {
				entries.forEach(en => {
					if (en.isIntersecting) { en.target.classList.add('in'); revealObserver.unobserve(en.target); }
				});
			}, { rootMargin: '0px 0px -8% 0px' });
		}
		items.forEach(el => revealObserver.observe(el));
	}

	/* ---------------- início: contato ---------------- */
	// Altere aqui os canais que recebem os contatos do site.
	const CONTACT_WHATSAPP = '5583933003583'; // DDI + DDD + número, só dígitos
	const CONTACT_EMAIL = 'danielmaraboo@gmail.com';

	function whatsappUrl(text) {
		return 'https://wa.me/' + CONTACT_WHATSAPP + (text ? '?text=' + encodeURIComponent(text) : '');
	}

	function setInterest(value) {
		const sel = document.getElementById('contact-interest');
		if (sel) sel.value = value;
	}

	function initContact() {
		const link = document.getElementById('contact-email-link');
		if (link) { link.href = 'mailto:' + CONTACT_EMAIL; link.textContent = CONTACT_EMAIL; }
		const year = document.getElementById('year');
		if (year) year.textContent = new Date().getFullYear();

		// todo link [data-wa] abre o WhatsApp com a mensagem do atributo
		document.querySelectorAll('[data-wa]').forEach(a => {
			a.href = whatsappUrl(a.dataset.wa);
			a.target = '_blank';
			a.rel = 'noopener';
		});

		const form = document.getElementById('contact-form');
		if (!form) return;
		form.addEventListener('submit', (e) => {
			e.preventDefault();
			const d = new FormData(form);
			const text = `Olá! Vim pelo site da KernelBase.\n\n*Nome:* ${d.get('nome')}\n*Interesse:* ${d.get('interesse')}\n\n${d.get('mensagem')}`;
			window.open(whatsappUrl(text), '_blank', 'noopener');
			playChime();
		});
	}

	/* ---------------- patches ---------------- */
	async function loadPatches() {
		const loading = document.getElementById('patches-loading');
		loading.style.display = 'block';
		try {
			const res = await fetch('patches.json?' + Date.now());
			if (!res.ok) throw new Error('HTTP ' + res.status);
			allPatches = await res.json();
			loading.style.display = 'none';
			renderPatches(allPatches);
		} catch (e) {
			loading.textContent = '❌ Erro ao carregar patches: ' + e.message;
		}
	}

	function renderPatches(patches) {
		const list = document.getElementById('patch-list');
		document.getElementById('patch-count').textContent = patches.length + ' patch(es) encontrados';
		list.innerHTML = '';
		patches.forEach((p) => {
			const li = document.createElement('li');
			li.className = 'patch-item';
			li.onclick = () => openPatch(p);
			let dateStr = '';
			try {
				const d = new Date(p.updated);
				dateStr = d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
			} catch (e) {}
			li.innerHTML = `
				<div class="patch-title">${escapeHtml(p.title)}</div>
				<div class="patch-meta"><span>${escapeHtml(p.author)}</span><span>${dateStr}</span></div>
			`;
			list.appendChild(li);
		});
	}

	function filterPatches() {
		const q = document.getElementById('search-input').value.toLowerCase();
		const filtered = !q ? allPatches : allPatches.filter(p =>
			(p.title || '').toLowerCase().includes(q) ||
			(p.author || '').toLowerCase().includes(q) ||
			(p.content || '').toLowerCase().includes(q)
		);
		renderPatches(filtered);
	}
	window.filterPatches = filterPatches;

	function openPatch(p) {
		document.getElementById('patch-list-wrap').style.display = 'none';
		document.getElementById('patch-viewer').style.display = 'block';
		document.getElementById('viewer-title').textContent = p.title;
		document.getElementById('viewer-lore-link').href = p.link;
		let dateStr = '';
		try { const d = new Date(p.updated); dateStr = d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR'); } catch (e) {}
		document.getElementById('viewer-meta').innerHTML =
			`<strong>Autor:</strong> ${escapeHtml(p.author)} &lt;${escapeHtml(p.email || '')}&gt; · <strong>Data:</strong> ${dateStr}`;
		document.getElementById('viewer-content').innerHTML = highlightDiff(p.content || '');
		window.scrollTo({ top: document.getElementById('patches').offsetTop - 80, behavior: 'smooth' });
	}
	window.closePatch = () => {
		document.getElementById('patch-viewer').style.display = 'none';
		document.getElementById('patch-list-wrap').style.display = '';
	};

	function highlightDiff(text) {
		return text.split('\n').map(line => {
			if (/^diff --git/.test(line) || /^---\s+a\//.test(line) || /^\+\+\+\s+b\//.test(line)) return `<span class="diff-file">${escapeHtml(line)}</span>`;
			if (/^@@/.test(line)) return `<span class="diff-hunk">${escapeHtml(line)}</span>`;
			if (/^\+/.test(line) && !/^\+\+\+/.test(line)) return `<span class="diff-add">${escapeHtml(line)}</span>`;
			if (/^-/.test(line) && !/^---/.test(line)) return `<span class="diff-del">${escapeHtml(line)}</span>`;
			return escapeHtml(line);
		}).join('\n');
	}

	function escapeHtml(str) {
		const div = document.createElement('div');
		div.textContent = str == null ? '' : String(str);
		return div.innerHTML;
	}

	/* ---------------- status do kernel / banner ---------------- */
	async function loadKernelStatus() {
		try {
			const res = await fetch('kernel-releases.json?' + Date.now());
			const data = await res.json();
			const releases = data.releases || [];
			const mainline = releases.find(r => r.moniker === 'mainline');
			const card = document.getElementById('kernel-banner');
			if (!mainline || !card) return;

			const titleEl = document.getElementById('banner-title');
			const descEl = document.getElementById('banner-desc');
			const tbody = document.getElementById('releases-tbody');
			const ver = mainline.version;
			const rcMatch = ver.match(/rc(\d+)/);

			if (rcMatch) {
				const rcNum = parseInt(rcMatch[1], 10);
				card.classList.remove('closed');
				if (rcNum === 1) {
					titleEl.innerHTML = '<span class="pulse"></span>Janela de merge fechada (' + ver + ') — ótimo momento para traduções!';
					descEl.textContent = 'O ' + ver + ' foi lançado em ' + mainline.released.isodate + '. A janela de merge fechou e o kernel entrou em estabilização — os mantenedores de documentação estão disponíveis para revisar patches.';
				} else {
					titleEl.innerHTML = '<span class="pulse"></span>Estabilização em andamento (' + ver + ') — envie seus patches!';
					descEl.textContent = 'Estamos no rc' + rcNum + '. Bom momento para enviar traduções e correções de documentação.';
				}
			} else {
				card.classList.add('closed');
				titleEl.innerHTML = '<span class="pulse"></span>Janela de merge ABERTA — kernel ' + ver + ' lançado';
				descEl.textContent = 'A versão ' + ver + ' foi lançada e a janela de merge está aberta. Os mantenedores estão ocupados com pull requests; patches de doc ainda são bem-vindos, mas a revisão pode demorar mais.';
			}

			tbody.innerHTML = '';
			releases.forEach(r => {
				const tr = document.createElement('tr');
				let links = '';
				if (r.source) links += `<a href="${r.source}" target="_blank" rel="noopener">tarball</a>`;
				if (r.pgp) links += `<a href="${r.pgp}" target="_blank" rel="noopener">pgp</a>`;
				if (r.gitweb) links += `<a href="${r.gitweb}" target="_blank" rel="noopener">browse</a>`;
				if (r.changelog) links += `<a href="${r.changelog}" target="_blank" rel="noopener">changelog</a>`;
				if (r.diffview) links += `<a href="${r.diffview}" target="_blank" rel="noopener">diff</a>`;
				const eolBadge = r.iseol ? ' <span class="eol-badge">EOL</span>' : '';
				tr.innerHTML = `<td class="moniker">${r.moniker}${eolBadge}</td><td class="version">${r.version}</td><td>${r.released.isodate}</td><td>${links}</td>`;
				tbody.appendChild(tr);
			});
		} catch (e) {
			console.error('Erro ao carregar status do kernel:', e);
		}
	}

	/* ---------------- copy-to-clipboard nos blocos de código ---------------- */
	function initCodeCopy() {
		document.querySelectorAll('.prose pre').forEach(pre => {
			if (pre.closest('.code-block')) return;
			const wrap = document.createElement('div');
			wrap.className = 'code-block';
			pre.parentNode.insertBefore(wrap, pre);
			wrap.appendChild(pre);
			const btn = document.createElement('button');
			btn.className = 'copy-btn';
			btn.type = 'button';
			btn.textContent = 'copiar';
			btn.onclick = async () => {
				try {
					await navigator.clipboard.writeText(pre.textContent);
					btn.textContent = 'copiado ✓';
					btn.classList.add('copied');
					playBlip();
					setTimeout(() => { btn.textContent = 'copiar'; btn.classList.remove('copied'); }, 1600);
				} catch (e) {
					btn.textContent = 'erro';
				}
			};
			wrap.appendChild(btn);
		});
	}

	/* ---------------- fundo de pontos interativo (efeito "onda" ao mover/clicar) ---------------- */
	function initDotGrid() {
		const canvas = document.getElementById('bg-grid');
		if (!canvas || !canvas.getContext) return;
		const ctx = canvas.getContext('2d');
		const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

		const SPACING = 26;
		const DOT_SIZE = 1.6;
		const CURSOR_RADIUS = 130;
		const RIPPLE_SPEED = 620;       // px/s
		const RIPPLE_MAX_AGE = 1400;    // ms
		const RIPPLE_BAND = 34;         // largura da "crista" da onda, em px

		let dpr = Math.min(window.devicePixelRatio || 1, 1.75);
		let w = 0, h = 0;
		let mouseX = -9999, mouseY = -9999;
		let hasMouse = false;
		let lastMoveRipple = 0;
		let ripples = [];
		let dotColor = '148,163,184';
		let glowColor = '245,196,69';
		let running = true;
		let rafId = null;

		function readColors() {
			const cs = getComputedStyle(document.documentElement);
			dotColor = hexToRgbStr(cs.getPropertyValue('--text-muted').trim()) || dotColor;
			glowColor = hexToRgbStr(cs.getPropertyValue('--accent').trim()) || glowColor;
		}

		function hexToRgbStr(hex) {
			const m = hex.replace('#', '').match(/^([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
			if (!m) return null;
			return `${parseInt(m[1], 16)},${parseInt(m[2], 16)},${parseInt(m[3], 16)}`;
		}

		function resize() {
			w = window.innerWidth;
			h = window.innerHeight;
			canvas.width = Math.floor(w * dpr);
			canvas.height = Math.floor(h * dpr);
			canvas.style.width = w + 'px';
			canvas.style.height = h + 'px';
			ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
		}

		function addRipple(x, y) {
			ripples.push({ x, y, t0: performance.now() });
			if (ripples.length > 6) ripples.shift();
		}

		function draw(now) {
			ctx.clearRect(0, 0, w, h);

			ripples = ripples.filter(r => now - r.t0 < RIPPLE_MAX_AGE);

			const cols = Math.ceil(w / SPACING) + 1;
			const rows = Math.ceil(h / SPACING) + 1;

			for (let iy = 0; iy < rows; iy++) {
				const y = iy * SPACING;
				for (let ix = 0; ix < cols; ix++) {
					const x = ix * SPACING;

					let boost = 0; // 0..1

					if (hasMouse) {
						const d = Math.hypot(x - mouseX, y - mouseY);
						if (d < CURSOR_RADIUS) boost = Math.max(boost, 1 - d / CURSOR_RADIUS);
					}

					for (let i = 0; i < ripples.length; i++) {
						const r = ripples[i];
						const age = now - r.t0;
						const radius = (age / 1000) * RIPPLE_SPEED;
						const d = Math.hypot(x - r.x, y - r.y);
						const band = Math.abs(d - radius);
						if (band < RIPPLE_BAND) {
							const fade = 1 - age / RIPPLE_MAX_AGE;
							boost = Math.max(boost, (1 - band / RIPPLE_BAND) * fade);
						}
					}

					const alpha = 0.16 + boost * 0.75;
					const size = DOT_SIZE + boost * 2.1;
					ctx.fillStyle = boost > 0.06
						? `rgba(${glowColor},${alpha.toFixed(3)})`
						: `rgba(${dotColor},${alpha.toFixed(3)})`;
					ctx.fillRect(x - size / 2, y - size / 2, size, size);
				}
			}

			if (running) rafId = requestAnimationFrame(draw);
		}

		resize();
		readColors();
		draw(performance.now());

		if (reduceMotion) return; // grade estática, sem reatividade

		rafId = requestAnimationFrame(draw);

		window.addEventListener('resize', () => { resize(); });

		window.addEventListener('pointermove', (e) => {
			mouseX = e.clientX; mouseY = e.clientY; hasMouse = true;
			const now = performance.now();
			if (now - lastMoveRipple > 260) {
				lastMoveRipple = now;
				addRipple(mouseX, mouseY);
			}
		}, { passive: true });

		window.addEventListener('pointerleave', () => { hasMouse = false; });

		window.addEventListener('pointerdown', (e) => {
			addRipple(e.clientX, e.clientY);
			playBlip();
		}, { passive: true });

		document.addEventListener('visibilitychange', () => {
			running = !document.hidden;
			if (running) rafId = requestAnimationFrame(draw);
			else if (rafId) cancelAnimationFrame(rafId);
		});

		document.addEventListener('kb:theme-changed', readColors);
	}

	/* ---------------- releases table toggle ---------------- */
	function initReleasesToggle() {
		const toggle = document.getElementById('releases-toggle');
		const table = document.getElementById('releases-table');
		if (!toggle || !table) return;
		toggle.onclick = () => {
			table.classList.toggle('open');
			toggle.textContent = table.classList.contains('open') ? '▾ ocultar todas as versões' : '▸ ver todas as versões (mainline, stable, longterm)';
		};
	}

	/* ---------------- init ---------------- */
	document.addEventListener('DOMContentLoaded', () => {
		initTheme();
		initDotGrid();
		initSound();
		initBoot();
		initCodeCopy();
		initReleasesToggle();
		loadKernelStatus();
		if (!document.getElementById('home')) return; // lab.html usa só tema/fundo/sons

		initLinks();
		initContact();
		initHeroChat();
		routeFromHash();
	});
})();

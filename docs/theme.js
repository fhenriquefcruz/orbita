/* ORBITA — Alternância visual não sensível; não modifica dados nem sessão. */
(() => {
  'use strict';
  const KEY = 'orbita_display_theme_v1';
  const THEMES = new Set(['light','night']);
  const root = document.documentElement;
  function readTheme() {
    try {
      const stored = localStorage.getItem(KEY);
      return THEMES.has(stored) ? stored : 'light';
    } catch (_) { return 'light'; }
  }
  function apply(theme) {
    const mode = THEMES.has(theme) ? theme : 'light';
    root.setAttribute('data-orbita-theme',mode);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = mode === 'night' ? '#0E1426' : '#F4F6FB';
    const toggle = document.getElementById('orbitaThemeToggle');
    if (toggle) {
      const next = mode === 'night' ? 'light' : 'night';
      toggle.setAttribute('aria-label', next === 'night' ? 'Ativar tema noturno' : 'Ativar tema claro');
      toggle.setAttribute('aria-pressed',String(mode === 'night'));
      toggle.title = next === 'night' ? 'Trocar para tema noturno' : 'Trocar para tema claro';
      const icon = toggle.querySelector('.theme-icon');
      const caption = toggle.querySelector('.theme-caption');
      if (icon) icon.textContent = mode === 'night' ? '☀' : '☾';
      if (caption) caption.textContent = mode === 'night' ? 'Claro' : 'Noite';
    }
    return mode;
  }
  apply(readTheme());
  function mount() {
    const parent = document.querySelector('.top .headtools');
    if (!parent || document.getElementById('orbitaThemeToggle')) return;
    const toggle = document.createElement('button');
    toggle.id='orbitaThemeToggle';
    toggle.type='button';
    toggle.className='orbita-theme-toggle';
    toggle.innerHTML='<span class="theme-icon" aria-hidden="true">☾</span><span class="theme-caption">Noite</span>';
    parent.insertBefore(toggle,parent.firstChild);
    toggle.addEventListener('click',() => {
      const mode = root.getAttribute('data-orbita-theme') === 'night' ? 'light' : 'night';
      apply(mode);
      try { localStorage.setItem(KEY,mode) } catch (_) { /* No persistent storage; visual choice stays during page lifecycle. */ }
    });
    apply(root.getAttribute('data-orbita-theme'));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();

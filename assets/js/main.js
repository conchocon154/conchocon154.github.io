/* Theme + language toggles, scroll reveal. No dependencies. */
(function () {
  'use strict';

  var root = document.documentElement;
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  };

  /* ---------- theme ---------- */
  var themeBtn = document.getElementById('themeBtn');
  var savedTheme = store.get('theme');
  var prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
  setTheme(savedTheme || (prefersLight ? 'light' : 'dark'));

  function setTheme(t) {
    root.setAttribute('data-theme', t);
    if (themeBtn) {
      themeBtn.textContent = t === 'dark' ? '☀' : '☾';
      themeBtn.setAttribute('aria-label', t === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    }
  }

  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      setTheme(next);
      store.set('theme', next);
    });
  }

  /* ---------- language ---------- */
  var langBtn = document.getElementById('langBtn');
  var savedLang = store.get('lang');
  var browserVi = (navigator.language || '').toLowerCase().indexOf('vi') === 0;
  setLang(savedLang || (browserVi ? 'vi' : 'en'));

  function setLang(l) {
    root.setAttribute('data-lang', l);
    root.setAttribute('lang', l);
    if (langBtn) {
      // the button shows the language you would switch TO
      langBtn.textContent = l === 'en' ? 'VI' : 'EN';
      langBtn.setAttribute('aria-label', l === 'en' ? 'Chuyển sang tiếng Việt' : 'Switch to English');
    }
  }

  if (langBtn) {
    langBtn.addEventListener('click', function () {
      var next = root.getAttribute('data-lang') === 'en' ? 'vi' : 'en';
      setLang(next);
      store.set('lang', next);
    });
  }

  /* ---------- scroll reveal ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(reveals, function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });

    Array.prototype.forEach.call(reveals, function (el, i) {
      el.style.transitionDelay = (Math.min(i % 4, 3) * 60) + 'ms';
      io.observe(el);
    });
  }

  /* ---------- footer year ---------- */
  var yr = document.getElementById('yr');
  if (yr) { yr.textContent = String(new Date().getFullYear()); }
})();

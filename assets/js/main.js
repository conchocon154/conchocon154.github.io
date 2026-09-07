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
    // which icon shows is decided in CSS off data-theme; only the label changes here
    root.setAttribute('data-theme', t);
    if (themeBtn) {
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

  /* Language is a URL now, not a runtime state: /  and  /vi/ are separate
     documents so each can declare its own <html lang> and be indexed on its
     own. The button in the bar is an ordinary link, so nothing to wire here. */

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

  /* ---------- scroll: progress rail + sticky bar state ----------
     One passive listener that only flags a frame as dirty; all reading and
     writing happens inside the rAF callback, so scrolling never waits on
     layout. */
  var bar = document.getElementById('progress');
  var topbar = document.querySelector('.topbar');
  var ticking = false;
  var wasStuck = false;

  function onFrame() {
    ticking = false;
    var doc = document.documentElement;
    var max = doc.scrollHeight - window.innerHeight;
    var y = window.scrollY || doc.scrollTop || 0;
    var p = max > 0 ? Math.min(1, Math.max(0, y / max)) : 0;

    if (bar) { bar.style.setProperty('--p', p.toFixed(4)); }

    var stuck = y > 8;
    if (topbar && stuck !== wasStuck) {
      topbar.classList.toggle('stuck', stuck);
      wasStuck = stuck;
    }
  }

  function onScroll() {
    if (!ticking) { ticking = true; requestAnimationFrame(onFrame); }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  onFrame();

  /* ---------- footer year ---------- */
  var yr = document.getElementById('yr');
  if (yr) { yr.textContent = String(new Date().getFullYear()); }
})();

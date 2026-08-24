/* Progressive enhancement. The page is fully readable and navigable without
   this file; everything here only improves keyboard and screen-reader access.

   1. Wide tables become horizontally scrollable regions. WCAG 2.1.1 requires a
      scrollable area to be reachable by keyboard, so an overflowing wrapper
      gets tabindex="0" plus a role and accessible name. A table that fits gets
      neither - an untabbable stop is noise for keyboard users.
   2. Table header cells get an explicit scope. Kramdown emits bare <th>, and
      while browsers infer column scope inside <thead>, screen readers are more
      reliable when it is stated.
   3. Section headings get a permalink so students can cite "section 5, task 3"
      with an actual URL.
*/
(function () {
  'use strict';

  function labelFor(table, index) {
    var caption = table.querySelector('caption');
    if (caption && caption.textContent.trim()) return caption.textContent.trim();

    var heading = table.closest('article');
    var prev = table.previousElementSibling;
    while (prev) {
      if (/^H[1-6]$/.test(prev.tagName)) return prev.textContent.trim() + ' table';
      prev = prev.previousElementSibling;
    }
    return 'Table ' + (index + 1);
  }

  function setupTables() {
    var tables = document.querySelectorAll('.prose table');

    Array.prototype.forEach.call(tables, function (table, i) {
      if (table.parentNode.classList.contains('table-scroll')) return;

      Array.prototype.forEach.call(
        table.querySelectorAll('thead th'),
        function (th) { if (!th.hasAttribute('scope')) th.setAttribute('scope', 'col'); }
      );

      var wrap = document.createElement('div');
      wrap.className = 'table-scroll';
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(table);

      var name = labelFor(table, i);

      var sync = function () {
        var overflows = wrap.scrollWidth > wrap.clientWidth + 1;
        if (overflows) {
          wrap.setAttribute('role', 'region');
          wrap.setAttribute('aria-label', name + ' (scrollable)');
          wrap.setAttribute('tabindex', '0');
        } else {
          wrap.removeAttribute('role');
          wrap.removeAttribute('aria-label');
          wrap.removeAttribute('tabindex');
        }
      };

      sync();
      if ('ResizeObserver' in window) new ResizeObserver(sync).observe(wrap);
      else window.addEventListener('resize', sync);
    });
  }

  // Same scroll-region treatment as tables, for diagrams that have a min-width.
  function setupDiagrams() {
    var wraps = document.querySelectorAll('.diagram-scroll');

    Array.prototype.forEach.call(wraps, function (wrap) {
      var svg = wrap.querySelector('svg');
      var name = 'Diagram';
      if (svg) {
        var t = svg.querySelector('title');
        if (t && t.textContent.trim()) name = t.textContent.trim();
      }

      var sync = function () {
        if (wrap.scrollWidth > wrap.clientWidth + 1) {
          wrap.setAttribute('role', 'region');
          wrap.setAttribute('aria-label', name + ' (scrollable)');
          wrap.setAttribute('tabindex', '0');
        } else {
          wrap.removeAttribute('role');
          wrap.removeAttribute('aria-label');
          wrap.removeAttribute('tabindex');
        }
      };

      sync();
      if ('ResizeObserver' in window) new ResizeObserver(sync).observe(wrap);
      else window.addEventListener('resize', sync);
    });
  }

  function setupHeadingAnchors() {
    var headings = document.querySelectorAll('.prose h2[id], .prose h3[id]');

    Array.prototype.forEach.call(headings, function (h) {
      if (h.classList.contains('toc__heading')) return;
      if (h.classList.contains('callout__title')) return;

      var a = document.createElement('a');
      a.className = 'heading-anchor';
      a.href = '#' + h.id;
      a.textContent = '#';
      a.setAttribute('aria-label', 'Link to this section: ' + h.textContent.trim());
      h.appendChild(a);
    });
  }

  function init() {
    setupTables();
    setupDiagrams();
    setupHeadingAnchors();
    // Only now is every table inside a real scroll container, so the no-JS
    // fallback in main.css can stand down.
    document.documentElement.classList.remove('no-js');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());

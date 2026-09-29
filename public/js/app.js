(function () {
  var body = document.body;
  var menuBtn = document.getElementById('menuBtn');
  var scrim = document.getElementById('scrim');
  function setMenu(open) {
    body.classList.toggle('menu-open', open);
    if (menuBtn) menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (scrim) scrim.hidden = !open;
  }
  if (menuBtn) menuBtn.addEventListener('click', function () { setMenu(!body.classList.contains('menu-open')); });
  if (scrim) scrim.addEventListener('click', function () { setMenu(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
  document.querySelectorAll('.nav a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });

  // capítulo activo visible en el menú
  var act = document.querySelector('.nav a.is-active');
  if (act && act.scrollIntoView) act.scrollIntoView({ block: 'center' });

  // tema claro/oscuro
  var themeBtn = document.getElementById('themeBtn');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var el = document.documentElement;
    var dark = el.dataset.theme === 'dark' || (!el.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches);
    el.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('theme', el.dataset.theme); } catch (e) {}
  });

  // barra de progreso de lectura
  var bar = document.getElementById('progressBar');
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    if (bar) bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
  }
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // preguntas tipo test: al elegir una opción se muestra su explicación
  document.querySelectorAll('.quiz').forEach(function (quiz) {
    quiz.addEventListener('change', function (e) {
      var input = e.target;
      if (!input.matches('input[type=radio]')) return;
      quiz.querySelectorAll('.opt').forEach(function (o) { o.classList.remove('is-ok', 'is-bad'); });
      quiz.querySelectorAll('.opt__fb').forEach(function (f) { f.hidden = true; });
      var label = input.closest('.opt');
      var st = input.dataset.state;
      if (st === 'ok') label.classList.add('is-ok');
      if (st === 'bad') label.classList.add('is-bad');
      var fb = label.nextElementSibling;
      if (fb && fb.classList.contains('opt__fb')) fb.hidden = false;
    });
  });
})();

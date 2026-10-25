// Review page behaviour: theme toggle, topic filter, copy caption, one video playing at a time.
(function () {
  var root = document.documentElement;

  function store(key, value) {
    try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch (e) { return null; }
  }

  // Theme: dark is the brand default; a saved choice wins.
  var toggle = document.querySelector('.theme-toggle');
  function setTheme(t) {
    root.setAttribute('data-theme', t);
    if (toggle) {
      toggle.querySelector('span').textContent = t === 'dark' ? 'Light theme' : 'Dark theme';
      toggle.setAttribute('aria-pressed', t === 'light' ? 'true' : 'false');
    }
  }
  setTheme(store('theme') === 'light' ? 'light' : 'dark');
  if (toggle) toggle.addEventListener('click', function () {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    setTheme(next);
    store('theme', next);
  });

  // Topic filter.
  var buttons = document.querySelectorAll('.filters button');
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      var tag = b.getAttribute('data-filter');
      buttons.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      document.querySelectorAll('.card[data-tag]').forEach(function (c) {
        c.hidden = tag !== 'all' && c.getAttribute('data-tag') !== tag;
      });
    });
  });

  // Copy caption.
  var toast = document.querySelector('.toast');
  function say(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(say.t);
    say.t = setTimeout(function () { toast.classList.remove('show'); }, 1600);
  }
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var text = b.getAttribute('data-copy');
      var done = function () { say('Caption copied'); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { say('Copy failed. Select the text instead.'); });
      } else {
        say('Copy failed. Select the text instead.');
      }
    });
  });

  // Only one clip plays at a time.
  var videos = document.querySelectorAll('.player video');
  videos.forEach(function (v) {
    v.addEventListener('play', function () {
      videos.forEach(function (o) { if (o !== v) o.pause(); });
    });
  });
})();

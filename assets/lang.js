/* 語言切換 —— 兩種語言都在 DOM 裡，只切顯示。
   這樣審查員直接分享網址給同事，對方看到的是自己讀得懂的語言。 */
(function () {
  var KEY = 'pibook-site-lang';
  var body = document.body;

  function pick() {
    try {
      var saved = localStorage.getItem(KEY);
      if (saved === 'zh' || saved === 'en') return saved;
    } catch (e) { /* 隱私模式下讀不到，往下用瀏覽器語言 */ }
    var nav = (navigator.language || 'en').toLowerCase();
    return nav.indexOf('zh') === 0 ? 'zh' : 'en';
  }

  function apply(lang) {
    body.setAttribute('data-lang', lang);
    document.documentElement.setAttribute('lang', lang === 'zh' ? 'zh-Hant' : 'en');
    var buttons = document.querySelectorAll('.lang-toggle button');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', String(buttons[i].dataset.lang === lang));
    }
  }

  apply(pick());

  document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.lang-toggle button') : null;
    if (!btn) return;
    var lang = btn.dataset.lang;
    apply(lang);
    try { localStorage.setItem(KEY, lang); } catch (err) { /* 不能存就算了 */ }
  });
})();

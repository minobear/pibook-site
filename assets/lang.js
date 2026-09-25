/* 語言選單。
   語言在第一次繪製之前就由 _partials/head.html 決定好了（網址的 ?lang= → 上次手動選的 →
   裝置語言 → 英文），這支只負責選單本身：開關、鍵盤操作、選了之後切換並記住。
   五種語言都在同一份 HTML 裡，切換只是換 <html data-lang>，不需要重新載入頁面 ——
   審查員把網址轉給同事時，對方看到的也會是自己裝置的語言。 */
(function (d, w) {
  var P = w.PibookLang;
  var button = d.getElementById('lang-button');
  var menu = d.getElementById('lang-menu');
  if (!P || !button || !menu) return;

  var items = Array.prototype.slice.call(menu.querySelectorAll('[data-set-lang]'));
  var LABEL = {
    'zh-Hant': '切換語言（目前：繁體中文）',
    'zh-Hans': '切换语言（当前：简体中文）',
    'en': 'Change language (current: English)',
    'ja': '言語を切り替える（現在：日本語）',
    'ko': '언어 변경 (현재: 한국어)'
  };

  // 舊版只有繁中／英文兩個選項時存下的選擇，不代表他在五種語言裡的偏好：丟掉，讓裝置語言作主。
  try { w.localStorage.removeItem('pibook-site-lang'); } catch (e) { /* 讀寫不到就算了 */ }

  function sync(lang) {
    button.setAttribute('aria-label', LABEL[lang] || LABEL.en);
    for (var i = 0; i < items.length; i++) {
      items[i].setAttribute('aria-checked', String(items[i].getAttribute('data-set-lang') === lang));
    }
  }

  function isOpen() { return !menu.hidden; }

  function open(focusWhich) {
    if (!isOpen()) {
      menu.hidden = false;
      button.setAttribute('aria-expanded', 'true');
    }
    var target = focusWhich === 'last' ? items[items.length - 1]
      : menu.querySelector('[aria-checked="true"]') || items[0];
    target.focus();
  }

  function close(returnFocus) {
    if (!isOpen()) return;
    menu.hidden = true;
    button.setAttribute('aria-expanded', 'false');
    if (returnFocus) button.focus();
  }

  function choose(lang) {
    if (P.langs.indexOf(lang) < 0) return;
    P.current = lang;
    P.apply(lang);
    sync(lang);
    try { w.localStorage.setItem(P.key, lang); } catch (e) { /* 不能存就只換這一次 */ }
    // 網址上帶著 ?lang= 的話，下次重新整理它會蓋過剛剛的選擇 —— 手動選了就把它拿掉。
    if (/[?&]lang=/.test(w.location.search) && w.history && w.history.replaceState) {
      var rest = w.location.search.slice(1).split('&').filter(function (kv) {
        return kv && kv.split('=')[0] !== 'lang';
      });
      w.history.replaceState(null, '', w.location.pathname + (rest.length ? '?' + rest.join('&') : '') + w.location.hash);
    }
  }

  button.addEventListener('click', function () {
    if (isOpen()) close(false); else open();
  });

  button.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown' || e.key === 'Down') { e.preventDefault(); open(); }
    else if (e.key === 'ArrowUp' || e.key === 'Up') { e.preventDefault(); open('last'); }
  });

  menu.addEventListener('click', function (e) {
    var item = e.target.closest ? e.target.closest('[data-set-lang]') : null;
    if (!item) return;
    choose(item.getAttribute('data-set-lang'));
    close(true);
  });

  menu.addEventListener('keydown', function (e) {
    var i = items.indexOf(d.activeElement);
    if (e.key === 'ArrowDown' || e.key === 'Down') {
      e.preventDefault(); items[(i + 1) % items.length].focus();
    } else if (e.key === 'ArrowUp' || e.key === 'Up') {
      e.preventDefault(); items[(i - 1 + items.length) % items.length].focus();
    } else if (e.key === 'Home') {
      e.preventDefault(); items[0].focus();
    } else if (e.key === 'End') {
      e.preventDefault(); items[items.length - 1].focus();
    } else if (e.key === 'Escape' || e.key === 'Esc') {
      e.preventDefault(); close(true);
    } else if (e.key === 'Tab') {
      close(false);
    }
  });

  // 點選單以外的地方、或焦點離開選單，就收起來。
  d.addEventListener('pointerdown', function (e) {
    if (isOpen() && !menu.contains(e.target) && !button.contains(e.target)) close(false);
  });
  menu.addEventListener('focusout', function (e) {
    if (e.relatedTarget && !menu.contains(e.relatedTarget) && e.relatedTarget !== button) close(false);
  });

  // 從上一頁／下一頁快取回來時，語言可能已在別的分頁改過：跟著最新的選擇走。
  w.addEventListener('pageshow', function (e) {
    if (!e.persisted || /[?&]lang=/.test(w.location.search)) return;
    var saved = null;
    try { saved = w.localStorage.getItem(P.key); } catch (err) { /* 沿用目前的 */ }
    if (saved && saved !== P.current && P.langs.indexOf(saved) >= 0) {
      P.current = saved;
      P.apply(saved);
      sync(saved);
    }
  });

  sync(P.current);
})(document, window);

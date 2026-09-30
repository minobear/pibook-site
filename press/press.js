/* 畫板以 932 CSS px 高為設計基準（＝ iPhone 6.9" 的 CSS 尺寸），
   實際輸出畫布高度不一（iOS 2796、Play 1920），這裡用 zoom 等比放大整塊版面。

   為什麼不是用 vh/vw 寫流體字級：無頭 Chrome 的 --force-device-scale-factor
   會給出一個**與輸出比例不同**的 CSS 視窗（實測 --window-size=360,640 得到
   490×489），版面等於先照 1:1 排好再被拉成 9:16 —— 文字被裁、比例走樣，
   而且不會有任何錯誤訊息。現在改成 DSF=1 ＋ 精算視窗，畫布比例才是真的。

   ⚠️ zoom 會連 100vw/100vh 一起放大，所以畫板不能寫 100vw/100vh ——
   必須由這裡換算成「除以 zoom 之後的 CSS 尺寸」再寫死，否則只會看到左上角。 */
/* 2026-09-23 起畫板本身不畫任何系統狀態列（見 phone.css 的說明），素材也已經
   在裁圖階段把狀態列與 Android 手勢列裁掉 —— App Store 與 Play 吃同一份圖，
   不需要再依網址參數切換成 iOS 專用的版本。舊的 ?ios 換圖邏輯已移除。 */

(function () {
  var BASE_H = 932;
  function apply() {
    var z = window.innerHeight / BASE_H;
    document.documentElement.style.zoom = z;
    var b = document.querySelector('.board');
    if (!b) return;
    b.style.width = (window.innerWidth / z) + 'px';
    b.style.height = BASE_H + 'px';
  }
  apply();
  window.addEventListener('resize', apply);
})();

/* 官網模式：見 press.css 最後一段。另外把「版面錨點」的位置寫進 <meta name="web-anchor">
   （有手機就是機身；沒有手機的板子是舞台上內容的聯集，星芒除外），
   tools/web_shots.py 用 --dump-dom 讀回去 —— 官網排版以錨點為準，
   伸出錨點外的特寫與陰影不佔版面。
   數值以畫板座標表示（高 932 為基準）：左右是相對畫板水平中心、上下是相對畫板頂端。
   ⚠️ 不能寫成「佔視窗的比例」：--dump-dom 與 --screenshot 的視窗外框不同（實測前者
   少了約 127px 高），畫板寬度跟著變，比例就對不上；舞台置中，所以「離中心多遠」不受影響。 */
(function () {
  if (!/[?&]web\b/.test(location.search)) return;
  document.documentElement.classList.add('web');
  function report() {
    var els = document.querySelectorAll('.stage .phone');
    if (!els.length) els = document.querySelectorAll('.stage > :not(.spark)');
    var l = Infinity, t = Infinity, r = -Infinity, b = -Infinity;
    for (var i = 0; i < els.length; i++) {
      var q = els[i].getBoundingClientRect();
      l = Math.min(l, q.left); t = Math.min(t, q.top);
      r = Math.max(r, q.right); b = Math.max(b, q.bottom);
    }
    var bd = document.querySelector('.board').getBoundingClientRect();
    var k = 932 / bd.height, cx = bd.left + bd.width / 2;
    var m = document.createElement('meta');
    m.name = 'web-anchor';
    m.content = [(l - cx) * k, (t - bd.top) * k, (r - cx) * k, (b - bd.top) * k]
      .map(function (v) { return v.toFixed(2); }).join(',');
    document.head.appendChild(m);
  }
  if (document.readyState === 'complete') report();
  else window.addEventListener('load', report);
})();

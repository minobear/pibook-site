/* 畫板以 932 CSS px 高為設計基準（＝ iPhone 6.9" 的 CSS 尺寸），
   實際輸出畫布高度不一（iOS 2796、Play 1920），這裡用 zoom 等比放大整塊版面。

   為什麼不是用 vh/vw 寫流體字級：無頭 Chrome 的 --force-device-scale-factor
   會給出一個**與輸出比例不同**的 CSS 視窗（實測 --window-size=360,640 得到
   490×489），版面等於先照 1:1 排好再被拉成 9:16 —— 文字被裁、比例走樣，
   而且不會有任何錯誤訊息。現在改成 DSF=1 ＋ 精算視窗，畫布比例才是真的。

   ⚠️ zoom 會連 100vw/100vh 一起放大，所以畫板不能寫 100vw/100vh ——
   必須由這裡換算成「除以 zoom 之後的 CSS 尺寸」再寫死，否則只會看到左上角。 */
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

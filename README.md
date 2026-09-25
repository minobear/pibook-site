# pibook.app

拍簿 Pibook 的官方網站 —— 純靜態，由 GitHub Pages 託管於 `pibook.app`。

上架審查會實際點開這裡的三個連結，所以它們必須永遠打得開：

| 網址 | 檔案 | 用途 | 誰會來看 |
|---|---|---|---|
| `/privacy/` | `privacy/index.html` | 隱私權政策 | App Store 審查、Google Play Data safety、使用者 |
| `/terms/` | `terms/index.html` | 服務條款／EULA | App Store 3.1.2（訂閱必備） |
| `/delete-account/` | `delete-account/index.html` | 帳號刪除說明 | Google Play 帳號刪除規定（必須免登入可存取） |
| `/support/` | `support/index.html` | 支援與常見問題 | App Store Connect 的「支援網址」欄位 |

## 網址沒有 .html

正式路徑是 `/privacy/` 這種形式（`privacy/index.html`）。根目錄還留著
`privacy.html` 等四個檔案，但它們只是轉址到新路徑的空殼 —— 因為送審資料、
商店後台與**已經上架的 App 版本**裡都還寫著舊網址，那些連結必須繼續有效。
新的連結一律寫沒有 .html 的版本。

## 頁首頁尾只有一份

`_partials/head.html`（語言判斷與字型）、`_partials/header.html`、`_partials/footer.html`
是唯一的來源。每一頁的 `<!-- @partial:header -->` … `<!-- @/partial:header -->`
之間是展開後的內容，**不要直接改那一段**。改完片段後跑：

```bash
python build.py          # 展開到每一頁
python build.py --check  # 只檢查：展開後的內容有沒有人手改、每一段是不是五語到齊
```

就地展開（而不是 src → dist）是因為 GitHub Pages 沒有建置步驟：頁面檔本身
就是成品，這樣原始 HTML 裡就有頁首頁尾 —— 爬蟲讀得到、關掉 JS 也看得到、
而且不會有「頁首晚一拍才出現」的版面跳動。

## 改完怎麼上線

推到 `main` 就好，GitHub Pages 會自動部署，約一分鐘生效。

```bash
python build.py && git add -A && git commit -m "更新條款" && git push
```

## 注意事項

- **`CNAME` 不要刪。** 它是 GitHub Pages 認得自訂網域的依據，刪掉網站會退回
  `<帳號>.github.io` 的網址，而審查中的 App 連結就會全部失效。
- **改條款要留紀錄。** 頁面上有「生效日期」與「版本」，實質變更請一併更新，
  並依條款所述於生效前 30 天在 App 內公告。
- **改了 `assets/*.css` 或 `assets/lang.js`，把各頁引用它們時的 `?v=` 換成當天日期。**
  GitHub Pages 讓瀏覽器快取約 10 分鐘；不換的話，老訪客會拿到「新頁面＋舊樣式」
  （例如五種語言同時出現在畫面上）。
- 條款與隱私權政策以**繁體中文為準**，其他語言是方便閱讀的譯本（條款的「語言」條明文寫了）。
  改繁中條文時，五種語言要在同一次提交裡一起改。

## 五種語言（繁中／簡中／英／日／韓）

和 App 支援的語言相同。每一段文字的五個版本都寫在同一份 HTML 裡，以 `lang`
屬性標記，相鄰的一串就是同一段話：

```html
<h2 lang="zh-Hant">隱私權政策</h2>
<h2 lang="zh-Hans">隐私权政策</h2>
<h2 lang="en">Privacy Policy</h2>
<h2 lang="ja">プライバシーポリシー</h2>
<h2 lang="ko">개인정보 처리방침</h2>
```

CSS 只顯示 `<html data-lang>` 那一種。這樣審查員把網址轉給同事時，對方看到的
會是自己讀得懂的語言，而且切換不必重新載入。

- **預設跟著裝置語言。** `_partials/head.html` 在第一次繪製之前決定：
  網址的 `?lang=ja` → 這個瀏覽器上次在選單裡手動選的 → 裝置的語言清單
  （`zh-TW`／`zh-HK`／`zh-MO` 是繁中，`zh-CN`／`zh-SG` 是簡中）→ 都沒有就英文。
  沒有 JavaScript 時顯示繁中。
- **右上角的語言選單**在 `assets/lang.js`：地球圖示＋目前語言，點開是錨定選單，
  每一項用各自的文字寫（看不懂目前語言的人也認得出自己的）。手動選的會記在
  `localStorage` 的 `pibook-lang` —— 隱私權政策第 13 節寫的「只存一項偏好」就是它。
- **字型跟著語言走**，規則與 App 的 `PibookScript` 相同：日文用 JP（繁中字型畫出來的
  漢字是中文字形）、韓文刻意只用黑體、簡中用 SC、英文與繁中共用 TC，只載入正在用的那一套。
- **新增或改寫文案時五種都要到齊。** 少了一種，那個語言的訪客會看到一個空洞，
  畫面上不會有任何錯誤 —— `python build.py --check` 會把這種段落逐條列出來。
  ⚠️ 帶 `lang` 的元素裡不要再包帶 `lang` 的元素（會被當成另一種語言藏起來）。
- **用詞跟 App 同一套**：產品名詞（整理、待刪除、圖庫、回憶⋯）與畫面上的按鈕名稱，
  照主 repo `lib/l10n/app_*.arb` 的實際字串寫；品牌在日韓英文是「Pibook」、中文是「拍簿」。
- 每一頁 `<head>` 裡的 `page-titles` 是分頁標題的五種語言。

## 首頁的截圖

首頁每一段的畫面都是**商店截圖**（主 repo 的 `store_assets/screenshots/<語言>/`），
由 `tools/web_shots.py` 裁掉上方的標題區（官網這一段自己就有標題）後轉成
`assets/shots/<語言>/<名稱>-{480,800,1200}.webp`。五種語言各一張、只顯示目前語言那一張；
看不見的那四張是 `display:none` 的 lazy 圖片，瀏覽器根本不會去下載。

商店截圖更新後：

```bash
python tools/web_shots.py        # 預設讀 ../store_assets/screenshots
```

`press/` 是商店行銷截圖的畫板。改完跑：

```bash
bash press/render.sh
```

會用無頭 Chrome 輸出到主 repo 的 `store_assets/`：
`ios_6.9/`（1290×2796，App Store 6.9 吋）與 `play_phone/`（1080×1920，Google Play）。

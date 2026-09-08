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

`_partials/header.html`、`_partials/footer.html` 是唯一的來源。每一頁的
`<!-- @partial:header -->` … `<!-- @/partial:header -->` 之間是展開後的內容，
**不要直接改那一段**。改完片段後跑：

```bash
python build.py          # 展開到每一頁
python build.py --check  # 只檢查有沒有人手改了展開後的內容
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
- 語言切換是純前端的顯示切換，兩種語言都在同一份 HTML 裡 ——
  審查員把網址轉給同事時，對方看到的會是自己讀得懂的語言。

## 首頁的手機畫面模擬與商店截圖

首頁的 App 畫面不是圖片，是照著 App 設計系統重建的 HTML/CSS 元件
（`assets/phone.css`＋手工 SVG 情景圖 `assets/scenes/`）。
**App 的皮改了，記得回來同步**：色票對 `pibook_colors.dart`、文案對 `app_zh.arb`。

`press/` 是商店行銷截圖的畫板（同一套元件）。改完跑：

```bash
bash press/render.sh
```

會用無頭 Chrome 輸出到主 repo 的 `store_assets/`：
`ios_6.9/`（1290×2796，App Store 6.9 吋）與 `play_phone/`（1080×1920，Google Play）。

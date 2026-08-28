# pibook.app

拍簿 Pibook 的官方網站 —— 純靜態，由 GitHub Pages 託管於 `pibook.app`。

上架審查會實際點開這裡的三個連結，所以它們必須永遠打得開：

| 頁面 | 用途 | 誰會來看 |
|---|---|---|
| `privacy.html` | 隱私權政策 | App Store 審查、Google Play Data safety、使用者 |
| `terms.html` | 服務條款／EULA | App Store 3.1.2（訂閱必備） |
| `delete-account.html` | 帳號刪除說明 | Google Play 帳號刪除規定（必須免登入可存取） |
| `support.html` | 支援與常見問題 | App Store Connect 的「支援網址」欄位 |

## 改完怎麼上線

推到 `main` 就好，GitHub Pages 會自動部署，約一分鐘生效。

```bash
git add -A && git commit -m "更新條款" && git push
```

## 注意事項

- **`CNAME` 不要刪。** 它是 GitHub Pages 認得自訂網域的依據，刪掉網站會退回
  `<帳號>.github.io` 的網址，而審查中的 App 連結就會全部失效。
- **改條款要留紀錄。** 頁面上有「生效日期」與「版本」，實質變更請一併更新，
  並依條款所述於生效前 30 天在 App 內公告。
- 語言切換是純前端的顯示切換，兩種語言都在同一份 HTML 裡 ——
  審查員把網址轉給同事時，對方看到的會是自己讀得懂的語言。

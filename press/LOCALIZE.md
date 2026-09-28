# 商店截圖：新增一個語言

同一套七張畫板、同一批示範照片，只換語言。整個流程**不需要人看截圖**，
只在最後看一張總覽確認。

## 一次性準備（已經做好的話跳過）

1. 截圖專用模擬器 `Pibook_Shots`（`D:\AndroidAVD\Pibook_Shots.avd`，port 5556）。
   ⚠️ 不要用共用的 emulator-5554（別的工作階段在用、裡面有使用者真照片）。
   開機：`ANDROID_SDK_ROOT=… emulator -avd Pibook_Shots -port 5556 -no-snapshot -no-audio -gpu host`
2. 裝不含開發者工具的 release 包（`tool/build_apk.ps1 -NoDevTools`，另開 worktree 打，
   模擬器要暫時關 Impeller 的 release manifest，只放在那個 worktree 裡）。
   ⚠️ 模擬器剛開機時 `adb install` 會失敗（套件管理員還沒好），而且之後的腳本照樣跑、
   拍到的是舊包。裝完一定看到 `Success` 再開拍。
3. 示範圖庫已推好（`build/store_demo_library/`，八本相簿、今天 7 張、巴哥犬三張、
   三組連拍、兩支回憶影片、兩支 4K 影片）。檔案分組寫在 `shoot_locale.py` 最上面。
4. `python shoot_locale.py base` —— 把目前的 App 資料存成快照（引導都關過、沒有整理記號）。
   之後每個語言開拍前都會先還原這份快照。

## 每個新語言（例如 fr）

```bash
cd site/press
# 1. shoot_locale.py：ALBUMS 加八本相簿的名字、LOCALE_TAG 加語系代碼
# 2. make_boards.py：TEXT 加一份翻譯、FONTS 加字型
python shoot_locale.py fr          # 約 15 分鐘，大多在等壓縮；可以丟背景跑
python make_boards.py fr
LOCALES=fr bash render.sh          # → store_assets/screenshots/fr/（兩種尺寸＋總覽.jpg）
```

最後只看 `store_assets/screenshots/fr/總覽.jpg` 一張。常見要修的只有一種：
**標題太長換成三行**（英文 32px 一行約 20 字元）→ 改短 `TEXT` 裡那一句，重跑後兩步。

只重拍某幾張：`python shoot_locale.py fr --only similar,memory`。

## 新語言上架前：先查 App 本身有沒有跑版

商店截圖好看之前，App 本身要先跟中文版一樣整齊。

```bash
python audit_wrap.py fr      # 約 5 分鐘／語言；中文當基準
```

它會輸出 `_shoot_tmp/sheet_*.jpg`（每個畫面「中文｜新語言」並排），看一輪就知道
哪裡中文一行、新語言折成兩行。修法（見 CLAUDE.md〈一行版位〉）：
1. 先縮短那句文案；
2. 把那個版位登記進 `test/i18n_width_parity_test.dart` 的 `_singleLineSlots`，
   之後任何語言再變長都會被測試擋下來。

要多查一個畫面，就在 `audit_wrap.py` 的 `SCREENS` 加一筆。

## 翻譯的原則

- 先抄 App 自己的字：引導頁的標題（`onboardingOrganizeTitle`、`onboardingFindSimilarTitle`、
  `onboardingMemoryTitle`、`onboardingSloganLead`）各語言都有，語氣也一致。
- 標籤與 App 畫面上的字要一致（例如「已整理」用 `statsOrganizedLabel`）。
- 回憶那張講「隨機回味」，不要講「N 年前的今天」（影片分頁是隨機播的）。
- 日文不用「あなた」、韓文不用「당신」；韓文標題用黑體（沒有明體）。
- 商店截圖不准寫「第一」「最好」「#1」這類排名字眼（Google Play 規範）。

## 為什麼這樣做（每一條都是踩過的）

| 做法 | 原因 |
|---|---|
| 相簿名在裝置上直接改資料夾，再到 App 補圖示與順序 | `adb input text` 打不出中日韓字 |
| 每個語言先還原 App 資料快照 | 「已整理」記號是 App 資料；圖庫那張要先整理一輪，下個語言得歸零 |
| 回憶影片搬回圖庫後改 `date_added`（`is_pending` 1→改→0） | Android 的「幾年前」看加入時間；搬進搬出會變成「現在」 |
| 壓縮每個語言換一天 | 影片免費額度每天 2 部，超過整批擋 |
| 壓縮跑馬燈用參考圖比對挑格（`shoot_ref/compress_strip.png`） | 跑馬燈一直在捲，挑格不必看圖 |
| 相似清單用節點座標微調捲動 | 字的長度不同，清單位置會差十幾 px，第三組的大小會被下方按鈕切到 |
| 手勢一律推 .sh 到裝置上跑 | 從電腦下每個 adb 指令有 200–400ms 抖動 |
| 縮圖特寫、飛進相簿的小照片各語言共用 | 上面沒有字 |
| 切語言前先清掉 App 自己的語言（`cmd locale set-app-locales … --locales ""`） | Android 13 起每個 App 可以有自己的語言、會蓋過系統；簡中那輪就這樣拍成了繁體 |
| 相簿改名前先 `rmdir` 同名空資料夾 | 目標已存在時 `mv` 會把整本搬「進去」，而不是改名 |

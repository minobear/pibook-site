# 原始錄影（未剪）

專案 `clips/` 裡的六支，有四支存的就是**完整錄影**（review / similar / album / memory），
只有 `library.mp4` 與 `compress.mp4` 是剪過的 —— 中間的空檔被切掉了。
這裡放的是那兩支的**完整版**，以後要重新決定剪點時不必再開模擬器重錄。

| 檔案 | 長度 | 內容 |
|---|---|---|
| `library_raw.mp4` | 10.97s | 靜止 3s → 長按 → 加入相簿 → 選相簿 → 收起（中間表單有一段等待） |
| `compress_raw.mp4` | 8.74s | 選三部影片 → 下一步 → 比較品質 → 開始壓縮 → 確認對話框 |
| `compress_run_raw.mp4` | 4.86s | 按下「開始」之後的進度畫面（模擬器編碼器失敗，跑不完） |

重剪的指令形狀（fps=30 要放在 trim 之前，否則 VFR 來源會掉格）：

```bash
ffmpeg -y -i library_raw.mp4 -filter_complex "\
[0:v]fps=30,split=2[v0][v1];\
[v0]trim=0.20:3.28,setpts=PTS-STARTPTS[a];\
[v1]trim=3.28:5.15,setpts=PTS-STARTPTS[b];\
[a][b]concat=n=2:v=1:a=0[o]" -map "[o]" -r 30 -c:v libx264 -crf 17 -pix_fmt yuv420p out.mp4
```

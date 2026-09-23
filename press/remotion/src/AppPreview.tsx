import React from 'react';
import { AbsoluteFill, Audio, staticFile } from 'remotion';
import { TransitionSeries, springTiming, linearTiming } from '@remotion/transitions';
import { slide } from '@remotion/transitions/slide';
import { wipe } from '@remotion/transitions/wipe';
import { fade } from '@remotion/transitions/fade';
import { FeatureTitle } from './scenes/FeatureTitle';
import { Stage, Move, Highlight } from './scenes/Stage';
import { OpenCard, EndCard } from './scenes/Bookends';
import { ACCENTS } from './theme';

/**
 * 一段功能 ＝ 一張滿版標題卡 ＋ 一段實機錄影。
 *
 * 分鏡與每一拍的用意寫在 `site/press/DIRECTOR_SCRIPT.md`（導演腳本）。
 * 要調整演示內容請**先改那份**，再回來對這裡的數字。
 *
 * 三條在這裡被實作出來的鐵則：
 *  C1 標題卡切進實機畫面後，動作必須在 ~0.3 秒內開始 → startFrom 都對到操作前一點點。
 *  C2 要介紹的細節要主動聚焦 → moves 把鏡頭推到相簿軌 / 縮圖標記 / 省下的數字上。
 *  C3 不要整段緩慢放大 → 運鏡是「停 → 一次推 → 停」，且外框不動（見 Stage.tsx）。
 */

/**
 * 兩種長度，兩套節奏。
 *
 * **`long`（Google Play / YouTube）**：宣傳影片是 YouTube 連結，沒有長度上限，
 * 所以照內容本來該有的節奏走 —— 開場字卡讀得完、每段操作看得完、回憶那段留得住呼吸。
 *
 * **`short`（App Store）**：Apple 規定 App Preview **必須落在 15–30 秒**，超過直接退件。
 * 六個功能塞進 30 秒本來就緊，所以這裡不是「把長版加速播」（那只會更趕），
 * 而是**每段各自取較短的素材窗**：留住那一拍的重點動作，捨掉前後的鋪陳。
 */
type Variant = 'long' | 'short';

type Cut = { startFrom: number; frames: number; rate?: number };

type Beat = {
  key: keyof typeof ACCENTS;
  index: string;
  kicker: string;
  lines: string[];
  highlight?: string;
  clip: string;
  long: Cut;
  short: Cut;
  moves?: Move[];
  highlights?: Highlight[];
  from?: 'bottom' | 'right';
};

export const BEATS: Beat[] = [
  {
    // 保留、保留、丟棄、保留、丟棄、保留 —— 兩次丟棄才看得出這是雙向的決定
    key: 'sort',
    index: '01',
    kicker: 'ORGANIZE',
    lines: ['滑一下', '就整理好一張'],
    highlight: '一張',
    clip: 'clips/review.mp4',
    long: { startFrom: 1.05, frames: 165, rate: 1.0 },
    short: { startFrom: 1.05, frames: 92, rate: 1.42 },
    from: 'bottom',
  },
  {
    // 四張連續歸檔。相簿軌橫跨整個畫面寬度，推近必然裁掉兩端 —— 不做運鏡，
    // 觸控指示圈本身已經把視線帶到那一排。
    key: 'file',
    index: '02',
    kicker: 'FILING',
    lines: ['點一下相簿', '照片就收進去'],
    highlight: '收進去',
    clip: 'clips/album.mp4',
    long: { startFrom: 1.02, frames: 132, rate: 1.0 },
    short: { startFrom: 1.02, frames: 80, rate: 1.40 },
    from: 'right',
  },
  {
    // 兩組各挑一張保留（兩組都完整在畫面上時才點）→ 點進全螢幕左右比對
    key: 'pick',
    index: '03',
    kicker: 'BEST SHOT',
    lines: ['連拍裡最美的', '自動挑好'],
    highlight: '自動挑好',
    clip: 'clips/similar.mp4',
    long: { startFrom: 1.05, frames: 205, rate: 1.0 },
    short: { startFrom: 1.05, frames: 134, rate: 1.52 },
    from: 'bottom',
  },
  {
    // 完整跑完一次：勾三部 → 比較品質 → 確認 → 壓縮動畫 → 完成結算（1.69 GB / −96.4%）
    key: 'space',
    index: '04',
    kicker: 'FREE SPACE',
    lines: ['三部影片', '省回 1.7 GB'],
    highlight: '1.7 GB',
    clip: 'clips/compress.mp4',
    long: { startFrom: 0.05, frames: 200, rate: 1.09 },
    short: { startFrom: 0.05, frames: 126, rate: 1.56 },
    from: 'right',
  },
  {
    // 三次上滑、四則影片、中間雙擊愛心。
    // **原速播放且每則都留停留** —— 這一拍賣的就是「停下來看」的感覺，
    // 加速等於把它要傳達的東西直接拿掉。
    key: 'relive',
    index: '05',
    kicker: 'MEMORIES',
    lines: ['留下的照片', '自己回來找你'],
    highlight: '自己回來',
    clip: 'clips/memory.mp4',
    long: { startFrom: 0.35, frames: 268, rate: 1.0 },
    short: { startFrom: 1.60, frames: 186, rate: 1.0 },
    from: 'bottom',
  },
  {
    // 先推到縮圖上的整理標記與相簿標記並停住，再拉回來長按 → 加入相簿
    key: 'library',
    index: '06',
    kicker: 'LIBRARY',
    lines: ['整理過的', '一眼看得到'],
    highlight: '一眼',
    clip: 'clips/library.mp4',
    long: { startFrom: 0.05, frames: 118, rate: 0.78 },
    short: { startFrom: 0.05, frames: 98, rate: 0.94 },
    from: 'right',
    moves: [
      { at: 4, rect: [0.01, 0.19, 0.46, 0.41], dur: 22 },
      { at: 76, rect: [0, 0, 1, 1], dur: 16 },
    ],
    // 只圈起來還不夠 —— 觀眾看得到記號，但不知道它是什麼意思，所以補上文字。
    highlights: [
      { at: 26, until: 76, x: 0.220, y: 0.240, r: 0.042, label: '整理狀態' },
      { at: 34, until: 76, x: 0.149, y: 0.335, r: 0.080, label: '已收進相簿' },
    ],
  },
];

const CHROME = {
  long:  { open: 62, title: 46, end: 66 },
  short: { open: 46, title: 37, end: 50 },
} as const;

const T_IN = 12;
const T_OUT = 10;

/**
 * 錄影是在 Android 模擬器上拍的，畫面頂端是 Android 的狀態列。App Store 那一支
 * 必須改用 `clips/ios/` 底下的版本（`press/ios_statusbar.py clips` 產生：只換掉
 * 系統列，App 畫面不動）—— 2026-09-21 審查以 Guideline 2.3.10「截圖出現非 iOS 的
 * 狀態列」退件，預覽影片放在同一個欄位，一樣會被看到。
 */
type StatusBar = 'android' | 'ios';

const clipFor = (clip: string, statusBar: StatusBar) =>
  statusBar === 'ios' ? clip.replace(/^clips\//, 'clips/ios/') : clip;

export const AppPreview: React.FC<{ variant?: Variant; statusBar?: StatusBar }> = ({
  variant = 'long',
  statusBar = 'android',
}) => {
  const C0 = CHROME[variant];
  return (
    <AbsoluteFill style={{ backgroundColor: '#FBF7F0' }}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={C0.open}>
          <OpenCard />
        </TransitionSeries.Sequence>

        {BEATS.map((b) => {
          const a = ACCENTS[b.key];
          const cut = b[variant];
          return (
            <React.Fragment key={b.key}>
              <TransitionSeries.Transition
                presentation={slide({ direction: 'from-bottom' })}
                timing={springTiming({
                  config: { damping: 200 },
                  durationInFrames: T_IN,
                  durationRestThreshold: 0.001,
                })}
              />
              <TransitionSeries.Sequence durationInFrames={C0.title}>
                <FeatureTitle
                  index={b.index}
                  kicker={b.kicker}
                  lines={b.lines}
                  highlight={b.highlight}
                  accent={a}
                />
              </TransitionSeries.Sequence>

              <TransitionSeries.Transition
                presentation={wipe({ direction: 'from-bottom' })}
                timing={linearTiming({ durationInFrames: T_OUT })}
              />
              <TransitionSeries.Sequence durationInFrames={cut.frames}>
                <Stage
                  clip={clipFor(b.clip, statusBar)}
                  startFrom={cut.startFrom}
                  accent={a}
                  from={b.from}
                  rate={cut.rate ?? 1}
                  moves={b.moves}
                  highlights={b.highlights}
                  caption={`${b.index} · ${b.kicker}`}
                />
              </TransitionSeries.Sequence>
            </React.Fragment>
          );
        })}

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: T_IN })}
        />
        <TransitionSeries.Sequence durationInFrames={C0.end}>
          <EndCard />
        </TransitionSeries.Sequence>
      </TransitionSeries>

      {/* App Store 規定一定要有音軌，就算全靜音。 */}
      <Audio src={staticFile('silence.wav')} />
    </AbsoluteFill>
  );
};

/** 給 Root 算總長用：片段長度相加、再扣掉每個轉場重疊的格數。 */
export const totalFrames = (variant: Variant = 'long') => {
  const c = CHROME[variant];
  const scenes =
    c.open + BEATS.reduce((n, b) => n + c.title + b[variant].frames, 0) + c.end;
  const overlaps = BEATS.length * (T_IN + T_OUT) + T_IN;
  return scenes - overlaps;
};

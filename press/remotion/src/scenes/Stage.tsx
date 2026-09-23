import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { Accent, FONT_SANS } from '../theme';

/** 實機錄影原檔的尺寸（screenrecord 出來的都是這個） */
const SRC_W = 1080;
const SRC_H = 2400;

/**
 * 一次運鏡：把畫面裡的一塊**矩形**推到滿版。
 *
 * 為什麼是「矩形」而不是「縮放倍率 + 焦點」（舊版做法）：
 *  1. 舊版要手算倍率，算錯就會把焦點推到畫面外，露出黑邊。
 *  2. 就算沒露黑邊，也常常放大過頭，把本來要給人看的那塊 UI 裁掉一半。
 * 改成宣告「我要讓這塊完整看到」，倍率與位移由程式反推，並強制夾在合法範圍內
 * —— 黑邊與裁切這兩件事就都不可能發生了。
 *
 * rect 是原始錄影畫面的比例座標 [x0, y0, x1, y1]，0~1。
 */
export type Move = {
  at: number;
  rect: [number, number, number, number];
  dur?: number;
  /** 目標矩形四周要多留多少（比例），預設 6%，避免貼齊畫面邊緣 */
  pad?: number;
};

/** 由矩形反推「倍率 + 中心點」，並夾住讓畫面永遠填滿、不露底。 */
function solve(rect: [number, number, number, number], pad: number) {
  const [x0, y0, x1, y1] = rect;
  const rw = Math.max(1e-3, x1 - x0) * (1 + pad * 2);
  const rh = Math.max(1e-3, y1 - y0) * (1 + pad * 2);
  // 倍率 s 時，畫面上看得到的是原圖的 1/s —— 要讓 rect 完整入鏡就得 1/s >= rw 且 >= rh
  const s = Math.max(1, Math.min(1 / rw, 1 / rh));
  const half = 0.5 / s;
  const cx = Math.min(Math.max((x0 + x1) / 2, half), 1 - half);
  const cy = Math.min(Math.max((y0 + y1) / 2, half), 1 - half);
  return { s, cx, cy };
}

const FULL: [number, number, number, number] = [0, 0, 1, 1];

/**
 * 推近之後，在畫面上圈出一個小東西。
 *
 * 為什麼需要：只是把畫面放大，觀眾不知道該看哪裡 —— 使用者回報過「根本抓不到重點」。
 * 圈本身是行銷素材的疊層，不是 App 的 UI；圈的是真實畫面上真實存在的記號。
 * 座標是**原始錄影畫面**的比例（0~1），會跟著運鏡一起被縮放，所以永遠貼在該貼的位置上。
 */
export type Highlight = {
  at: number; until: number; x: number; y: number; r: number;
  /** 圈旁邊的說明文字。只圈起來，觀眾仍然不知道那個記號是什麼意思。 */
  label?: string;
  /** 文字放在圈的哪一側（預設右邊） */
  side?: 'right' | 'left';
};

/**
 * 實機畫面舞台。
 *
 * ⚠️ 三件事刻意這樣寫，都是被使用者打回來過的：
 *  1. **絕不裁切**：依高度等比縮放放進畫布，兩側留底色。兩種輸出長寬比不同，
 *     共用一支再裁就是上下少一大塊。
 *  2. **圓角遮罩與陰影掛在完全不動的外層**，運鏡動的是內層 —— 外框不動，
 *     邊緣就沒有機會每幀重新取樣、閃爍。
 *  3. **運鏡永遠夾在合法範圍**（見 solve），畫面不可能被推出鏡頭外露出黑底。
 */
export const Stage: React.FC<{
  clip: string;
  startFrom: number;
  accent: Accent;
  from?: 'bottom' | 'right';
  rate?: number;
  moves?: Move[];
  highlights?: Highlight[];
  caption?: string;
}> = ({ clip, startFrom, accent, from = 'bottom', rate = 1, moves = [], highlights = [], caption }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // ── 版位：完整放進畫面，整數化避免半像素 ──────────────────────────
  const margin = Math.round(height * 0.05);
  const scaleFit = Math.min((height - margin * 2) / SRC_H, (width - margin * 2) / SRC_W);
  const w = Math.round(SRC_W * scaleFit);
  const h = Math.round(SRC_H * scaleFit);

  // ── 進場：整張卡推入（只動位移與透明度，不動縮放）──────────────
  const enter = spring({ frame, fps, config: { damping: 200, mass: 0.7 }, durationInFrames: 16 });
  const dx = from === 'right' ? Math.round(interpolate(enter, [0, 1], [width * 0.3, 0])) : 0;
  const dy = from === 'bottom' ? Math.round(interpolate(enter, [0, 1], [height * 0.14, 0])) : 0;

  // ── 運鏡：一段一段疊，每段是一條彈簧；起點是滿版 ────────────────
  let cur = solve(FULL, 0);
  for (const m of moves) {
    const p = spring({
      frame: frame - m.at,
      fps,
      config: { damping: 200, mass: 0.85 },
      durationInFrames: m.dur ?? 22,
    });
    const t = solve(m.rect, m.pad ?? 0.06);
    cur = {
      s: cur.s + (t.s - cur.s) * p,
      cx: cur.cx + (t.cx - cur.cx) * p,
      cy: cur.cy + (t.cy - cur.cy) * p,
    };
  }
  // 過場途中也要夾一次：兩段運鏡之間的插值可能短暫跑出合法範圍
  const half = 0.5 / cur.s;
  const cx = Math.min(Math.max(cur.cx, half), 1 - half);
  const cy = Math.min(Math.max(cur.cy, half), 1 - half);
  const tx = (0.5 - cx) * w * cur.s;
  const ty = (0.5 - cy) * h * cur.s;

  return (
    <AbsoluteFill style={{ backgroundColor: accent.stageBg }}>
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div
          style={{
            width: w,
            height: h,
            borderRadius: Math.round(w * 0.062),
            overflow: 'hidden',
            transform: `translate(${dx}px, ${dy}px)`,
            opacity: enter,
            boxShadow: `0 ${Math.round(h * 0.028)}px ${Math.round(h * 0.07)}px -${Math.round(
              h * 0.026,
            )}px rgba(18,26,34,.45)`,
            backgroundColor: '#000',
          }}
        >
          <div
            style={{
              width: '100%',
              height: '100%',
              transform: `translate(${tx}px, ${ty}px) scale(${cur.s})`,
              transformOrigin: 'center center',
              willChange: 'transform',
              backfaceVisibility: 'hidden',
            }}
          >
            <OffthreadVideo
              src={staticFile(clip)}
              startFrom={Math.round(startFrom * fps)}
              playbackRate={rate}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              muted
            />

            {highlights.map((hl, i) => {
              // 進場 6 格畫出來、離場 8 格收掉，中間輕輕呼吸一下
              const inP = interpolate(frame, [hl.at, hl.at + 6], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
              const outP = interpolate(frame, [hl.until, hl.until + 8], [1, 0], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
              const a = inP * outP;
              if (a <= 0.001) return null;
              const pulse = 1 + 0.06 * Math.sin((frame - hl.at) / 5);
              const d = hl.r * 2 * w * pulse;
              return (
                <div
                  key={i}
                  style={{
                    position: 'absolute',
                    left: `${(hl.x - hl.r * pulse) * 100}%`,
                    top: `${(hl.y - (hl.r * pulse * w) / h) * 100}%`,
                    width: d,
                    height: d,
                    borderRadius: '50%',
                    border: `${Math.max(2, Math.round(3 / cur.s))}px solid rgba(246,196,83,${a})`,
                    boxShadow: `0 0 ${Math.round(14 / cur.s)}px rgba(246,196,83,${a * 0.55})`,
                    opacity: interpolate(a, [0, 1], [0, 1]),
                    transform: `scale(${interpolate(inP, [0, 1], [1.5, 1])})`,
                  }}
                />
              );
            })}

            {highlights.map((hl, i) => {
              if (!hl.label) return null;
              // 文字要跟著運鏡貼在記號旁邊，但**大小不能跟著放大** ——
              // 所以字級與間距都除以當前縮放倍率，畫面上看起來永遠一樣大。
              const inP = interpolate(frame, [hl.at + 4, hl.at + 12], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
              const outP = interpolate(frame, [hl.until, hl.until + 8], [1, 0], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
              const a = inP * outP;
              if (a <= 0.001) return null;
              const left = hl.side === 'left';
              const gap = (hl.r + 0.022) * w;
              const fs = Math.round(30 / cur.s);
              return (
                <div
                  key={'L' + i}
                  style={{
                    position: 'absolute',
                    left: left ? undefined : `${hl.x * 100}%`,
                    right: left ? `${(1 - hl.x) * 100}%` : undefined,
                    top: `${hl.y * 100}%`,
                    transform: `translate(${left ? -gap : gap}px, -50%)`,
                    opacity: a,
                    whiteSpace: 'nowrap',
                    fontFamily: FONT_SANS,
                    fontWeight: 700,
                    fontSize: fs,
                    lineHeight: 1,
                    color: '#1B2530',
                    background: 'rgba(246,196,83,.96)',
                    padding: `${Math.round(9 / cur.s)}px ${Math.round(16 / cur.s)}px`,
                    borderRadius: Math.round(999 / cur.s),
                    boxShadow: `0 ${Math.round(4 / cur.s)}px ${Math.round(14 / cur.s)}px rgba(18,26,34,.35)`,
                  }}
                >
                  {hl.label}
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>

      {caption ? (
        <AbsoluteFill
          style={{
            alignItems: 'center',
            justifyContent: 'flex-end',
            paddingBottom: Math.round(height * 0.016),
          }}
        >
          <div
            style={{
              fontFamily: FONT_SANS,
              fontWeight: 700,
              fontSize: Math.round(Math.min(width, height * 0.52) * 0.034),
              letterSpacing: '.22em',
              color: accent.stageFg,
              opacity: interpolate(frame, [5, 14], [0, 0.55], { extrapolateRight: 'clamp' }),
            }}
          >
            {caption}
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

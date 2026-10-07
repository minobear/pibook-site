import React from 'react';
import { AbsoluteFill, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { SANS } from './tokens';
import { DecisionStamps, Stamp } from './Flourish';

/** 錄影素材：1080×2400 實拍，裁掉狀態列與手勢列後是 1080×2260（見 video/rec.py 的 CROP）。 */
export const SRC_W = 1080;
export const SRC_H = 2260;
/** 觸控座標是在 1080×2400 的裝置座標上記的，素材上方被裁掉 100px。 */
const CROP_TOP = 100;

/** 手機外框（比例照 site/assets/phone.css：414 寬、圓角 60、邊框 12；螢幕圓角 44/390）。 */
export const phoneGeometry = (height: number) => {
  const k = 12 / 414;
  const outerW = Math.round((SRC_W / SRC_H) * height / (1 + 2 * k * (SRC_W / SRC_H) - 2 * k));
  const bezel = Math.round(outerW * k);
  const screenW = outerW - bezel * 2;
  const screenH = Math.round(screenW * (SRC_H / SRC_W));
  return {
    outerW,
    outerH: screenH + bezel * 2,
    bezel,
    screenW,
    screenH,
    outerR: Math.round(outerW * (60 / 414)),
    screenR: Math.round(screenW * (44 / 390)),
  };
};

/**
 * 一次運鏡：把畫面裡的一塊矩形推到滿版（座標是裁切後素材的 0~1 比例）。
 * 「宣告要看到哪一塊」而不是「放大幾倍」—— 倍率由程式反推並夾住，不會露底、不會推過頭
 * （舊版 Stage.tsx 的作法，C3：外框不動、動的是內層，邊緣不會閃）。
 */
export type Move = { at: number; rect: [number, number, number, number]; dur?: number; pad?: number };

/** 畫面上的說明標籤（圈出記號＋一句話）。座標同上。 */
export type Callout = {
  at: number;
  until: number;
  x: number;
  y: number;
  r: number;
  label: string;
  /** below＝標籤擺在圈的正下方（左右都有東西、不能蓋住的時候：相似照片縮圖軌的鄰格） */
  side?: 'left' | 'right' | 'below';
  /** 標籤往下挪多少（素材高度的比例）；不是 0 時從圈畫一條引線過去 —— 兩個標籤擠在同一排時用 */
  dy?: number;
  /** 保留／刪除的標記：圈與標籤換成 App 的決策色（保留＝綠、刪除＝珊瑚，`keep_discard_buttons.dart`），
   *  不然一律是金色。相似照片比對頁按下去之後，把縮圖軌上那個小角標圈出來（2026-10-07 使用者：
   *  「標記要在他按下之後更顯眼的能被注意到」） */
  tone?: 'keep' | 'discard';
};

const CALLOUT_TONE = {
  gold: { ring: [246, 196, 83], fill: 'rgba(246,196,83,.98)', ink: '#1B2530' },
  keep: { ring: [109, 168, 144], fill: 'rgba(109,168,144,.98)', ink: '#FFFFFF' },
  discard: { ring: [232, 128, 110], fill: 'rgba(232,128,110,.98)', ink: '#FFFFFF' },
} as const;

/** 錄影時記下的一個手勢（rec.py → clips.ts）。時間是素材時間軸上的秒數。 */
export type Touch = { kind: string; args: number[]; b: number; e: number };

function solve(rect: [number, number, number, number], pad: number, aspect: number) {
  const [x0, y0, x1, y1] = rect;
  const rw = Math.max(1e-3, x1 - x0) * (1 + pad * 2);
  const rh = Math.max(1e-3, y1 - y0) * (1 + pad * 2 * aspect);
  const s = Math.max(1, Math.min(1 / rw, 1 / rh));
  const half = 0.5 / s;
  const cx = Math.min(Math.max((x0 + x1) / 2, half), 1 - half);
  const cy = Math.min(Math.max((y0 + y1) / 2, half), 1 - half);
  return { s, cx, cy };
}

/** 觸控指示：先出現（預備）→ 接觸瞬間最實 → 收掉。App 的反應落在接觸之後（導演腳本 §3）。 */
const TouchMarks: React.FC<{ touches: Touch[]; t: number; w: number; h: number; zoom: number }> = ({
  touches,
  t,
  w,
  h,
  zoom,
}) => {
  const px = (x: number) => (x / SRC_W) * w;
  const py = (y: number) => ((y - CROP_TOP) / SRC_H) * h;
  const R = (66 / SRC_W) * w; // 接觸時外圈直徑約 140px（素材 1080 寬上；導演腳本 §2）
  const nodes: React.ReactNode[] = [];
  touches.forEach((tc, i) => {
    if (tc.kind === 'tap' || tc.kind === 'dtap' || tc.kind === 'hold') {
      const contact = tc.kind === 'hold' ? tc.b : tc.e;
      const release = tc.kind === 'hold' ? tc.e : tc.e;
      const a0 = contact - 0.12;
      const a1 = release + 0.32;
      if (t < a0 || t > a1) return;
      const pre = interpolate(t, [a0, contact], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      const post = interpolate(t, [release, a1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      const x = px(tc.args[0]);
      const y = py(tc.args[1]);
      const ringR = R * interpolate(pre, [0, 1], [1.7, 1.05]) * (1 + post * 0.55);
      const op = pre * (1 - post);
      const holdP =
        tc.kind === 'hold' ? interpolate(t, [tc.b, tc.e], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) : 0;
      const dotR = R * 0.62 * (1 - post * 0.4);
      nodes.push(
        <svg
          key={i}
          width={w}
          height={h}
          style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', pointerEvents: 'none' }}
        >
          {/* 外圈：白環＋深色內環，白底與深色照片上都看得見 */}
          <circle cx={x} cy={y} r={ringR} fill="none" stroke="rgba(255,255,255,.95)" strokeWidth={(5 / zoom) * (w / 660)} opacity={op} />
          <circle cx={x} cy={y} r={ringR - (5 / zoom) * (w / 660)} fill="none" stroke="rgba(27,37,48,.35)" strokeWidth={(2 / zoom) * (w / 660)} opacity={op} />
          {/* 實心點：接觸瞬間最實 */}
          <circle cx={x} cy={y} r={dotR} fill="rgba(255,255,255,.62)" stroke="rgba(27,37,48,.28)" strokeWidth={(1.5 / zoom) * (w / 660)} opacity={op * (pre >= 0.999 ? 1 : pre)} />
          {tc.kind === 'hold' && holdP > 0 && holdP < 1 ? (
            <circle
              cx={x}
              cy={y}
              r={ringR + (8 / zoom) * (w / 660)}
              fill="none"
              stroke="rgba(255,255,255,.95)"
              strokeWidth={(5 / zoom) * (w / 660)}
              strokeDasharray={`${2 * Math.PI * (ringR + (8 / zoom) * (w / 660)) * holdP} 9999`}
              transform={`rotate(-90 ${x} ${y})`}
              opacity={op}
            />
          ) : null}
        </svg>,
      );
    } else if (tc.kind === 'swipe' || tc.kind === 'drag') {
      const [x1, y1, x2, y2] = tc.args;
      const a0 = tc.b - 0.08;
      const a1 = tc.e + 0.22;
      if (t < a0 || t > a1) return;
      const p = interpolate(t, [tc.b, tc.e], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      const pre = interpolate(t, [a0, tc.b], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      const post = interpolate(t, [tc.e, a1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      const sx = px(x1);
      const sy = py(y1);
      const cx = px(x1 + (x2 - x1) * p);
      const cy = py(y1 + (y2 - y1) * p);
      // 軌跡：只畫最近一段，尾巴淡出（像手機錄影開「顯示觸控」的樣子）
      const tailP = Math.max(0, p - 0.45);
      const tx = px(x1 + (x2 - x1) * tailP);
      const ty = py(y1 + (y2 - y1) * tailP);
      const op = pre * (1 - post);
      const gid = `tr${i}`;
      nodes.push(
        <svg
          key={i}
          width={w}
          height={h}
          style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', pointerEvents: 'none' }}
        >
          <defs>
            <linearGradient id={gid} gradientUnits="userSpaceOnUse" x1={tx} y1={ty} x2={cx} y2={cy}>
              <stop offset="0" stopColor="#fff" stopOpacity={0} />
              <stop offset="1" stopColor="#fff" stopOpacity={0.85} />
            </linearGradient>
          </defs>
          {p > 0.02 ? (
            <line x1={tx} y1={ty} x2={cx} y2={cy} stroke={`url(#${gid})`} strokeWidth={R * 0.9} strokeLinecap="round" opacity={op} />
          ) : null}
          <circle cx={cx} cy={cy} r={R * 0.62} fill="rgba(255,255,255,.7)" stroke="rgba(27,37,48,.3)" strokeWidth={(1.5 / zoom) * (w / 660)} opacity={op} />
          <circle cx={cx} cy={cy} r={R * 1.02} fill="none" stroke="rgba(255,255,255,.92)" strokeWidth={(4 / zoom) * (w / 660)} opacity={op * (1 - p * 0.5)} />
          {p === 0 ? <circle cx={sx} cy={sy} r={R} fill="none" stroke="#fff" strokeWidth={4} opacity={op} /> : null}
        </svg>,
      );
    }
  });
  return <>{nodes}</>;
};

/**
 * 一段實機畫面：手機外框固定不動，裡面播素材、運鏡、疊觸控指示與說明標籤。
 * `frame` 是這一段的相對格數（呼叫端用 Sequence 包好）。
 */
export const PhoneClip: React.FC<{
  clip: string;
  from: number;
  rate?: number;
  touches?: Touch[];
  moves?: Move[];
  callouts?: Callout[];
  stamps?: Stamp[];
  spots?: { at: number; until: number; rect: [number, number, number, number]; radius?: number }[];
  /** 這一段在素材上播到哪（秒）：快到段尾才開始的手勢不畫（只會閃一下就被切掉） */
  until?: number;
  screenW: number;
  screenH: number;
  radius: number;
}> = ({ clip, from, rate = 1, touches = [], moves = [], callouts = [], stamps = [], spots = [], until, screenW: w, screenH: h, radius }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const tLocal = frame / fps;
  const tClip = from + tLocal * rate;

  let cur = solve([0, 0, 1, 1], 0, w / h);
  for (const m of moves) {
    const p = spring({ frame: frame - Math.round(m.at * fps), fps, config: { damping: 200, mass: 0.8 }, durationInFrames: m.dur ?? 16 });
    const tgt = solve(m.rect, m.pad ?? 0.05, w / h);
    cur = { s: cur.s + (tgt.s - cur.s) * p, cx: cur.cx + (tgt.cx - cur.cx) * p, cy: cur.cy + (tgt.cy - cur.cy) * p };
  }
  const half = 0.5 / cur.s;
  const cx = Math.min(Math.max(cur.cx, half), 1 - half);
  const cy = Math.min(Math.max(cur.cy, half), 1 - half);
  const tx = (0.5 - cx) * w * cur.s;
  const ty = (0.5 - cy) * h * cur.s;

  return (
    <div style={{ position: 'absolute', inset: 0, borderRadius: radius, overflow: 'hidden', background: '#000' }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translate(${tx}px, ${ty}px) scale(${cur.s})`,
          transformOrigin: 'center center',
          willChange: 'transform',
        }}
      >
        <OffthreadVideo
          src={staticFile(clip)}
          startFrom={Math.round(from * fps)}
          playbackRate={rate}
          muted
          style={{ width: '100%', height: '100%', display: 'block' }}
        />
        {/* 這一段開始前就按下去的手勢不畫：段落之間是剪接，上一刀的觸控圈不該拖到這一刀
           （similar_done 從「刪除 9 張」之後切進來，殘留的圈剛好落在成果頁的「完成」上，像在按完成） */}
        <TouchMarks
          touches={touches.filter((tc) => tc.b >= from - 0.05 && (until === undefined || tc.b <= until - 0.25))}
          t={tClip}
          w={w}
          h={h}
          zoom={cur.s}
        />
        <DecisionStamps stamps={stamps} t={tLocal} w={w} h={h} />
        {/* 聚光（v3.3「相似的照片自動排成一組」）：這一塊框起來，其餘調暗 —— 框是細的實線，不發光 */}
        {spots.map((sp, i) => {
          const a =
            interpolate(tLocal, [sp.at, sp.at + 0.25], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) *
            interpolate(tLocal, [sp.until - 0.2, sp.until], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          if (a <= 0.001) return null;
          const [x0, y0, x1, y1] = sp.rect;
          const u = height / 1920;
          return (
            <div
              key={`spot${i}`}
              style={{
                position: 'absolute',
                left: x0 * w,
                top: y0 * h,
                width: (x1 - x0) * w,
                height: (y1 - y0) * h,
                borderRadius: (sp.radius ?? 0.035) * w,
                border: `${(5 * u) / cur.s}px solid rgba(246,196,83,${a})`,
                boxShadow: `0 0 0 ${3 * h}px rgba(16,22,30,${0.5 * a})`,
                pointerEvents: 'none',
              }}
            />
          );
        })}
        {callouts.map((c, i) => {
          const a =
            interpolate(tLocal, [c.at, c.at + 0.2], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) *
            interpolate(tLocal, [c.until, c.until + 0.2], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          if (a <= 0.001) return null;
          // 標籤的字級與線寬以「成片上看起來多大」為準：在推近的內層裡，所以除以當下的倍率
          const u = height / 1920;
          const left = c.side === 'left';
          const below = c.side === 'below';
          const d = c.r * 2 * w;
          const fs = (44 * u) / cur.s;
          const stroke = (6 * u) / cur.s;
          const gap = (c.r + 0.012) * w;
          const cx = c.x * w;
          const cy = c.y * h;
          const ly = below ? cy + d / 2 + (18 * (height / 1920)) / cur.s : cy + (c.dy ?? 0) * h;
          const lx = below ? cx : left ? cx - gap : cx + gap;
          const tone = CALLOUT_TONE[c.tone ?? 'gold'];
          const ring = (alpha: number) => `rgba(${tone.ring.join(',')},${alpha})`;
          return (
            <React.Fragment key={i}>
              <div
                style={{
                  position: 'absolute',
                  left: cx - d / 2,
                  top: cy - d / 2,
                  width: d,
                  height: d,
                  borderRadius: '50%',
                  border: `${stroke}px solid ${ring(a)}`,
                  boxShadow: `0 0 0 ${stroke * 0.5}px rgba(27,37,48,${0.35 * a})`,
                  transform: `scale(${interpolate(a, [0, 1], [1.35, 1])})`,
                }}
              />
              {c.dy ? (
                <svg
                  width={w}
                  height={h}
                  style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', pointerEvents: 'none' }}
                >
                  <line
                    x1={cx + (left ? -1 : 1) * (d / 2) * 0.7}
                    y1={cy + (d / 2) * 0.7}
                    x2={lx}
                    y2={ly}
                    stroke={ring(a)}
                    strokeWidth={stroke * 0.8}
                    strokeLinecap="round"
                  />
                </svg>
              ) : null}
              <div
                style={{
                  position: 'absolute',
                  left: left ? undefined : lx,
                  right: left ? w - lx : undefined,
                  top: ly,
                  transform: below
                    ? `translateX(-50%) scale(${interpolate(a, [0, 1], [0.85, 1])})`
                    : `translateY(-50%) scale(${interpolate(a, [0, 1], [0.85, 1])})`,
                  transformOrigin: below ? 'center top' : left ? 'right center' : 'left center',
                  opacity: a,
                  whiteSpace: 'nowrap',
                  fontFamily: SANS,
                  fontWeight: 700,
                  fontSize: fs,
                  lineHeight: 1,
                  letterSpacing: '.04em',
                  color: tone.ink,
                  background: tone.fill,
                  padding: `${(14 * u) / cur.s}px ${(24 * u) / cur.s}px`,
                  borderRadius: 999,
                  boxShadow: `0 ${(8 * u) / cur.s}px ${(20 * u) / cur.s}px -${(6 * u) / cur.s}px rgba(16,22,30,.5)`,
                }}
              >
                {c.label}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

/** 手機外框本體（深色邊框＋淡淡的外陰影；不畫瀏海、不畫任何系統列）。 */
export const PhoneFrame: React.FC<{
  x: number;
  y: number;
  height: number;
  scale?: number;
  children: React.ReactNode;
}> = ({ x, y, height, scale = 1, children }) => {
  const g = phoneGeometry(height);
  return (
    <div
      style={{
        position: 'absolute',
        left: x - g.outerW / 2,
        top: y,
        width: g.outerW,
        height: g.outerH,
        borderRadius: g.outerR,
        padding: g.bezel,
        boxSizing: 'border-box',
        background: 'linear-gradient(160deg, #3A4654 0%, #232C36 55%, #1A222B 100%)',
        boxShadow:
          'inset 0 1px 1px rgba(255,255,255,.28), inset 0 -1px 2px rgba(0,0,0,.55), 0 2px 6px rgba(26,34,43,.18), 0 40px 90px -30px rgba(26,34,43,.5)',
        transform: `scale(${scale})`,
        transformOrigin: '50% 100%',
      }}
    >
      <div style={{ position: 'relative', width: g.screenW, height: g.screenH, borderRadius: g.screenR, overflow: 'hidden' }}>
        {children}
      </div>
    </div>
  );
};

export const Fill: React.FC<{ color: string }> = ({ color }) => <AbsoluteFill style={{ background: color }} />;

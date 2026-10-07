import React from 'react';
import { Easing, interpolate } from 'remotion';
import { GOLD, SANS } from './tokens';
import { PLANE_SVG } from './planeSvg';

/**
 * 預覽影片 v3.2（2026-10-07 使用者）的三個小動畫：
 * - [DecisionStamps]：相似照片比對頁按下「保留／丟棄」的那一刻，照片上蓋一個大的標記、很快淡掉
 *   （App 按下去就跳到下一張，鈕的顏色看不到 —— 使用者選「只在影片裡加強調」）。
 * - [SighEmoji]：開場「相簿爆滿／整理真的好難」之後，底下冒出一個真的在嘆氣的表情（吸一口氣 → 吐出來）。
 * - [PlaneArc]：結尾「離線也能用」配一架小飛機沿弧線飛過（就算在飛機上沒網路也能整理）。
 *   飛機用的是 App 相簿圖示裡那架「旅行」像素飛機（`lib/core/design/pibook_album_icons.dart`），
 *   跟商店的標題與搜尋結果主視覺是同一套圖。
 *
 * 表情符號用系統的彩色表情字型（Windows 上是 Fluent Emoji，微軟以 MIT 授權開源）—— 跟字卡裡的 🤩 同一套。
 */

export const EMOJI_FONT = '"Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif';

const easeInOut = Easing.bezier(0.45, 0, 0.25, 1);
const easeOut = Easing.bezier(0.2, 0.8, 0.3, 1);
const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const prog = (t: number, a: number, b: number, ease: (n: number) => number = (v) => v) =>
  ease(interpolate(t, [a, b], [0, 1], clamp));
const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

// ─────────────────────────────── 保留／丟棄的大標記 ───────────────────────────────

export type Stamp = { at: number; kind: 'keep' | 'discard'; x?: number; y?: number };

/** App 的決策色（`lib/core/widgets/decision/keep_discard_buttons.dart`）：保留＝綠、丟棄＝珊瑚；圖示是 Material 的圓角版 */
const STAMP = {
  keep: {
    color: 'rgba(109,168,144,.95)',
    label: '保留',
    path: 'M9 16.17 5.53 12.7a.996.996 0 1 0-1.41 1.41l4.18 4.18c.39.39 1.02.39 1.41 0L20.29 7.71a.996.996 0 1 0-1.41-1.41L9 16.17z',
  },
  discard: {
    color: 'rgba(232,128,110,.95)',
    label: '丟棄',
    path: 'M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2H8c-1.1 0-2 .9-2 2v10zM18 4h-2.5l-.71-.71c-.18-.18-.44-.29-.7-.29H9.91c-.26 0-.52.11-.7.29L8.5 4H6c-.55 0-1 .45-1 1s.45 1 1 1h12c.55 0 1-.45 1-1s-.45-1-1-1z',
  },
} as const;

/** t＝段內秒數；w、h＝素材畫面的寬高（在運鏡的內層裡，跟著畫面一起縮放）。 */
export const DecisionStamps: React.FC<{ stamps: Stamp[]; t: number; w: number; h: number }> = ({ stamps, t, w, h }) => (
  <>
    {stamps.map((s, i) => {
      const p = t - s.at;
      if (p < 0 || p > 0.8) return null;
      const st = STAMP[s.kind];
      // 按下去：0.1 秒彈到位 → 停住 → 0.5 秒起淡掉（同時微微放大，像蓋上去之後散開）
      const pop = interpolate(p, [0, 0.1, 0.18], [0.55, 1.08, 1], clamp);
      const fade = interpolate(p, [0, 0.05, 0.5, 0.78], [0, 1, 1, 0], clamp);
      const grow = 1 + 0.06 * prog(p, 0.5, 0.78);
      const d = w * 0.3;
      const cx = (s.x ?? 0.5) * w;
      const cy = (s.y ?? 0.45) * h;
      return (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: cx - d / 2,
            top: cy - d / 2,
            width: d,
            height: d,
            opacity: fade,
            transform: `scale(${pop * grow})`,
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              width: d,
              height: d,
              borderRadius: '50%',
              background: st.color,
              boxShadow: `0 ${d * 0.04}px ${d * 0.14}px rgba(10,14,20,.35)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg viewBox="0 0 24 24" width={d * 0.5} height={d * 0.5}>
              <path d={st.path} fill="#FFFFFF" />
            </svg>
          </div>
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: d * 1.06,
              transform: 'translateX(-50%)',
              whiteSpace: 'nowrap',
              fontFamily: SANS,
              fontWeight: 700,
              fontSize: d * 0.2,
              letterSpacing: '.08em',
              color: '#FFFFFF',
              textShadow: `0 ${d * 0.01}px ${d * 0.05}px rgba(0,0,0,.55)`,
            }}
          >
            {st.label}
          </div>
        </div>
      );
    })}
  </>
);

// ─────────────────────────────── 嘆氣 ───────────────────────────────

/**
 * 一個真的在嘆氣的表情：冒出來 → 吸一口氣（往上、拉長）→ 吐出來（往下沉、壓扁、微微低頭，一團氣從嘴邊飄出去）
 * → 回到原樣。t＝從開場開始的秒數；at＝冒出來的時間；speed＝整段播放的速度（開場只有 2.4 秒時用 1.5）。
 * 臉用 😩（真的很困擾的表情，使用者 2026-10-07 指定）；😮‍💨 自己就畫了一團氣、再飄一團出來會重複。
 */
export const SighEmoji: React.FC<{ t: number; at: number; size: number; speed?: number }> = ({ t, at, size, speed = 1 }) => {
  const k = (t - at) * speed;
  if (k < 0) return <div style={{ width: size, height: size }} />;
  const appear = interpolate(k, [0, 0.12, 0.22], [0, 1.1, 1], clamp);
  const fadeIn = interpolate(k, [0, 0.08], [0, 1], clamp);
  const inhale = prog(k, 0.35, 0.8, easeInOut);
  const exhale = prog(k, 0.8, 1.45, easeOut);
  const settle = prog(k, 1.45, 1.95, easeInOut);
  // 吸氣：拉高、上移；吐氣：壓扁、下沉、低頭；之後慢慢回來
  const sy = lerp(lerp(lerp(1, 1.07, inhale), 0.92, exhale), 1, settle);
  const sx = lerp(lerp(lerp(1, 0.98, inhale), 1.04, exhale), 1, settle);
  const ty = lerp(lerp(lerp(0, -0.05, inhale), 0.04, exhale), 0, settle) * size;
  const rot = lerp(lerp(0, -4, exhale), 0, settle);
  // 那團氣：從嘴邊（臉的下緣中間）出來、往右下飄、變大、淡掉
  const puff = prog(k, 0.85, 1.75, easeOut);
  const puffO = interpolate(k, [0.85, 1.0, 1.45, 1.8], [0, 0.95, 0.8, 0], clamp);
  return (
    // 視覺置中（使用者 2026-10-07：嘆氣的臉偏右）：系統表情字型的 😩 在字框裡偏右約 0.12 個字框寬（實測 886 寬
    // 的成片上臉的中心在 465.5、畫面中心 443），整組往左挪回來；吐出去的那團氣也收短一點，不把重心往右拉。
    <div style={{ position: 'relative', width: size, height: size, transform: `translateX(${-0.118 * size}px)` }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          fontFamily: EMOJI_FONT,
          fontSize: size * 0.92,
          lineHeight: `${size}px`,
          textAlign: 'center',
          opacity: fadeIn,
          transform: `translateY(${ty}px) rotate(${rot}deg) scale(${appear * sx}, ${appear * sy})`,
          transformOrigin: '50% 85%',
        }}
      >
        😩
      </div>
      {puffO > 0.001 ? (
        <div
          style={{
            position: 'absolute',
            left: size * lerp(0.56, 0.9, puff),
            top: size * lerp(0.8, 0.86, puff),
            fontFamily: EMOJI_FONT,
            fontSize: size * lerp(0.16, 0.46, puff),
            lineHeight: 1,
            opacity: puffO,
            transform: 'translate(-30%, -50%)',
          }}
        >
          💨
        </div>
      ) : null}
    </div>
  );
};

// ─────────────────────────────── 小飛機 ───────────────────────────────

/**
 * 結尾「離線也能用」底下的弧線：飛機從左邊進來、沿著一條往上拱的弧線貼著那行字的下方飛過、從右邊出去，
 * 後面留一串淡金色的點（飛機雲）慢慢散掉。座標以那行字的中心為原點（px）。
 * t＝結尾卡開始後的秒數；at＝起飛時間；span＝左右兩端離中心多遠；top＝弧頂在中心下方多少；dip＝兩端比弧頂低多少。
 */
export const PlaneArc: React.FC<{ t: number; at: number; dur: number; span: number; top: number; dip: number; size: number }> = ({
  t,
  at,
  dur,
  span,
  top,
  dip,
  size,
}) => {
  const k = (t - at) / dur;
  if (k < 0) return null;
  // 二次貝茲的頂點在 0.5 時落在 (0, top)：控制點要比頂點再高 dip
  const P0 = { x: -span, y: top + dip };
  const Q = { x: 0, y: top - dip };
  const P2 = { x: span, y: top + dip };
  const pos = (q: number) => {
    const u = 1 - q;
    return {
      x: u * u * P0.x + 2 * u * q * Q.x + q * q * P2.x,
      y: u * u * P0.y + 2 * u * q * Q.y + q * q * P2.y,
    };
  };
  const q = easeInOut(Math.min(1, Math.max(0, k)));
  const p = pos(q);
  const dx = 2 * (1 - q) * (Q.x - P0.x) + 2 * q * (P2.x - Q.x);
  const dy = 2 * (1 - q) * (Q.y - P0.y) + 2 * q * (P2.y - Q.y);
  const ang = (Math.atan2(dy, dx) * 180) / Math.PI + 90; // 像素飛機的機頭朝上
  // 飛機雲：沿路每隔一小段一個點；點越舊越淡（年紀用「飛機已經飛過它多遠」近似）
  const dots: React.ReactNode[] = [];
  const N = 46;
  for (let i = 1; i < N; i++) {
    const qi = i / N;
    if (qi > q - 0.025) break;
    const age = (q - qi) * dur * 1.6 + Math.max(0, k - 1) * dur;
    const o = interpolate(age, [0, 0.15, 0.9], [0, 0.85, 0], clamp);
    if (o <= 0.01) continue;
    const pt = pos(qi);
    dots.push(
      <div
        key={i}
        style={{
          position: 'absolute',
          left: pt.x - size * 0.045,
          top: pt.y - size * 0.045,
          width: size * 0.09,
          height: size * 0.09,
          borderRadius: '50%',
          background: GOLD,
          opacity: o,
        }}
      />,
    );
  }
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 0, height: 0, overflow: 'visible', pointerEvents: 'none' }}>
      {dots}
      {k <= 1 ? (
        <div
          style={{
            position: 'absolute',
            left: p.x - size / 2,
            top: p.y - size / 2,
            width: size,
            height: size,
            transform: `rotate(${ang}deg)`,
            filter: 'drop-shadow(0 3px 6px rgba(0,0,0,.35))',
          }}
          dangerouslySetInnerHTML={{ __html: PLANE_SVG.replace('<svg ', `<svg width="${size}" height="${size}" `) }}
        />
      ) : null}
    </div>
  );
};

// ─────────────────────────────── 儲存空間快滿了 ───────────────────────────────

const STORAGE = {
  ok: [109, 168, 144], // App success
  warn: [232, 169, 113], // App warning
  danger: [216, 97, 92], // App danger
} as const;
const mix3 = (a: readonly number[], b: readonly number[], p: number) => a.map((v, i) => Math.round(v + (b[i] - v) * p));

/**
 * 開場：手機的儲存空間一路被塞滿（2026-10-07 使用者：「配個示意手機儲存空間爆滿，容量條變紅、有警告、危急的感覺」）。
 * 容量條越塞越快（照片一直進來），綠 → 橘 → 紅；滿的那一刻整張卡抖一下、警告標誌閃一下。
 * 是一張「示意圖」，不是系統畫面：用 App 的字與決策色，不模仿 iOS 設定頁。t＝開場後的秒數。
 */
export const StorageAlert: React.FC<{ t: number; at: number; width: number; u: number }> = ({ t, at, width, u }) => {
  const k = t - at;
  if (k < 0) return null;
  const enter = prog(k, 0, 0.28, easeOut);
  const fill = lerp(0.62, 0.996, prog(k, 0.06, 0.75, Easing.bezier(0.55, 0, 0.9, 0.6)));
  const c =
    fill < 0.8 ? mix3(STORAGE.ok, STORAGE.warn, (fill - 0.62) / 0.18) : mix3(STORAGE.warn, STORAGE.danger, Math.min(1, (fill - 0.8) / 0.14));
  const color = `rgb(${c.join(',')})`;
  const full = k >= 0.75;
  // 滿的那一刻：左右抖三下、越來越小
  const sk = k - 0.75;
  const shake = full && sk < 0.42 ? Math.sin(sk * Math.PI * 2 * 7.5) * 9 * u * (1 - sk / 0.42) : 0;
  const blink = full ? interpolate(sk % 0.5, [0, 0.12, 0.25, 0.5], [1, 0.35, 1, 1], clamp) : 1;
  const used = (fill * 128).toFixed(1);
  return (
    <div
      style={{
        width,
        padding: `${24 * u}px ${30 * u}px ${26 * u}px`,
        borderRadius: 30 * u,
        background: 'rgba(251,247,240,.97)',
        boxShadow: `0 ${14 * u}px ${36 * u}px -${10 * u}px rgba(10,14,20,.55)`,
        opacity: enter,
        transform: `translate(${shake}px, ${lerp(-26, 0, enter) * u}px)`,
        fontFamily: SANS,
        color: '#2A3744',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 * u }}>
        <svg viewBox="0 0 24 24" width={38 * u} height={38 * u} style={{ opacity: blink, flex: 'none' }}>
          <path d="M12 3.2 1.6 21h20.8L12 3.2z" fill={color} stroke={color} strokeWidth="1.4" strokeLinejoin="round" />
          <rect x="11" y="9.2" width="2" height="6.2" rx="1" fill="#FFFFFF" />
          <circle cx="12" cy="18" r="1.2" fill="#FFFFFF" />
        </svg>
        <div style={{ fontWeight: 700, fontSize: 31 * u, letterSpacing: '.04em', flex: 1 }}>{full ? '儲存空間已滿' : '儲存空間'}</div>
        <div style={{ fontWeight: 700, fontSize: 31 * u, color, fontVariantNumeric: 'tabular-nums' }}>{Math.round(fill * 100)}%</div>
      </div>
      <div style={{ marginTop: 18 * u, height: 16 * u, borderRadius: 999, background: 'rgba(42,55,68,.12)', overflow: 'hidden' }}>
        <div style={{ width: `${fill * 100}%`, height: '100%', borderRadius: 999, background: color }} />
      </div>
      <div style={{ marginTop: 12 * u, fontSize: 22 * u, color: '#5C6A78', letterSpacing: '.03em', fontVariantNumeric: 'tabular-nums' }}>
        已使用 {used} GB／128 GB
      </div>
    </div>
  );
};

// ─────────────────────────────── 看得頭暈的「爆滿」 ───────────────────────────────

/**
 * 「爆滿」兩個字：照片多到看得頭暈（2026-10-07 使用者）。字本身輕輕晃、繞小圈，後面拖著兩層錯開的殘影
 * （珊瑚與淺藍，往相反方向繞）—— 像眼睛對不準焦的複視。不發光、不模糊。開頭最暈，之後收小但不停。
 */
export const DizzyText: React.FC<{ text: string; t: number; at: number; size: number }> = ({ text, t, at, size }) => {
  const k = Math.max(0, t - at);
  const env = interpolate(k, [0, 0.35, 1.8, 2.8], [0, 1, 1, 0.45], clamp);
  const w = 2 * Math.PI * 1.35; // 一秒繞 1.35 圈
  const r = size * 0.08 * env;
  const rot = 6.5 * Math.sin(w * k) * env;
  const base = { x: r * 0.35 * Math.cos(w * k), y: r * 0.35 * Math.sin(w * k) };
  const ghost = (phase: number, dir: number) => ({
    x: r * Math.cos(dir * w * k + phase),
    y: r * Math.sin(dir * w * k + phase),
  });
  const g1 = ghost(0.9, 1);
  const g2 = ghost(2.6, -1);
  const layer = (dx: number, dy: number, color: string, opacity: number): React.CSSProperties => ({
    position: 'absolute',
    left: 0,
    top: 0,
    color,
    opacity,
    transform: `translate(${dx}px, ${dy}px) rotate(${rot}deg)`,
  });
  return (
    <span style={{ position: 'relative', display: 'inline-block' }}>
      <span style={layer(g1.x, g1.y, '#F4A291', 0.65 * env)}>{text}</span>
      <span style={layer(g2.x, g2.y, '#8FB3D9', 0.55 * env)}>{text}</span>
      <span style={{ position: 'relative', display: 'inline-block', transform: `translate(${base.x}px, ${base.y}px) rotate(${rot}deg)` }}>{text}</span>
    </span>
  );
};

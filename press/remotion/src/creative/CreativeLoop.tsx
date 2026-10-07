import React from 'react';
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';

/**
 * App Store 創意素材（iOS 27 起的「產品頁標題」「搜尋結果」）的影片版：照片一張接一張收進相簿軌。
 *
 * 版面不在這裡排：`site/press/creative/make_creative.py --video` 先用 Chrome 把整個場景（字、相簿軌、皮皮、
 * 兩側落下的照片、虛線路線）**不含排隊的照片、哪一格都沒亮**烤成底圖，再烤一張「四個目標格都亮著」的，
 * 把那四格裁下來 —— 跟靜態 PNG 是同一份版面、同一套字。這裡只動兩樣東西：
 *   1. 排隊的照片：沿著底圖上那條虛線（二次貝茲）一張接一張往前。
 *   2. 目標那一格：點一下（觸控圈）→ 亮起 → 最前面那張縮小落進去 → 熄掉。
 * 跟 App 裡的相簿軌同一個動作：先點相簿，照片就收進去。
 *
 * 一張 3 秒、六張一輪＝18 秒，輪完剛好回到起點 —— 循環播放看不出接縫。
 * 六張而不是三張：隊伍裡同時有三張，三張一輪的話剛收進相簿的那張下一秒就從隊伍最後面又冒出來。
 * T.ringEnd–T.flyStart 那一段（格子亮著、觸控圈已散、照片還在原位）＝靜態 PNG 那一刻。
 */

export type Item = {
  photo: string;
  pos: string;
  album: string;
  /** 亮著的那一格（從第二張底圖裁下來的，連同名稱與皮皮的手） */
  lit: { src: string; x: number; y: number; w: number; h: number };
  /** 格子中心 */
  tx: number;
  ty: number;
};
/** 手機模式（v3 C「手機破框」）：照片是手機裡的整理卡片，被點進相簿時從螢幕裡飛出來、落進軌道上那一格 */
export type PhoneGeo = {
  /** 卡片能被看見的範圍（手機螢幕、到相簿軌上緣為止 —— 軌道擋在手機前面） */
  clip: { x: number; y: number; w: number; h: number; r: number };
  card: { x: number; y: number; w: number; h: number; r: number };
  /** 後面那一張：只露出上緣一條 */
  back: { x: number; y: number; w: number; h: number; o: number };
  /** 卡片右下角的愛心與展開鈕 */
  icon: { size: number; right: number; bottom: number; gap: number };
};
export type Scene = {
  /** queue（預設）＝照片沿著虛線排隊；phone＝手機裡的整理卡片 */
  mode?: 'queue' | 'phone';
  phone?: PhoneGeo;
  /** 從哪裡進場（預設：路線起點、看不見、轉 12°）。v3 A「照片牆」＝從牆上空出來的那一格 */
  entry?: { q: number; scale: number; rot: number; o: number };
  placement: string;
  loc: string;
  zoom: number;
  plate: string;
  ts: number;
  /** 最前面那張的位置（＝靜態圖的巴哥犬） */
  hero: { x: number; y: number; size: number; rot: number };
  /** 排隊路線：P0（最遠）→ 控制點 Q → 最前面那張的中心 */
  path: { x0: number; y0: number; qx: number; qy: number };
  /** 排在後面的位置，近的在前（q＝在路線上的位置，0 最遠、1 最前） */
  slots: { q: number; scale: number; rot: number }[];
  items: Item[];
  /** 照片的陰影（已換算成輸出像素）：各主題不同，與靜態圖的 .fly 相同 */
  shadow: string;
};

export const CYCLE_SEC = 3;
const T = {
  tap: 0.3, // 點相簿：觸控圈出現、那一格亮起
  litIn: 0.42,
  ringEnd: 0.56, // 觸控圈散掉
  // 0.56–0.70＝靜態圖那一刻（海報影格：第 38 格＝0.633 秒）
  flyStart: 0.7, // 最前面那張開始落進格子
  arrive: 1.0, // 到了格子正上方
  land: 1.12, // 縮進去、看不見了（配樂在這一刻放「收進相簿」音效）
  advStart: 1.22, // 後面的往前遞補
  advEnd: 2.05,
  litOut: 2.1, // 那一格熄掉
  litOutEnd: 2.5,
};

const easeInOut = Easing.bezier(0.45, 0, 0.25, 1);
const easeIn = Easing.bezier(0.5, 0, 0.9, 0.6);
const easeOut = Easing.bezier(0.2, 0.75, 0.25, 1);
const prog = (t: number, a: number, b: number, ease: (n: number) => number = (v) => v) =>
  ease(interpolate(t, [a, b], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

type Pose = { x: number; y: number; size: number; rot: number; o: number };

const Photo: React.FC<{ src: string; pos: string; pose: Pose; z: number; shadow: string }> = ({ src, pos, pose, z, shadow }) => (
  <div
    style={{
      position: 'absolute',
      left: pose.x - pose.size / 2,
      top: pose.y - pose.size / 2,
      width: pose.size,
      height: pose.size,
      transform: `rotate(${pose.rot}deg)`,
      zIndex: z,
      opacity: pose.o,
      borderRadius: '14%',
      overflow: 'hidden',
      background: '#ccc',
      boxShadow: shadow,
    }}
  >
    <Img src={staticFile(src)} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: pos, display: 'block' }} />
  </div>
);

export const CreativeLoop: React.FC<{ scene: Scene }> = ({ scene }) =>
  scene.mode === 'phone' ? <PhoneLoop scene={scene} /> : <QueueLoop scene={scene} />;

const QueueLoop: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = scene.items.length;
  const sec = frame / fps;
  const k = Math.floor(sec / CYCLE_SEC);
  const t = sec - k * CYCLE_SEC;
  const item = (i: number) => scene.items[(((k + i) % n) + n) % n];
  const { hero, path } = scene;

  // 路線上的站：最前面（q=1）、後面排隊的幾格（v2 兩格；v3 A 一格都沒有）、進場的地方
  const S = scene.slots.length;
  const entry = scene.entry ?? { q: 0, scale: (S ? scene.slots[S - 1].scale : 1) * 0.6, rot: 12, o: 0 };
  const stops = [{ q: 1, scale: 1, rot: hero.rot, o: 1 }, ...scene.slots.map((s) => ({ ...s, o: 1 })), entry];
  const onPath = (q: number) => {
    const u = 1 - q;
    return {
      x: u * u * path.x0 + 2 * u * q * path.qx + q * q * hero.x,
      y: u * u * path.y0 + 2 * u * q * path.qy + q * q * hero.y,
    };
  };
  const between = (from: number, to: number, p: number): Pose => {
    const a = stops[from];
    const b = stops[to];
    const q = lerp(a.q, b.q, p);
    const { x, y } = onPath(q);
    return { x, y, size: hero.size * lerp(a.scale, b.scale, p), rot: lerp(a.rot, b.rot, p), o: lerp(a.o, b.o, p) };
  };

  // 最前面那張：落進目標格。位置先到（T.arrive），到了格子正上方才縮完、淡掉 —— 半透明的照片
  // 只出現在目標格上，不會疊在隔壁那格上讓人以為收錯相簿。
  // 路線：目標在右邊 → 先往右、再從上面落進去（不從狗狗那格上面橫切過去）；
  // 目標在左邊 → 直線斜落（先往左會劃過標題的尾巴，英文、日文的標題更長）
  const target = item(0);
  const pf = prog(t, T.flyStart, T.arrive, easeInOut);
  const u = 1 - pf;
  const right = target.tx > hero.x;
  const cx = right ? target.tx : (hero.x + target.tx) / 2;
  const cy = right ? hero.y - scene.ts * 0.1 : (hero.y + target.ty) / 2;
  const front: Pose = {
    x: u * u * hero.x + 2 * u * pf * cx + pf * pf * target.tx,
    y: u * u * hero.y + 2 * u * pf * cy + pf * pf * target.ty,
    size: lerp(hero.size, scene.ts * 0.62, pf) * lerp(1, 0.55, prog(t, T.arrive - 0.04, T.land, easeIn)),
    rot: lerp(hero.rot, 0, pf),
    o: 1 - prog(t, T.arrive - 0.02, T.land, easeIn),
  };

  // 後面的往前遞補（每一張晚一點起步，讀起來是一張推著一張）
  const adv = (lag: number) => prog(t, T.advStart + lag, T.advEnd + lag * 0.6, easeOut);
  const litO = prog(t, T.tap, T.litIn, easeOut) * (1 - prog(t, T.litOut, T.litOutEnd, easeInOut));
  // 觸控圈：在格子中心按下去 —— 縮小一點再散開
  const ringP = prog(t, T.tap - 0.02, T.ringEnd);
  const ringO = interpolate(ringP, [0, 0.15, 0.6, 1], [0, 0.95, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const ringR = scene.ts * lerp(0.36, 0.3, prog(t, T.tap, T.tap + 0.12, easeOut)) * (1 + 0.18 * prog(t, T.tap + 0.15, T.ringEnd));
  const rw = Math.max(3, ringR * 0.1);

  return (
    <AbsoluteFill>
      <Img src={staticFile(scene.plate)} style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%' }} />
      {/* 會輪到的照片與亮格全部先掛著（看不見）：每個渲染分頁一開始就載好，換張時不會有空白格 */}
      <div style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', opacity: 0 }}>
        {scene.items.map((c) => (
          <React.Fragment key={c.photo}>
            <Img src={staticFile(c.photo)} style={{ width: 1, height: 1 }} />
            <Img src={staticFile(c.lit.src)} style={{ width: 1, height: 1 }} />
          </React.Fragment>
        ))}
      </div>
      {litO > 0 ? (
        <Img
          src={staticFile(target.lit.src)}
          style={{ position: 'absolute', left: target.lit.x, top: target.lit.y, width: target.lit.w, height: target.lit.h, opacity: litO, zIndex: 5 }}
        />
      ) : null}
      {ringO > 0 ? (
        <div
          style={{
            position: 'absolute',
            left: target.tx - ringR,
            top: target.ty - ringR,
            width: ringR * 2,
            height: ringR * 2,
            borderRadius: '50%',
            zIndex: 30,
            opacity: ringO,
            background: 'rgba(255,255,255,.34)',
            boxShadow: `inset 0 0 0 ${rw}px rgba(255,255,255,.95), inset 0 0 0 ${rw * 1.45}px rgba(27,37,48,.28), 0 1px ${rw}px rgba(27,37,48,.25)`,
          }}
        />
      ) : null}
      {/* 進場的那一張（遞補開始才出現；一出現就是實的，不要半透明地飄一路） */}
      {t >= T.advStart ? (
        <Photo
          src={item(S + 1).photo}
          pos={item(S + 1).pos}
          pose={{ ...between(S + 1, S, adv(0.06 * S)), o: entry.o + (1 - entry.o) * prog(adv(0.06 * S), 0, 0.22) }}
          z={22}
          shadow={scene.shadow}
        />
      ) : null}
      {Array.from({ length: S }, (_, j) => S - j).map((i) => (
        <Photo
          key={i}
          src={item(i).photo}
          pos={item(i).pos}
          pose={t >= T.advStart ? between(i, i - 1, adv(0.06 * (i - 1))) : between(i, i, 0)}
          z={25 - i}
          shadow={scene.shadow}
        />
      ))}
      {t < T.land ? <Photo src={target.photo} pos={target.pos} pose={front} z={25} shadow={scene.shadow} /> : null}
    </AbsoluteFill>
  );
};

// ─────────────────────────── 手機模式（v3 C「手機破框」） ───────────────────────────

const HEART_SVG = (
  <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} strokeLinejoin="round" style={{ width: '100%', height: '100%' }}>
    <path d="M12 20.5s-7.5-4.6-7.5-10.1A4.2 4.2 0 0 1 12 7.6a4.2 4.2 0 0 1 7.5 2.8c0 5.5-7.5 10.1-7.5 10.1z" />
  </svg>
);
const EXPAND_SVG = (
  <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{ width: '100%', height: '100%' }}>
    <circle cx="12" cy="12" r="9.2" />
    <path d="M8.5 13.6 12 10.1l3.5 3.5" />
  </svg>
);

type Rect = { x: number; y: number; w: number; h: number; r: number; o: number; rot: number };

const Card: React.FC<{ src: string; pos: string; rc: Rect; z: number; shadow: string; icons?: { o: number; g: PhoneGeo['icon'] } }> = ({
  src,
  pos,
  rc,
  z,
  shadow,
  icons,
}) => (
  <div
    style={{
      position: 'absolute',
      left: rc.x,
      top: rc.y,
      width: rc.w,
      height: rc.h,
      borderRadius: rc.r,
      overflow: 'hidden',
      opacity: rc.o,
      transform: `rotate(${rc.rot}deg)`,
      zIndex: z,
      background: '#ccc',
      boxShadow: shadow,
    }}
  >
    <Img src={staticFile(src)} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: pos, display: 'block' }} />
    {icons && icons.o > 0 ? (
      <div style={{ position: 'absolute', right: icons.g.right, bottom: icons.g.bottom, display: 'flex', gap: icons.g.gap, opacity: icons.o }}>
        <div style={{ width: icons.g.size, height: icons.g.size }}>{HEART_SVG}</div>
        <div style={{ width: icons.g.size, height: icons.g.size }}>{EXPAND_SVG}</div>
      </div>
    ) : null}
  </div>
);

/**
 * 一張 3 秒，跟 App 裡點相簿一樣：點一下格子（觸控圈、亮起）→ 前面那張卡縮小、從手機螢幕裡飛出來落進那一格
 * → 後面那張往前補上 → 再後面一張從後面浮出來。卡片在螢幕裡時被裁在「螢幕到相簿軌上緣」之內（軌道擋在手機前面）；
 * 飛出去那張不裁 —— 照片真的從手機裡跑出來、落進軌道。
 */
const PhoneLoop: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = scene.phone as PhoneGeo;
  const n = scene.items.length;
  const sec = frame / fps;
  const k = Math.floor(sec / CYCLE_SEC);
  const t = sec - k * CYCLE_SEC;
  const item = (i: number) => scene.items[(((k + i) % n) + n) % n];
  const target = item(0);
  const front: Rect = { ...g.card, o: 1, rot: 0 };
  const back: Rect = { x: g.back.x, y: g.back.y, w: g.back.w, h: g.back.h, r: g.card.r, o: g.back.o, rot: 0 };
  const mix = (a: Rect, b: Rect, p: number): Rect => ({
    x: lerp(a.x, b.x, p),
    y: lerp(a.y, b.y, p),
    w: lerp(a.w, b.w, p),
    h: lerp(a.h, b.h, p),
    r: lerp(a.r, b.r, p),
    o: lerp(a.o, b.o, p),
    rot: lerp(a.rot, b.rot, p),
  });

  // 飛出去的那張：長方形的卡 → 落到格子上方縮成小方塊 → 縮進去淡掉
  const pf = prog(t, T.flyStart, T.arrive, easeInOut);
  const side = scene.ts * 0.62;
  const c0x = g.card.x + g.card.w / 2;
  const c0y = g.card.y + g.card.h / 2;
  const qx = lerp(c0x, target.tx, 0.85);
  const qy = lerp(c0y, target.ty, 0.35);
  const u = 1 - pf;
  const fx = u * u * c0x + 2 * u * pf * qx + pf * pf * target.tx;
  const fy = u * u * c0y + 2 * u * pf * qy + pf * pf * target.ty;
  const shrink = lerp(1, 0.55, prog(t, T.arrive - 0.04, T.land, easeIn));
  const fw = lerp(g.card.w, side, pf) * shrink;
  const fh = lerp(g.card.h, side, pf) * shrink;
  const flying: Rect = {
    x: fx - fw / 2,
    y: fy - fh / 2,
    w: fw,
    h: fh,
    r: lerp(g.card.r, side * 0.14, pf),
    o: 1 - prog(t, T.arrive - 0.02, T.land, easeIn),
    rot: lerp(0, 6, Math.sin(pf * Math.PI)),
  };
  // 後面那張往前補上；再後面一張浮出來
  const up = prog(t, T.flyStart + 0.18, T.flyStart + 0.78, easeOut);
  const next = mix(back, front, up);
  const newBack = { ...back, o: back.o * prog(t, T.advStart, T.advStart + 0.5, easeOut) };

  const litO = prog(t, T.tap, T.litIn, easeOut) * (1 - prog(t, T.litOut, T.litOutEnd, easeInOut));
  const ringP = prog(t, T.tap - 0.02, T.ringEnd);
  const ringO = interpolate(ringP, [0, 0.15, 0.6, 1], [0, 0.95, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const ringR = scene.ts * lerp(0.36, 0.3, prog(t, T.tap, T.tap + 0.12, easeOut)) * (1 + 0.18 * prog(t, T.tap + 0.15, T.ringEnd));
  const rw = Math.max(3, ringR * 0.1);
  const inner = (rc: Rect): Rect => ({ ...rc, x: rc.x - g.clip.x, y: rc.y - g.clip.y });
  const cardShadow = `0 ${g.card.w * 0.01}px ${g.card.w * 0.03}px rgba(42,55,68,.14)`;

  return (
    <AbsoluteFill>
      <Img src={staticFile(scene.plate)} style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%' }} />
      <div style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', opacity: 0 }}>
        {scene.items.map((c) => (
          <React.Fragment key={c.photo}>
            <Img src={staticFile(c.photo)} style={{ width: 1, height: 1 }} />
            <Img src={staticFile(c.lit.src)} style={{ width: 1, height: 1 }} />
          </React.Fragment>
        ))}
      </div>
      {/* 螢幕裡的卡片（裁在螢幕到相簿軌上緣之內） */}
      <div
        style={{
          position: 'absolute',
          left: g.clip.x,
          top: g.clip.y,
          width: g.clip.w,
          height: g.clip.h,
          overflow: 'hidden',
          borderTopLeftRadius: g.clip.r,
          borderTopRightRadius: g.clip.r,
          zIndex: 4,
        }}
      >
        {t >= T.advStart ? <Card src={item(2).photo} pos={item(2).pos} rc={inner(newBack)} z={1} shadow="none" /> : null}
        <Card
          src={item(1).photo}
          pos={item(1).pos}
          rc={inner(t < T.flyStart ? back : next)}
          z={2}
          shadow={cardShadow}
          icons={{ o: prog(t, T.flyStart + 0.6, T.flyStart + 0.9), g: g.icon }}
        />
        {t < T.flyStart ? (
          <Card src={target.photo} pos={target.pos} rc={inner(front)} z={3} shadow={cardShadow} icons={{ o: 1, g: g.icon }} />
        ) : null}
      </div>
      {litO > 0 ? (
        <Img
          src={staticFile(target.lit.src)}
          style={{ position: 'absolute', left: target.lit.x, top: target.lit.y, width: target.lit.w, height: target.lit.h, opacity: litO, zIndex: 5 }}
        />
      ) : null}
      {ringO > 0 ? (
        <div
          style={{
            position: 'absolute',
            left: target.tx - ringR,
            top: target.ty - ringR,
            width: ringR * 2,
            height: ringR * 2,
            borderRadius: '50%',
            zIndex: 30,
            opacity: ringO,
            background: 'rgba(255,255,255,.34)',
            boxShadow: `inset 0 0 0 ${rw}px rgba(255,255,255,.95), inset 0 0 0 ${rw * 1.45}px rgba(27,37,48,.28), 0 1px ${rw}px rgba(27,37,48,.25)`,
          }}
        />
      ) : null}
      {t >= T.flyStart && t < T.land ? <Card src={target.photo} pos={target.pos} rc={flying} z={25} shadow={scene.shadow} /> : null}
    </AbsoluteFill>
  );
};

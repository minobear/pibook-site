import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { PhoneClip, PhoneFrame, phoneGeometry } from './Phone';
import { DizzyText, PlaneArc, SighEmoji, StorageAlert } from './Flourish';
import { BADGES_BY_VARIANT, StoreBadge } from './StoreBadge';
import { CLIPS } from './clips';
import { CANVAS, GOLD, INK, NIGHT, NIGHT_INK, NIGHT_SOFT, SANS, SERIF } from './tokens';
import { Caption, Seg, Variant, storyboard } from './storyboard';

export const FPS = 30;

const frames = (sec: number) => Math.round(sec * FPS);

export const totalFrames = (variant: Variant) => storyboard(variant).reduce((n, s) => n + frames(s.dur), 0);

/**
 * 版位（以 1920 高為基準）。
 * v2.2（使用者第三輪）：字卡**永遠出現在同一個位置** —— 手機正下方的字幕帶。節奏快，觀眾的眼睛會停在
 * 字幕出現的地方；位置一換就來不及看。字幕帶在手機外面，所以也不會蓋到任何 App 畫面。
 * 頂部只留一行小小的品牌字標。
 */
const layout = (height: number) => {
  const u = height / 1920;
  // v3：字卡搬進手機畫面，下方原本的字幕帶空出來 → 手機放大（1524 → 1640）
  return { u, brandY: 84 * u, phoneTop: 156 * u, phoneH: 1640 * u };
};

/** 素材時間 → 段內時間（秒） */
const toLocal = (s: Seg, t: number) => (t - (s.from ?? 0)) / (s.rate ?? 1);

/** 頂部的品牌字標：App 圖示＋拍簿＋PIBOOK。小、安靜，不搶操作畫面。 */
const BrandMark: React.FC<{ night: number }> = ({ night }) => {
  const { height, width } = useVideoConfig();
  const u = height / 1920;
  const ink = night > 0.5 ? NIGHT_INK : INK;
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        width,
        top: layout(height).brandY,
        transform: 'translateY(-50%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16 * u,
      }}
    >
      <Img src={staticFile('app_icon.png')} style={{ width: 58 * u, height: 58 * u, borderRadius: 14 * u }} />
      <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 42 * u, color: ink, letterSpacing: '.06em' }}>拍簿</div>
      <div
        style={{
          fontFamily: SANS,
          fontWeight: 700,
          fontSize: 19 * u,
          letterSpacing: '.34em',
          color: night > 0.5 ? GOLD : '#C75F4E',
          marginTop: 6 * u,
        }}
      >
        PIBOOK
      </div>
    </div>
  );
};

/**
 * 字卡：每一張都出現在同一個位置，在動作前一刻浮出、8 個字以內。
 * v3（2026-10-06 使用者）：從手機下方的字幕帶搬到**手機畫面上的中下方**（螢幕高度 72%）——
 * 看操作的同時就瞄得到字。72% 是逐段比過畫面挑的（導演腳本 §1.0 V1）。
 * 夜色段（回憶）用米白卡，其餘用深色卡。純色、不發光。
 */
export const CAPTION_AT = 0.72;

const CaptionCard: React.FC<{
  c: Caption;
  t: number;
  dur: number;
  night: boolean;
  screenW: number;
  screenH: number;
  /** 接著上一段的畫面：段落開始前就在的字卡直接在，不重新冒出來 */
  cont?: boolean;
}> = ({ c, t, dur, night, screenW, screenH, cont }) => {
  const { fps, height } = useVideoConfig();
  const u = height / 1920;
  const t1 = Math.min(c.t1, dur);
  if (t < c.t0 || t > t1) return null;
  const inP =
    cont && c.t0 < 0
      ? 1
      : spring({ frame: Math.round((t - c.t0) * fps), fps, config: { damping: 15, mass: 0.45 }, durationInFrames: 9 });
  // 段落裡換卡時淡出；段落最後一張留到硬切
  const outP = c.t1 < dur ? interpolate(t, [t1 - 0.14, t1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) : 0;
  const fg = night ? INK : '#FFFFFF';
  const hl = night ? '#C75F4E' : GOLD;
  const parts = c.hl && c.text.includes(c.hl) ? c.text.split(c.hl) : null;
  return (
    <div
      style={{
        position: 'absolute',
        left: screenW / 2,
        top: screenH * (c.y ?? CAPTION_AT),
        zIndex: 20,
        transform: `translate(-50%, -50%) translateY(${interpolate(inP, [0, 1], [16 * u, 0]) - outP * 8 * u}px) scale(${interpolate(inP, [0, 1], [0.92, 1])})`,
        opacity: Math.min(1, inP * 1.4) * (1 - outP),
        whiteSpace: 'nowrap',
        fontFamily: SANS,
        fontWeight: 700,
        fontSize: 46 * u,
        lineHeight: 1,
        letterSpacing: '.05em',
        color: fg,
        // 字幕底要跟「深色照片」分得開（2026-10-07 使用者：相似照片那段的字幕跟後面的照片混在一起）：
        // 幾乎不透明、外圈一道細亮線把輪廓描出來（亮的 App 介面上看不見它，只在深色照片上起作用），
        // 下方的陰影加深一點。不加任何發光。
        background: night ? 'rgba(251,247,240,.97)' : 'rgba(24,32,41,.97)',
        padding: `${20 * u}px ${36 * u}px`,
        borderRadius: 999,
        boxShadow: [
          night ? `0 0 0 ${1.5 * u}px rgba(27,36,46,.10)` : `0 0 0 ${1.5 * u}px rgba(255,255,255,.30)`,
          `0 ${12 * u}px ${30 * u}px -${8 * u}px rgba(10,14,20,.55)`,
        ].join(', '),
      }}
    >
      {parts ? (
        <>
          {parts[0]}
          <span style={{ color: hl }}>{c.hl}</span>
          {parts[1]}
        </>
      ) : (
        c.text
      )}
    </div>
  );
};

/** 一段的字幕（畫在手機螢幕上、不跟著運鏡縮放；時間換算成段內秒數）。 */
const SegCaptions: React.FC<{ seg: Seg; screenW: number; screenH: number }> = ({ seg, screenW, screenH }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  return (
    <>
      {(seg.captions ?? []).map((c, i) => (
        <CaptionCard
          key={i}
          c={{ ...c, t0: toLocal(seg, c.t0), t1: toLocal(seg, c.t1) }}
          t={t}
          dur={seg.dur}
          cont={seg.cont}
          night={seg.tone === 'night'}
          screenW={screenW}
          screenH={screenH}
        />
      ))}
    </>
  );
};

/** 開場：手機畫面上壓一層暗幕，痛點的大字在畫面正中央（沒有操作要看，字就是主角）。 */
const HookOverlay: React.FC<{ seg: Seg; screenW: number; durationInFrames: number }> = ({ seg, screenW, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const u = height / 1920;
  const scrim = interpolate(frame, [0, 4, durationInFrames - 4, durationInFrames], [0.35, 0.6, 0.6, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const lines = seg.hook?.lines ?? [];
  const longest = Math.max(...lines.map((l) => Array.from(l).length));
  const size = Math.min(112 * u, (screenW * 0.86) / longest);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: `rgba(16,22,30,${scrim})` }} />
      {seg.hook?.storage !== undefined ? (
        <AbsoluteFill
          style={{
            alignItems: 'center',
            paddingTop: 150 * u,
            opacity: interpolate(frame, [durationInFrames - 5, durationInFrames], [1, 0], { extrapolateLeft: 'clamp' }),
          }}
        >
          <StorageAlert t={frame / fps} at={seg.hook.storage} width={screenW * 0.8} u={u} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
        {lines.map((l, i) => {
          const s = spring({ frame: frame - 2 - i * 5, fps, config: { damping: 200, mass: 0.5 }, durationInFrames: 12 });
          const parts = seg.hook?.hl && l.includes(seg.hook.hl) ? l.split(seg.hook.hl) : null;
          const dizzy = seg.hook?.dizzy && l.includes(seg.hook.dizzy) ? l.split(seg.hook.dizzy) : null;
          const out = interpolate(frame, [durationInFrames - 5, durationInFrames], [1, 0], { extrapolateLeft: 'clamp' });
          return (
            // 字由下往上滑進來時要裁切；滑到位之後放開（「爆滿」會晃出原本的框）
            <div key={i} style={{ overflow: s < 0.999 ? 'hidden' : 'visible', padding: `${4 * u}px ${16 * u}px` }}>
              <div
                style={{
                  fontFamily: SERIF,
                  fontWeight: 700,
                  fontSize: size,
                  lineHeight: 1.22,
                  letterSpacing: '.03em',
                  color: '#FFFFFF',
                  textAlign: 'center',
                  whiteSpace: 'nowrap',
                  opacity: out,
                  transform: `translateY(${interpolate(s, [0, 1], [size * 1.1, 0])}px)`,
                }}
              >
                {dizzy ? (
                  <>
                    {dizzy[0]}
                    <DizzyText text={seg.hook!.dizzy!} t={frame / fps} at={0.35} size={size} />
                    {dizzy[1]}
                  </>
                ) : parts ? (
                  <>
                    {parts[0]}
                    <span style={{ color: '#F4A291' }}>{seg.hook?.hl}</span>
                    {parts[1]}
                  </>
                ) : (
                  l
                )}
              </div>
            </div>
          );
        })}
        {seg.hook?.sigh !== undefined ? (
          <div
            style={{
              marginTop: 36 * u,
              opacity: interpolate(frame, [durationInFrames - 5, durationInFrames], [1, 0], { extrapolateLeft: 'clamp' }),
            }}
          >
            <SighEmoji t={frame / fps} at={seg.hook.sigh} size={190 * u} speed={1.5} />
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** 結尾：手機往下收走，留下承諾、品牌與下載徽章（徽章依版本：見 StoreBadge.tsx）。 */
const EndCard: React.FC<{ seg: Seg; variant: Variant }> = ({ seg, variant }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const u = height / 1920;
  const s = (d: number) => spring({ frame: frame - d, fps, config: { damping: 200, mass: 0.5 }, durationInFrames: 14 });
  const icon = spring({ frame: frame - 9, fps, config: { damping: 14, mass: 0.6 } });
  const end = seg.end!;
  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
      <div style={{ transform: `translateY(${-40 * u}px)` }}>
        {end.lines.map((l, i) => (
          <div key={i} style={{ overflow: 'hidden' }}>
            <div
              style={{
                fontFamily: SERIF,
                fontWeight: 700,
                fontSize: 82 * u,
                lineHeight: 1.3,
                letterSpacing: '.03em',
                color: NIGHT_INK,
                transform: `translateY(${interpolate(s(2 + i * 3), [0, 1], [95 * u, 0])}px)`,
              }}
            >
              {l}
            </div>
          </div>
        ))}
        <div style={{ position: 'relative', marginTop: 28 * u }}>
          <div
            style={{
              fontFamily: SANS,
              fontSize: 38 * u,
              fontWeight: 700,
              color: GOLD,
              letterSpacing: '.08em',
              opacity: s(8),
              whiteSpace: 'nowrap',
            }}
          >
            {end.sub}
          </div>
          {/* v3.2（使用者）：小飛機從左到右沿弧線貼著這行字底下飛過 —— 在飛機上沒網路也能整理 */}
          <div style={{ position: 'absolute', left: '50%', top: '50%', width: 0, height: 0 }}>
            <PlaneArc t={frame / fps} at={0.35} dur={2.6} span={width * 0.56} top={66 * u} dip={30 * u} size={72 * u} />
          </div>
        </div>
        <div
          style={{
            marginTop: 120 * u,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 24 * u,
            opacity: icon,
            transform: `translateY(${interpolate(icon, [0, 1], [30 * u, 0])}px)`,
          }}
        >
          <Img
            src={staticFile('app_icon.png')}
            style={{ width: 120 * u, height: 120 * u, borderRadius: 28 * u, boxShadow: `0 ${10 * u}px ${30 * u}px rgba(0,0,0,.35)` }}
          />
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 66 * u, color: NIGHT_INK, letterSpacing: '.06em', lineHeight: 1.1 }}>
              拍簿
            </div>
            <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 23 * u, color: GOLD, letterSpacing: '.36em', marginTop: 8 * u }}>
              PIBOOK
            </div>
          </div>
        </div>
        <div
          style={{
            marginTop: 64 * u,
            display: 'flex',
            justifyContent: 'center',
            gap: 28 * u,
          }}
        >
          {(BADGES_BY_VARIANT[variant] ?? []).map((b, i) => {
            const p = spring({ frame: frame - 14 - i * 3, fps, config: { damping: 16, mass: 0.5 }, durationInFrames: 12 });
            return (
              <div key={b} style={{ opacity: p, transform: `translateY(${interpolate(p, [0, 1], [24 * u, 0])}px)` }}>
                <StoreBadge store={b} height={112 * u} />
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** 一段實機畫面（運鏡、觸控指示、標記的標籤都在裡面）。 */
const SegScreen: React.FC<{ seg: Seg; screenW: number; screenH: number; radius: number }> = ({ seg, screenW, screenH, radius }) => {
  const info = CLIPS[seg.clip ?? ''];
  if (!info) {
    return <AbsoluteFill style={{ background: '#ddd' }} />;
  }
  const moves = (seg.moves ?? []).map((m) => ({ ...m, at: toLocal(seg, m.at) }));
  const callouts = (seg.callouts ?? []).map((c) => ({ ...c, at: toLocal(seg, c.at), until: toLocal(seg, c.until) }));
  const stamps = (seg.stamps ?? []).map((s) => ({ ...s, at: toLocal(seg, s.at) }));
  const spots = (seg.spots ?? []).map((s) => ({ ...s, at: toLocal(seg, s.at), until: toLocal(seg, s.until) }));
  return (
    <AbsoluteFill>
      <PhoneClip
        clip={info.file}
        from={seg.from ?? 0}
        rate={seg.rate}
        touches={info.touches}
        moves={moves}
        callouts={callouts}
        stamps={stamps}
        spots={spots}
        until={(seg.from ?? 0) + seg.dur * (seg.rate ?? 1)}
        screenW={screenW}
        screenH={screenH}
        radius={radius}
      />
    </AbsoluteFill>
  );
};

export const AdPreview: React.FC<{ variant: Variant }> = ({ variant }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const segs = storyboard(variant);
  const { phoneTop, phoneH } = layout(height);
  const g = phoneGeometry(phoneH);

  const starts: number[] = [];
  segs.reduce((n, s) => {
    starts.push(n);
    return n + frames(s.dur);
  }, 0);
  const idx = Math.max(0, starts.filter((st) => st <= frame).length - 1);
  const cur = segs[idx];

  // 底色：換色調（奶油 ↔ 夜色）時 8 格交叉淡入
  const toneAt = (i: number) => (segs[i].tone === 'night' ? 1 : 0);
  let night = toneAt(idx);
  if (idx > 0 && toneAt(idx) !== toneAt(idx - 1)) {
    const p = interpolate(frame - starts[idx], [0, 8], [0, 1], { extrapolateRight: 'clamp' });
    night = toneAt(idx - 1) + (toneAt(idx) - toneAt(idx - 1)) * p;
  }

  // 每次切段手機輕輕一彈（落在拍點上）；結尾往下收走
  const segFrame = frame - starts[idx];
  const bump = idx > 0 && !cur.end && !cur.cont ? spring({ frame: segFrame, fps, config: { damping: 18, mass: 0.4 }, durationInFrames: 10 }) : 1;
  const phoneScale = interpolate(bump, [0, 1], [0.982, 1]);
  const endIdx = segs.findIndex((s) => s.end);
  const leave = endIdx >= 0 ? spring({ frame: frame - starts[endIdx], fps, config: { damping: 200, mass: 0.7 }, durationInFrames: 14 }) : 0;
  const phoneY = phoneTop + leave * height * 0.8;

  return (
    <AbsoluteFill style={{ background: CANVAS, overflow: 'hidden' }}>
      {/* 品牌底紋：跟商店截圖畫板同一層極淡的光暈 */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse 70% 30% at 10% -4%, rgba(232,128,110,.16), transparent 70%),' +
            'radial-gradient(ellipse 76% 34% at 96% 4%, rgba(91,122,146,.14), transparent 70%),' +
            'radial-gradient(ellipse 90% 40% at 50% 108%, rgba(169,192,210,.22), transparent 72%)',
        }}
      />
      <AbsoluteFill style={{ background: NIGHT, opacity: night }} />

      {leave < 0.5 ? (
        <div style={{ opacity: 1 - leave * 2 }}>
          <BrandMark night={night} />
        </div>
      ) : null}

      {segs.map((s, i) =>
        s.end ? (
          <Sequence key={s.key} from={starts[i]} durationInFrames={frames(s.dur)}>
            <EndCard seg={s} variant={variant} />
          </Sequence>
        ) : null,
      )}

      {leave < 0.999 ? (
        <PhoneFrame x={width / 2} y={phoneY} height={phoneH} scale={phoneScale}>
          {segs.map((s, i) =>
            s.end || !s.clip ? null : (
              <Sequence key={s.key} from={starts[i]} durationInFrames={frames(s.dur)}>
                <SegScreen seg={s} screenW={g.screenW} screenH={g.screenH} radius={g.screenR} />
                {s.hook ? <HookOverlay seg={s} screenW={g.screenW} durationInFrames={frames(s.dur)} /> : null}
                <SegCaptions seg={s} screenW={g.screenW} screenH={g.screenH} />
              </Sequence>
            ),
          )}
        </PhoneFrame>
      ) : null}

      {/* 配樂＋App 的操作音效（video/music.py 已經混好、限幅好的一軌；App Store 規定一定要有音軌） */}
      <Audio src={staticFile(`music/${variant}.wav`)} />
    </AbsoluteFill>
  );
};

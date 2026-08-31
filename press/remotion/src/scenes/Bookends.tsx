import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { C, FONT_SANS, FONT_SERIF } from '../theme';

/** 開場：品牌快速立起來 —— icon 彈進、字標裁切推出、一句話收尾。 */
export const OpenCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const unit = Math.min(width, height * 0.52);

  const icon = spring({ frame: frame - 2, fps, config: { damping: 12, mass: 0.5 } });
  const mark = spring({ frame: frame - 10, fps, config: { damping: 200 }, durationInFrames: 18 });
  const line1 = spring({ frame: frame - 18, fps, config: { damping: 200 }, durationInFrames: 20 });
  const line2 = spring({ frame: frame - 24, fps, config: { damping: 200 }, durationInFrames: 20 });

  // 兩道色帶橫掃，讓開場不是靜態的漸層底
  const band = (delay: number, color: string, top: string, h: number) => {
    const s = spring({ frame: frame - delay, fps, config: { damping: 200 }, durationInFrames: 26 });
    return (
      <div
        style={{
          position: 'absolute',
          left: 0,
          top,
          width: `${interpolate(s, [0, 1], [0, 100])}%`,
          height: h,
          background: color,
          opacity: 0.9,
        }}
      />
    );
  };

  return (
    <AbsoluteFill style={{ backgroundColor: C.cream, overflow: 'hidden' }}>
      {band(0, C.coral, '18%', Math.round(height * 0.006))}
      {band(6, C.blueDeep, '81%', Math.round(height * 0.006))}

      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
        <Img
          src={staticFile('app_icon.png')}
          style={{
            width: unit * 0.3,
            height: unit * 0.3,
            borderRadius: unit * 0.072,
            transform: `scale(${interpolate(icon, [0, 1], [0.55, 1])}) rotate(${interpolate(
              icon,
              [0, 1],
              [-9, 0],
            )}deg)`,
            opacity: icon,
            boxShadow: `0 ${unit * 0.03}px ${unit * 0.07}px -${unit * 0.02}px rgba(42,55,68,.42)`,
          }}
        />

        <div style={{ height: unit * 0.075 }} />

        <div style={{ overflow: 'hidden' }}>
          <div
            style={{
              fontFamily: FONT_SERIF,
              fontWeight: 700,
              fontSize: unit * 0.115,
              letterSpacing: '.06em',
              color: C.ink,
              transform: `translateY(${interpolate(mark, [0, 1], [70, 0])}px)`,
            }}
          >
            拍簿
          </div>
        </div>

        <div
          style={{
            fontFamily: FONT_SERIF,
            fontSize: unit * 0.042,
            letterSpacing: '.5em',
            color: C.inkSoft,
            opacity: mark,
            marginTop: unit * 0.012,
            marginLeft: '.5em',
          }}
        >
          PIBOOK
        </div>

        <div style={{ height: unit * 0.09 }} />

        {[
          { t: '盡情拍、放心錄', s: line1 },
          { t: '整理與回憶靠拍簿', s: line2 },
        ].map(({ t, s }, i) => (
          <div key={i} style={{ overflow: 'hidden', paddingBottom: unit * 0.012 }}>
            <div
              style={{
                fontFamily: FONT_SERIF,
                fontWeight: 700,
                fontSize: unit * 0.088,
                lineHeight: 1.34,
                color: i === 1 ? C.coralDeep : C.ink,
                transform: `translateY(${interpolate(s, [0, 1], [56, 0])}px)`,
                opacity: s,
              }}
            >
              {t}
            </div>
          </div>
        ))}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** 結尾：承諾 + 品牌 + 網址。深色收束，跟開場的亮底形成對照。 */
export const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const unit = Math.min(width, height * 0.52);

  const a = spring({ frame: frame - 2, fps, config: { damping: 200 }, durationInFrames: 20 });
  const b = spring({ frame: frame - 10, fps, config: { damping: 200 }, durationInFrames: 20 });
  const c = spring({ frame: frame - 20, fps, config: { damping: 200 }, durationInFrames: 22 });

  return (
    <AbsoluteFill style={{ backgroundColor: C.night, overflow: 'hidden' }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 70% 30% at 78% 10%, rgba(246,196,83,.20), transparent 70%),
                       radial-gradient(ellipse 76% 34% at 16% 92%, rgba(232,128,110,.24), transparent 72%)`,
        }}
      />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
        {[
          { t: '照片', s: a, color: '#F4F1EA' },
          { t: '不離開你的手機', s: b, color: C.gold },
        ].map(({ t, s, color }, i) => (
          <div key={i} style={{ overflow: 'hidden', paddingBottom: unit * 0.014 }}>
            <div
              style={{
                fontFamily: FONT_SERIF,
                fontWeight: 700,
                fontSize: unit * 0.125,
                lineHeight: 1.3,
                color,
                transform: `translateY(${interpolate(s, [0, 1], [70, 0])}px)`,
                opacity: s,
              }}
            >
              {t}
            </div>
          </div>
        ))}

        <div style={{ height: unit * 0.075 }} />

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: unit * 0.03,
            opacity: c,
            transform: `translateY(${interpolate(c, [0, 1], [26, 0])}px)`,
          }}
        >
          <Img
            src={staticFile('app_icon.png')}
            style={{ width: unit * 0.115, height: unit * 0.115, borderRadius: unit * 0.028 }}
          />
          <span
            style={{
              fontFamily: FONT_SERIF,
              fontWeight: 700,
              fontSize: unit * 0.062,
              color: '#F4F1EA',
              letterSpacing: '.04em',
            }}
          >
            拍簿
          </span>
          <span
            style={{
              fontFamily: FONT_SERIF,
              fontSize: unit * 0.036,
              letterSpacing: '.3em',
              color: 'rgba(244,241,234,.6)',
            }}
          >
            PIBOOK.APP
          </span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

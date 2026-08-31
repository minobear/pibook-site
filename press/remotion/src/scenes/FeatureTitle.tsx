import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Accent, FONT_SANS, FONT_SERIF } from '../theme';

/**
 * 功能標題卡：滿版純色 + 大字，每個字一組彈簧、依序推上來。
 *
 * 為什麼不把字壓在實機畫面上（舊版做法）：字壓在畫面上會同時搶走兩件事的注意力，
 * 而且商店預覽的觀看情境是「一邊滑一邊瞄」—— 先用一張只有字的卡把這一段要講的
 * 事講完，再讓畫面自己說話，資訊量反而更清楚。
 */
export const FeatureTitle: React.FC<{
  index: string;
  kicker: string;
  lines: string[];
  highlight?: string;
  accent: Accent;
}> = ({ index, kicker, lines, highlight, accent }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const unit = Math.min(width, height * 0.52);

  // 字級照最長那一行反推，保證不會被畫布切掉。
  // （CJK 一個字約等於 1em，英文字母約 0.55em —— 兩種尺寸的畫布寬度差很多，
  //  寫死字級一定會在窄的那邊爆出去，商店預覽被切字是致命的。）
  const padX = unit * 0.11;
  const availW = width - padX * 2;
  const widthOf = (t: string) =>
    Array.from(t).reduce((n, ch) => n + (/[一-鿿　-〿]/.test(ch) ? 1 : 0.56), 0);
  const longest = Math.max(...lines.map(widthOf));
  const titleSize = Math.min(unit * 0.155, (availW / longest) * 0.98);

  const line = (text: string, i: number) => {
    const s = spring({
      frame: frame - 1 - i * 4,
      fps,
      config: { damping: 200, mass: 0.55 },
      durationInFrames: 15,
    });
    const y = interpolate(s, [0, 1], [58, 0]);
    const clip = interpolate(s, [0, 1], [100, 0]);
    return (
      <div key={i} style={{ overflow: 'hidden', paddingBottom: unit * 0.018 }}>
        <div
          style={{
            transform: `translateY(${y}px)`,
            opacity: s,
            clipPath: `inset(0 0 ${clip}% 0)`,
            fontFamily: FONT_SERIF,
            fontWeight: 700,
            fontSize: titleSize,
            lineHeight: 1.28,
            letterSpacing: '.01em',
            color: accent.fg,
            whiteSpace: 'nowrap',
          }}
        >
          {highlight && text.includes(highlight) ? (
            <>
              {text.split(highlight)[0]}
              <span style={{ color: accent.hl }}>{highlight}</span>
              {text.split(highlight)[1]}
            </>
          ) : (
            text
          )}
        </div>
      </div>
    );
  };

  const kick = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 14 });
  const rule = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 16 });

  return (
    <AbsoluteFill style={{ backgroundColor: 'transparent' }}>
      <AbsoluteFill style={{ backgroundColor: accent.bg }} />
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          padding: `0 ${padX}px`,
        }}
      >
        {/* 編號＋分類：小、克制，讓大字獨佔畫面重量 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: unit * 0.035,
            marginBottom: unit * 0.055,
            opacity: kick,
            transform: `translateY(${interpolate(kick, [0, 1], [22, 0])}px)`,
          }}
        >
          <span
            style={{
              fontFamily: FONT_SERIF,
              fontWeight: 700,
              fontSize: unit * 0.042,
              letterSpacing: '.18em',
              color: accent.hl,
            }}
          >
            {index}
          </span>
          <span
            style={{
              width: interpolate(rule, [0, 1], [0, unit * 0.075]),
              height: 2,
              background: accent.dim,
              borderRadius: 2,
            }}
          />
          <span
            style={{
              fontFamily: FONT_SANS,
              fontWeight: 700,
              fontSize: unit * 0.04,
              letterSpacing: '.28em',
              color: accent.dim,
            }}
          >
            {kicker}
          </span>
        </div>

        {lines.map(line)}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

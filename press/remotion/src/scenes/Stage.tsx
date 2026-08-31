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
 * 實機畫面舞台。
 *
 * ⚠️ 這裡刻意**依高度等比縮放、絕不裁切**：舊版的 1080×1920 是拿 886×1920 直接
 * 拉寬再裁，上下少掉一大塊（使用者回報）。手機畫面本來就比 9:16 更長，
 * 想「滿版」就一定會犧牲內容 —— 所以改成完整放進畫面、兩側留底色，
 * 兩種輸出尺寸各自算一次，誰都不會被切到。
 */
export const Stage: React.FC<{
  clip: string;
  /** 從原始錄影的第幾秒開始 */
  startFrom: number;
  accent: Accent;
  /** 進場方向：由下推入或由右推入，讓連續段落不要每次都一樣 */
  from?: 'bottom' | 'right';
  /** 輕微推近，給畫面一點呼吸與速度感 */
  punchIn?: boolean;
  caption?: string;
}> = ({ clip, startFrom, accent, from = 'bottom', punchIn = true, caption }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 200, mass: 0.7 },
    durationInFrames: 18,
  });

  // 畫面完整放進去：以高度為準，寬度自然變窄，兩側是底色
  const margin = Math.round(height * 0.055);
  const maxH = height - margin * 2;
  const maxW = width - margin * 2;
  const scale = Math.min(maxH / SRC_H, maxW / SRC_W);
  const w = SRC_W * scale;
  const h = SRC_H * scale;

  const dx = from === 'right' ? interpolate(enter, [0, 1], [width * 0.28, 0]) : 0;
  const dy = from === 'bottom' ? interpolate(enter, [0, 1], [height * 0.16, 0]) : 0;
  const grow = interpolate(enter, [0, 1], [0.94, 1]);
  const punch = punchIn
    ? interpolate(frame, [0, durationInFrames], [1, 1.045], { extrapolateRight: 'clamp' })
    : 1;

  return (
    <AbsoluteFill style={{ backgroundColor: accent.stageBg }}>
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div
          style={{
            width: w,
            height: h,
            borderRadius: Math.round(w * 0.062),
            overflow: 'hidden',
            transform: `translate(${dx}px, ${dy}px) scale(${grow * punch})`,
            opacity: enter,
            boxShadow: `0 ${h * 0.03}px ${h * 0.075}px -${h * 0.028}px rgba(18,26,34,.42)`,
            backgroundColor: '#000',
          }}
        >
          <OffthreadVideo
            src={staticFile(clip)}
            startFrom={Math.round(startFrom * fps)}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            muted
          />
        </div>
      </AbsoluteFill>

      {caption ? (
        <AbsoluteFill
          style={{
            alignItems: 'center',
            justifyContent: 'flex-end',
            paddingBottom: Math.round(height * 0.018),
          }}
        >
          <div
            style={{
              fontFamily: FONT_SANS,
              fontWeight: 700,
              fontSize: Math.round(Math.min(width, height * 0.52) * 0.036),
              letterSpacing: '.22em',
              color: accent.stageFg,
              opacity: interpolate(frame, [6, 16], [0, 0.62], { extrapolateRight: 'clamp' }),
            }}
          >
            {caption}
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

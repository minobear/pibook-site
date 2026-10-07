import React from 'react';
import { Composition } from 'remotion';
import { CYCLE_SEC, CreativeLoop, Scene } from './CreativeLoop';

/**
 * | id             | 尺寸       | 給誰 |
 * |----------------|-----------|------|
 * | CreativeHeader | 3840×1646 | 產品頁標題（21:9，Apple 規定 3840×1646、30 或 60fps、5–30 秒） |
 * | CreativeSearch | 3240×2160 | 搜尋結果（3:2，Apple 收 1920×1280 到 3840×2560）。不用最大的 3840×2560：
 * |                |           | 它超過 H.264 level 5.2 的畫面上限（9,437,184 像素），不少解碼器直接拒收 |
 *
 * 60fps：照片落進格子那 0.4 秒在 30fps 只有 12 格，看得出一格一格。
 * 長度＝照片張數 × 一張 3 秒（六張＝18 秒），剛好回到起點，循環播放沒有接縫。
 * 場景（底圖、亮格、排隊路線）由 site/press/creative/make_creative.py --video 產生，以 --props 傳進來。
 */
export const FPS = 60;

const empty: Scene = {
  placement: 'header',
  loc: 'zh-Hant',
  zoom: 2,
  plate: 'creative/plates/header_zh-Hant.png',
  ts: 208,
  hero: { x: 2400, y: 640, size: 300, rot: -9 },
  path: { x0: 1690, y0: 40, qx: 2316, qy: 80 },
  slots: [
    { q: 0.68, scale: 0.62, rot: -4 },
    { q: 0.35, scale: 0.42, rot: 8 },
  ],
  items: [],
  shadow: 'none',
};

const duration = (scene: Scene) => Math.round(Math.max(1, scene.items.length) * CYCLE_SEC * FPS);

export const CreativeRoot: React.FC = () => (
  <>
    <Composition
      id="CreativeHeader"
      component={CreativeLoop}
      defaultProps={{ scene: empty }}
      calculateMetadata={({ props }) => ({ durationInFrames: duration(props.scene) })}
      durationInFrames={duration(empty)}
      fps={FPS}
      width={3840}
      height={1646}
    />
    <Composition
      id="CreativeSearch"
      component={CreativeLoop}
      defaultProps={{ scene: { ...empty, placement: 'search' } }}
      calculateMetadata={({ props }) => ({ durationInFrames: duration(props.scene) })}
      durationInFrames={duration(empty)}
      fps={FPS}
      width={3240}
      height={2160}
    />
  </>
);

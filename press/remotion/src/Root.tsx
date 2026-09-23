import React from 'react';
import { Composition } from 'remotion';
import { AppPreview, totalFrames } from './AppPreview';

const FPS = 30;

/**
 * 四個輸出，兩件事在變：**尺寸**與**長度**。
 *
 * 尺寸：886×1920（App Store iPhone 6.9"）與 1080×1920（Play / YouTube）長寬比不同
 * （0.461 vs 0.5625），所以各自渲染一次，**不是**把其中一支裁出另一支 ——
 * 裁就是上下少一大塊（舊版就是這樣做的）。
 *
 * 長度：Apple 規定 App Preview 必須落在 15–30 秒，Play 的宣傳影片是 YouTube 連結、
 * 沒有上限。以前為了同一支影片同時滿足兩邊，整支被壓得太趕（開場字卡不到一秒就切走）。
 * 現在 `long` 照內容本來的節奏走，`short` 只給 App Store 用。
 */
export const RemotionRoot: React.FC = () => {
  const long = totalFrames('long');
  const short = totalFrames('short');
  return (
    <>
      {/* App Store：必須 ≤30 秒 */}
      <Composition
        id="AppPreviewIOS"
        component={AppPreview}
        defaultProps={{ variant: 'short' as const, statusBar: 'ios' as const }}
        durationInFrames={short}
        fps={FPS}
        width={886}
        height={1920}
      />
      {/* Google Play / YouTube：沒有長度上限，用完整節奏 */}
      <Composition
        id="AppPreviewPlay"
        component={AppPreview}
        defaultProps={{ variant: 'long' as const }}
        durationInFrames={long}
        fps={FPS}
        width={1080}
        height={1920}
      />
      {/* 需要時也能出「短版的 1080」與「長版的 886」 */}
      <Composition
        id="AppPreviewPlayShort"
        component={AppPreview}
        defaultProps={{ variant: 'short' as const }}
        durationInFrames={short}
        fps={FPS}
        width={1080}
        height={1920}
      />
    </>
  );
};

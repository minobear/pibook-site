import React from 'react';
import { Composition } from 'remotion';
import { AppPreview, totalFrames } from './AppPreview';

const FPS = 30;

/**
 * 兩個尺寸各自渲染一次，**不是**把其中一支裁出另一支。
 * App Store 的 iPhone 6.9" 預覽是 886×1920，Google Play / YouTube 用 1080×1920，
 * 兩者長寬比不同（0.461 vs 0.5625）；共用一支再裁，就是上下被切掉一大塊
 * （舊版就是這樣做的）。版面本身是流體的，兩邊都算得出正確的留白。
 */
export const RemotionRoot: React.FC = () => {
  const dur = totalFrames();
  return (
    <>
      <Composition
        id="AppPreviewIOS"
        component={AppPreview}
        durationInFrames={dur}
        fps={FPS}
        width={886}
        height={1920}
      />
      <Composition
        id="AppPreviewPlay"
        component={AppPreview}
        durationInFrames={dur}
        fps={FPS}
        width={1080}
        height={1920}
      />
    </>
  );
};

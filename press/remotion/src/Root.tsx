import React from 'react';
import { Composition } from 'remotion';
import { AdPreview, FPS, totalFrames } from './ad/AdPreview';

/**
 * 預覽影片 v3.3（2026-10-07）—— 兩種剪法 × 依用途放不同的下載徽章：
 *
 * | id            | 尺寸       | 長度   | 徽章 | 給誰 |
 * |---------------|-----------|--------|------|------|
 * | AppStore      | 886×1920  | 29.4s  | App Store | App Store App Preview（iPhone 6.9"；Apple 規定 15–30 秒、一定要有音軌） |
 * | Play          | 1080×1920 | 29.4s  | Google Play | Google Play 宣傳影片（上傳 YouTube、貼連結）。內容同 AppStore |
 * | Ad30          | 1080×1920 | 29.4s  | 兩個都放 | Reels／Shorts／TikTok 30 秒投放。內容同 AppStore |
 * | Ad15          | 1080×1920 | 15.0s  | 兩個都放 | 短版投放：痛點→滑卡→歸檔→壓縮→承諾 |
 *
 * v2 的長版（Long，36.6 秒全部功能）2026-10-07 退役：使用者定案「要有主線、不要功能大全」，
 * 而且修圖／分享／圖庫／已整理的相簿那幾段是 v2 的舊錄影，App 介面已經改過。
 *
 * 每個版本的段落與長度在 `ad/timeline.json`（配樂也照它合成：`site/press/video/music.py`）。
 * 兩種寬度長寬比不同（0.461 vs 0.5625），各自排版、各自渲染，不從一支裁出另一支（導演腳本 P6）。
 * 素材不含任何系統狀態列（兩個商店共用同一份，見 video/rec.py 的 CROP）。
 */
export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="AppStore"
      component={AdPreview}
      defaultProps={{ variant: 'appstore' as const }}
      durationInFrames={totalFrames('appstore')}
      fps={FPS}
      width={886}
      height={1920}
    />
    <Composition
      id="Ad30"
      component={AdPreview}
      defaultProps={{ variant: 'ad30' as const }}
      durationInFrames={totalFrames('ad30')}
      fps={FPS}
      width={1080}
      height={1920}
    />
    <Composition
      id="Play"
      component={AdPreview}
      defaultProps={{ variant: 'play' as const }}
      durationInFrames={totalFrames('play')}
      fps={FPS}
      width={1080}
      height={1920}
    />
    <Composition
      id="Ad15"
      component={AdPreview}
      defaultProps={{ variant: 'ad15' as const }}
      durationInFrames={totalFrames('ad15')}
      fps={FPS}
      width={1080}
      height={1920}
    />
  </>
);

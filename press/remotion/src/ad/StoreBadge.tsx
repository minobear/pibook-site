import React from 'react';

/**
 * 商店下載徽章。圖形與排版照官網首頁那兩顆（`site/index.html` 的 `.store-badge`，同一組 SVG 路徑）：
 * 黑底、白色細框、左邊商店圖示、右邊兩行字。height 是整顆的高（px）。
 *
 * ⚠️ 用在哪一支影片有規矩（DIRECTOR_SCRIPT.md §1.4）：App Store 的預覽影片不准出現其他平台
 * （Apple 2.3.10），Play 的宣傳影片同理只放 Google Play；兩顆都放只限投放廣告。
 */
const BADGE_FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

const AppleGlyph: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="#fff">
    <path d="M17.05 12.54c-.03-2.9 2.37-4.3 2.48-4.37-1.35-1.98-3.46-2.25-4.21-2.28-1.79-.18-3.5 1.05-4.4 1.05-.9 0-2.31-1.03-3.8-1-1.95.03-3.75 1.14-4.76 2.88-2.03 3.52-.52 8.73 1.46 11.59.97 1.4 2.12 2.97 3.63 2.91 1.46-.06 2.01-.94 3.77-.94 1.76 0 2.26.94 3.8.91 1.57-.03 2.57-1.42 3.53-2.83 1.11-1.62 1.57-3.19 1.6-3.27-.04-.02-3.07-1.18-3.1-4.65ZM14.16 4c.8-.97 1.34-2.32 1.19-3.67-1.15.05-2.55.77-3.38 1.74-.74.86-1.39 2.24-1.22 3.56 1.29.1 2.6-.65 3.41-1.63Z" />
  </svg>
);

const PlayGlyph: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 512 512">
    <defs>
      <linearGradient id="adPlayA" x1="261.2" y1="63.4" x2="53.4" y2="271.2" gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#00A0FF" />
        <stop offset=".26" stopColor="#00BEFF" />
        <stop offset=".51" stopColor="#00D2FF" />
        <stop offset="1" stopColor="#00E3FF" />
      </linearGradient>
      <linearGradient id="adPlayB" x1="504.6" y1="256" x2="82.5" y2="256" gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#FFE000" />
        <stop offset=".41" stopColor="#FFBD00" />
        <stop offset=".78" stopColor="#FFA500" />
        <stop offset="1" stopColor="#FF9C00" />
      </linearGradient>
      <linearGradient id="adPlayC" x1="437.5" y1="296.3" x2="16.9" y2="716.9" gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#FF3A44" />
        <stop offset="1" stopColor="#C31162" />
      </linearGradient>
      <linearGradient id="adPlayD" x1="46.1" y1="-112.2" x2="233.9" y2="75.6" gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#32A071" />
        <stop offset=".48" stopColor="#15CF74" />
        <stop offset="1" stopColor="#00F076" />
      </linearGradient>
    </defs>
    <path fill="url(#adPlayA)" d="M99.6 24.8C93.4 31.3 89.8 41.4 89.8 54.5v403c0 13.1 3.6 23.2 9.8 29.7l1.3 1.3 225.9-225.9v-5.3L101 23.5l-1.4 1.3z" />
    <path fill="url(#adPlayB)" d="M401.9 331.6l-75.1-75.1v-5.3l75.2-75.2 1.7 1 89.1 50.6c25.4 14.4 25.4 38.1 0 52.6l-89.1 50.6-1.8.8z" />
    <path fill="url(#adPlayC)" d="M403.7 330.8l-76.9-76.9L99.6 481.1c8.4 8.9 22.2 10 37.8 1.1l266.3-151.4" />
    <path fill="url(#adPlayD)" d="M403.7 177.1L137.4 25.8C121.8 16.9 108 18 99.6 26.9l227.2 227.1 76.9-76.9z" />
  </svg>
);

export type Store = 'apple' | 'play';

export const StoreBadge: React.FC<{ store: Store; height: number }> = ({ store, height }) => {
  const k = height / 56; // 官網的徽章高 56px，其餘尺寸照比例放大
  const apple = store === 'apple';
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 10 * k,
        height,
        padding: `0 ${18 * k}px 0 ${15 * k}px`,
        borderRadius: 10 * k,
        border: `${Math.max(1, 1.2 * k)}px solid rgba(255,255,255,.3)`,
        background: '#000',
        color: '#fff',
        boxSizing: 'border-box',
        boxShadow: `0 ${2 * k}px ${4 * k}px rgba(0,0,0,.3)`,
      }}
    >
      {apple ? <AppleGlyph size={27 * k} /> : <PlayGlyph size={24 * k} />}
      {/* 兩行字靠左對齊（官方徽章就是這樣；父層的置中會繼承進來，要明寫）。
          「GET IT ON」原本 9.2 細字＋大字距，影片壓縮後糊成一片（使用者 2026-10-07）→ 放大、半粗、字距收窄 */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'flex-start',
          textAlign: 'left',
          lineHeight: 1,
          fontFamily: BADGE_FONT,
        }}
      >
        <span
          style={{
            fontSize: (apple ? 10.4 : 10.4) * k,
            fontWeight: apple ? 400 : 600,
            letterSpacing: apple ? '.01em' : '.07em',
          }}
        >
          {apple ? 'Download on the' : 'GET IT ON'}
        </span>
        <span style={{ fontSize: 20 * k, fontWeight: 600, letterSpacing: '.005em', marginTop: 4 * k }}>
          {apple ? 'App Store' : 'Google Play'}
        </span>
      </div>
    </div>
  );
};

export const BADGES_BY_VARIANT: Record<string, Store[]> = {
  appstore: ['apple'],
  play: ['play'],
  ad30: ['apple', 'play'],
  ad15: ['apple', 'play'],
};

/**
 * 預覽影片（v2，2026-10-03）的視覺語彙 —— 直接沿用商店截圖畫板（`site/press/press.css`、
 * `site/assets/phone.css`）的顏色、字體與手機外框，影片和截圖放在同一個商店頁面上要是同一家的東西。
 *
 * 克制的規則照 App 本身（CLAUDE.md〈設計系統四句〉）：純色底、不發光、不加裝飾性漸層；
 * 唯一的漸層是畫板本來就有的那層極淡品牌光暈（與截圖一致）。
 */

export const INK = '#2A3744';
export const INK_SOFT = '#5C6A78';
export const CANVAS = '#FBF7F0';
export const NIGHT = '#16212C';
export const NIGHT_INK = '#F4F1EA';
export const NIGHT_SOFT = 'rgba(244,241,234,.74)';
export const GOLD = '#F6C453';

export const SANS = '"Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif';
export const SERIF = '"Noto Serif TC", "Songti TC", Georgia, serif';

/** 每一段的小標顏色（與截圖畫板的 kicker 同一組） */
export const ACCENT = {
  coral: '#C75F4E',
  blue: '#3F5A72',
  emerald: '#3F7D68',
  plum: '#7A5A86',
  amber: '#A8742A',
  gold: GOLD,
} as const;

export type Tone = 'cream' | 'night';

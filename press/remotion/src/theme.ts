/**
 * 影片的視覺語彙。刻意跟官網共用同一組顏色與字體，但節奏更快、對比更強 ——
 * 商店預覽是「三秒內要被看懂」的東西，不是網頁那種可以慢慢讀的版面。
 */

export const C = {
  ink: '#1B2530',
  inkSoft: '#5B6B7A',
  cream: '#FBF7F0',
  paper: '#FFFFFF',
  coral: '#E8806E',
  coralDeep: '#C75F4E',
  blue: '#5B7A92',
  blueDeep: '#3C5B7A',
  night: '#131C25',
  gold: '#F6C453',
  emerald: '#6DA890',
  emeraldDeep: '#3F7D68',
} as const;

export const FONT_SANS = '"Noto Sans TC", system-ui, -apple-system, sans-serif';
export const FONT_SERIF = '"Noto Serif TC", Georgia, serif';

/** 每個段落一個色票：標題卡用滿版底色，接著的實機畫面沿用同一族色當背景。 */
export type Accent = {
  bg: string;
  fg: string;
  dim: string;
  hl: string;
  /** 實機畫面那一段的背景（比標題卡淡一階，讓畫面本身是主角） */
  stageBg: string;
  stageFg: string;
};

export const ACCENTS: Record<string, Accent> = {
  sort: {
    bg: C.coral,
    fg: '#FFF6F2',
    dim: 'rgba(255,246,242,.72)',
    hl: C.gold,
    stageBg: '#FDEDE7',
    stageFg: C.coralDeep,
  },
  file: {
    bg: C.blueDeep,
    fg: '#F1F6FA',
    dim: 'rgba(241,246,250,.72)',
    hl: C.gold,
    stageBg: '#E9F0F5',
    stageFg: C.blueDeep,
  },
  pick: {
    bg: C.ink,
    fg: '#F4F1EA',
    dim: 'rgba(244,241,234,.7)',
    hl: C.gold,
    stageBg: '#EDEAE3',
    stageFg: C.ink,
  },
  space: {
    bg: C.emeraldDeep,
    fg: '#EFF8F4',
    dim: 'rgba(239,248,244,.74)',
    hl: C.gold,
    stageBg: '#E6F2ED',
    stageFg: C.emeraldDeep,
  },
  relive: {
    bg: C.night,
    fg: '#F4F1EA',
    dim: 'rgba(244,241,234,.7)',
    hl: C.gold,
    stageBg: '#1B2530',
    stageFg: '#F4F1EA',
  },
  library: {
    bg: C.blue,
    fg: '#F3F7FA',
    dim: 'rgba(243,247,250,.74)',
    hl: C.gold,
    stageBg: '#EAF1F6',
    stageFg: C.blueDeep,
  },
};

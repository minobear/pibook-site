import type { Callout, Move } from './Phone';
import type { Stamp } from './Flourish';
import { Tone } from './tokens';
import timeline from './timeline.json';

/**
 * 預覽影片 v2.1 的分鏡（2026-10-03 第二輪）。需求與每一拍的用意寫在 `site/press/DIRECTOR_SCRIPT.md`
 * —— 要改演示內容先改那份，再回來改這裡。每個版本放哪幾段、各多長在 `timeline.json`（配樂也讀它）。
 *
 * 使用者第三輪（v2.2）：字卡固定在手機正下方的字幕帶（不要一下上一下下）；相似照片要「左滑看一張、
 * 右滑看回來、再按保留」；相似照片接圖庫太突兀 → 順序改成 壓縮 → 圖庫 → 相似，圖庫先給一個全景再推近；
 * 結尾換成「照片不會上傳／全都留在你的手機／離線也能用」＋商店徽章。
 *
 * 使用者第二輪的指正：說明文字放在最上面，眼睛沒辦法同時看說明與下面的操作；節奏又快、字又多，
 * 根本來不及讀。所以 v2.1：
 *  - **拿掉頂部標題區**。說明改成「跟著操作出現的短字卡」：在手指動作前一刻出現、位置就在動作旁邊，
 *    一張字卡 8 個字以內 —— 讀字的那一眼就是在看操作。
 *  - 30 秒版少一段（分享移到長版），每段 2.4–3.6 秒，加速播放降到 1.3 倍以內。
 *
 * 每段用哪支素材、從第幾秒開始、播放速率寫在 `timeline.json` 的 `segments`（配樂的操作音效也要對時間）。
 *
 * **時間一律寫素材時間軸上的秒數**（字卡、運鏡、標籤都是），換算成段內時間交給 AdPreview ——
 * 同一段在不同版本換了起點或速率，字卡仍然對得上動作。素材手勢時間見 `clips.ts`。
 */

/** 字幕帶上的字卡（位置固定在手機正下方，見 AdPreview 的 layout）。 */
export type Caption = {
  t0: number;
  t1: number;
  text: string;
  hl?: string;
  /** 字卡中心在螢幕高度的哪裡（不給＝CAPTION_AT）。要指著某個東西時才用（相似照片「這一組」） */
  y?: number;
};

/** 聚光：把一塊框起來、其餘調暗（素材畫面的比例座標，跟著運鏡縮放）。時間寫素材時間軸上的秒數 */
export type Spot = { at: number; until: number; rect: [number, number, number, number]; radius?: number };

export type Seg = {
  key: string;
  dur: number;
  tone: Tone;
  clip?: string;
  from?: number;
  rate?: number;
  moves?: Move[];
  callouts?: Callout[];
  /** 照片上後製的大標記（保留／丟棄），時間寫素材時間軸上的秒數 */
  stamps?: Stamp[];
  spots?: Spot[];
  /** 接著上一段的同一個畫面（只是換素材或速度）：手機不彈、上一段帶過來的字卡不重新冒出來 */
  cont?: boolean;
  captions?: Caption[];
  /** 開場：壓在手機畫面中央的大字 */
  /** sigh＝嘆氣的表情冒出來的秒數；dizzy＝做成看得頭暈的那幾個字；storage＝儲存空間卡冒出來的秒數 */
  hook?: { lines: string[]; hl?: string; sigh?: number; dizzy?: string; storage?: number };
  /** 結尾卡 */
  end?: { lines: string[]; sub: string };
};

export type Variant = 'appstore' | 'ad30' | 'play' | 'ad15';

type Base = Omit<Seg, 'dur'>;

const SEGMENTS: Record<string, Base> = {
  hook: {
    key: 'hook',
    tone: 'cream',
    // v3.2（2026-10-07 使用者）：「整理真的好難」；字出來之後停一下，底下冒出一個在嘆氣的表情（sigh＝冒出來的秒數）
    // 儲存空間卡跟著字一起出來、一路塞到紅；「爆滿」兩個字晃得讓人頭暈（使用者 2026-10-07）
    // v3.3：開場回到 2.4 秒（使用者：停太久、配樂一直同一個音很怪）—— 儲存空間卡 0.87 秒塞滿、1.0 秒嘆氣（1.5 倍速）
    hook: { lines: ['相簿爆滿', '整理真的好難'], hl: '好難', dizzy: '爆滿', storage: 0.12, sigh: 1.0 },
  },
  swipe: {
    // 保留、保留、丟棄、保留
    key: 'swipe',
    tone: 'cream',
    // v3.1（2026-10-07）：講給觀眾聽 —— 「想留的往左滑、不要的往下滑」，不是操作說明書
    // v3.3：保留兩下、丟棄兩下（丟棄的是手震糊掉、口袋裡誤觸的照片），兩張字卡各停 1.5 秒
    captions: [
      { t0: 0.1, t1: 1.793, text: '想留的　往左滑', hl: '往左滑' },
      { t0: 1.793, t1: 9, text: '不要的　往下滑', hl: '往下滑' },
    ],
  },
  album: {
    // 奶茶 → 美食、健行自拍 → 旅行、溜滑梯 → 家人（點了自動換下一張）
    key: 'album',
    tone: 'cream',
    captions: [{ t0: 0.3, t1: 9, text: '點相簿　就歸檔', hl: '點相簿' }],
  },
  edit: {
    // 展開 → 修圖 → 自動 → 濾鏡「鮮明」→ 儲存 → 覆寫原照片 → 回到卡片
    key: 'edit',
    tone: 'cream',
    captions: [
      { t0: 0.4, t1: 1.62, text: '整理時　直接修圖', hl: '直接修圖' },
      { t0: 1.62, t1: 3.5, text: '一鍵自動　套濾鏡', hl: '一鍵自動' },
    ],
  },
  share: {
    // 展開 → 分享 → 版型左右滑：原圖 → 底片 → 署名 → 那一天
    key: 'share',
    tone: 'cream',
    captions: [
      { t0: 0.4, t1: 1.95, text: '修完　直接分享', hl: '直接分享' },
      { t0: 1.95, t1: 9, text: '左右滑　挑版型', hl: '挑版型' },
    ],
  },
  compress: {
    // 最後一張保留 → 結尾頁「約可省 21.6 MB」→ 壓縮 → 懸浮球
    key: 'compress',
    tone: 'cream',
    captions: [{ t0: 1.6, t1: 9, text: '保留的　順手壓縮', hl: '順手壓縮' }],
  },
  compress_run: {
    // 2026-10-07 使用者：「壓縮那邊能比較清楚地看見從 0% 到 100% 的過程，但不用拖太久」。
    // 懸浮球的進度是真的在壓（不吃慢動作錄影的倍率），原速素材只閃 0.3 秒、而且球很小 ——
    // 這一段改用同一支錄影的 0.35 倍速還原（r5_slow：慢動作原檔取格，不是重複格），按下「壓縮」那一刻
    // 前一刻推近到懸浮球（1.7 倍，旁邊「已加入壓縮 8 張」那一列還看得到），0% → 16% → 55% → 67% → 打勾約 0.8 秒，打勾後拉回。
    // 時間是 r5_slow 的素材時間：按下壓縮 9.865、打勾約 10.67。
    key: 'compress_run',
    tone: 'cream',
    cont: true,
    moves: [
      { at: 9.62, rect: [0.42, 0.47, 1.0, 0.66], pad: 0, dur: 10 },
      { at: 10.8, rect: [0, 0, 1, 1], dur: 8 },
    ],
    captions: [{ t0: 0, t1: 99, text: '保留的　順手壓縮', hl: '順手壓縮' }],
  },
  compress_done: {
    // v3：懸浮球打勾 → 點一下 → 「壓縮完成 21.5 MB」成果頁從懸浮球長出來、前後對比在捲
    key: 'compress_done',
    tone: 'cream',
    // 表情符號只放在情緒的點上（使用者 2026-10-07）：省回來了 🤩、一次清掉 👍、下一段回憶 ❤️、開場的嘆氣
    // y：往下挪一點，不蓋到縮圖底下「多少 → 多少」那一行（使用者 2026-10-07）
    captions: [{ t0: 1.25, t1: 9, text: '空間　省回來了 🤩', hl: '省回來了', y: 0.765 }],
  },
  similar_clean: {
    // v3：清單底部「清理 9 張」那一下 —— 手指一碰就切到成果頁（素材 0.833 秒確認單開始升起，段尾 0.83 剛好在它之前）
    key: 'similar_clean',
    tone: 'cream',
  },
  similar_done: {
    // v3：成果頁「14.6 MB 這次騰出的空間」—— 數字從 0 跳上去、落定時彩帶
    key: 'similar_done',
    tone: 'cream',
    captions: [{ t0: 2.2, t1: 9, text: '重複的　一次清掉', hl: '一次清掉' }],
  },
  similar3_list: {
    // v3.3（2026-10-07 使用者）：「相似的照片自動排成一組」要指著那一組講 —— 聚光框住第一組、其餘調暗、
    // 輕輕推近；字卡就擺在那一組正下方。段尾推回原樣，接下一段（同一支素材）點開那一組。
    key: 'similar3_list',
    tone: 'cream',
    moves: [
      { at: 0.4, rect: [0.0285, 0.18, 0.9715, 0.4], pad: 0, dur: 14 },
      { at: 1.72, rect: [0, 0, 1, 1], dur: 12 },
    ],
    spots: [{ at: 0.45, until: 2.12, rect: [0.022, 0.178, 0.978, 0.402] }],
    captions: [{ t0: 0.5, t1: 9, text: '相似的照片　自動排成一組', hl: '自動排成一組', y: 0.468 }],
  },
  similar3: {
    // v3.3：點開之後先往左看一張、往右看回來（看得出可以這樣滑著比），再標：保留（App 標星號那張）→ 丟棄 → 丟棄。
    // App 按下去就跳到下一張、鈕的顏色看不到 —— 影片裡在照片上蓋大標記（使用者選「只在影片裡加強調」）。
    key: 'similar3',
    tone: 'cream',
    captions: [
      { t0: 2.6, t1: 4.45, text: '左右滑　比一比', hl: '比一比' },
      { t0: 4.45, t1: 9, text: '留下最好的　其他刪掉', hl: '留下最好的' },
    ],
    stamps: [
      { at: 4.624, kind: 'keep' },
      { at: 5.327, kind: 'discard' },
      { at: 6.031, kind: 'discard' },
    ],
  },
  similar3_done: {
    // v3.1：標完直接切到成果頁 —— 數字從 0 跳到 17.2 MB、彩帶、改版後的分享卡（選片印樣「留下最好的」）滑進來
    key: 'similar3_done',
    tone: 'cream',
    captions: [{ t0: 1.5, t1: 9, text: '重複的　一次清掉 👍', hl: '一次清掉' }],
  },
  similar: {
    // 自動精選 → 全部（每組最美的打勾、其餘待刪）→ 點開 → 往左看一張、往右看回來 → 按「保留」
    key: 'similar',
    tone: 'cream',
    captions: [
      { t0: 0.6, t1: 2.3, text: '最美的　自動挑好', hl: '自動挑好' },
      { t0: 2.3, t1: 9, text: '比一比　再決定', hl: '比一比' },
    ],
  },
  gallery: {
    // 先給一個全景（剛整理完的圖庫）→ 推近今天那兩排，圈出兩個記號並寫上意思 → 拉回 → 點開一張 → 開始整理
    key: 'gallery',
    tone: 'cream',
    moves: [
      { at: 0.5, rect: [0.47, 0.11, 1.0, 0.285], dur: 10 },
      { at: 2.85, rect: [0, 0, 1, 1], dur: 9 },
    ],
    callouts: [
      { at: 0.85, until: 2.75, x: 0.52, y: 0.129, r: 0.024, label: '已整理', dy: 0.062 },
      { at: 1.05, until: 2.75, x: 0.951, y: 0.133, r: 0.036, label: '已加相簿', side: 'left' },
    ],
    captions: [
      { t0: 0.0, t1: 3.35, text: '整理到哪　一眼看到', hl: '一眼看到' },
      { t0: 3.35, t1: 9, text: '點開　就接著整理', hl: '接著整理' },
    ],
  },
  organised: {
    // 已整理的相簿：勾家人、旅行、美食 → 套用 → 首頁那三本變成「已完成」
    key: 'organised',
    tone: 'cream',
    captions: [
      { t0: 0.8, t1: 2.95, text: '勾選整理過的相簿', hl: '整理過的' },
      { t0: 2.95, t1: 9, text: '不必重新整理', hl: '不必' },
    ],
  },
  memory: {
    // 影片分頁：煙火播著 → 雙擊愛心 → 上滑到生日女孩
    //（素材第 1.43 秒與 4.77 秒各有一格原生影片閃黑。v3 這一段拉長到 3.6 秒、會播到 4.77 ——
    //  兩格已用 rec.fix_flashes 換成前一格（2026-10-06），verify.py 的閃黑檢查會再擋一次）
    key: 'memory',
    tone: 'night',
    // v3.1（2026-10-07 使用者）：先講這個功能在做什麼（短影音），雙擊愛心畫面上看得懂、不必再寫
    captions: [
      { t0: 1.7, t1: 3.62, text: '回憶　變成短影音', hl: '短影音' },
      { t0: 3.62, t1: 9, text: '上滑　下一段回憶 ❤️', hl: '上滑' },
    ],
  },
  end: {
    key: 'end',
    tone: 'night',
    end: { lines: ['照片不會上傳', '全都留在你的手機'], sub: '離線也能用' },
  },
};

type Entry = [string, number] | [string, number, Partial<Seg>];


type Timeline = {
  bpm: number;
  segments: Record<string, Partial<Seg>>;
  variants: Record<string, Entry[]>;
};
const TL = timeline as unknown as Timeline;

export const storyboard = (variant: Variant): Seg[] =>
  TL.variants[variant].map(([key, dur, over]) => ({ ...SEGMENTS[key], ...TL.segments[key], ...(over ?? {}), dur }));

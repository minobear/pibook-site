import { registerRoot } from 'remotion';
import { CreativeRoot } from './Root';

// App Store 創意素材（產品頁標題／搜尋結果）的影片版 —— 獨立入口，跟預覽影片（src/index.ts）分開：
//   npx remotion render src/creative/index.ts CreativeHeader out.mp4 --props=<場景 json>
// 場景由 site/press/creative/make_creative.py --motion 產生。
registerRoot(CreativeRoot);

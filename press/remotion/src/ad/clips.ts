// 由 site/press/video/rec.py export() 產生 —— 不要手改。
// 每段實機錄影：檔案、長度（秒）、錄影時記下的手勢（素材時間軸上的秒數）。
import type { Touch } from './Phone';

export type ClipInfo = { file: string; duration: number; touches: Touch[] };

const CLIPS_JSON = {
 "r1_swipe": {
  "file": "clips/v2/r1_swipe.mp4",
  "duration": 4.267,
  "touches": [
   {
    "kind": "swipe",
    "args": [
     760,
     1150,
     140,
     1190
    ],
    "b": 0.517,
    "e": 0.761
   },
   {
    "kind": "swipe",
    "args": [
     760,
     1150,
     140,
     1190
    ],
    "b": 1.214,
    "e": 1.449
   },
   {
    "kind": "swipe",
    "args": [
     540,
     950,
     560,
     1950
    ],
    "b": 1.901,
    "e": 2.164
   },
   {
    "kind": "swipe",
    "args": [
     540,
     950,
     560,
     1950
    ],
    "b": 2.615,
    "e": 2.878
   }
  ]
 },
 "r2_album": {
  "file": "clips/v2/r2_album.mp4",
  "duration": 4.167,
  "touches": [
   {
    "kind": "tap",
    "args": [
     568,
     2203
    ],
    "b": 0.515,
    "e": 0.52
   },
   {
    "kind": "tap",
    "args": [
     421,
     2203
    ],
    "b": 1.471,
    "e": 1.474
   },
   {
    "kind": "tap",
    "args": [
     274,
     2203
    ],
    "b": 2.425,
    "e": 2.428
   }
  ]
 },
 "r3_edit": {
  "file": "clips/v2/r3_edit.mp4",
  "duration": 5.767,
  "touches": [
   {
    "kind": "tap",
    "args": [
     975,
     1806
    ],
    "b": 0.56,
    "e": 0.565
   },
   {
    "kind": "tap",
    "args": [
     525,
     1483
    ],
    "b": 0.969,
    "e": 0.979
   },
   {
    "kind": "tap",
    "args": [
     126,
     1917
    ],
    "b": 1.782,
    "e": 1.787
   },
   {
    "kind": "tap",
    "args": [
     880,
     2232
    ],
    "b": 2.391,
    "e": 2.396
   },
   {
    "kind": "tap",
    "args": [
     808,
     2010
    ],
    "b": 2.85,
    "e": 2.856
   },
   {
    "kind": "tap",
    "args": [
     974,
     201
    ],
    "b": 3.609,
    "e": 3.614
   },
   {
    "kind": "tap",
    "args": [
     733,
     368
    ],
    "b": 4.017,
    "e": 4.021
   }
  ]
 },
 "r4_share": {
  "file": "clips/v2/r4_share.mp4",
  "duration": 5.3,
  "touches": [
   {
    "kind": "tap",
    "args": [
     975,
     1806
    ],
    "b": 0.537,
    "e": 0.544
   },
   {
    "kind": "tap",
    "args": [
     718,
     1368
    ],
    "b": 1.0,
    "e": 1.004
   },
   {
    "kind": "swipe",
    "args": [
     820,
     1100,
     300,
     1110
    ],
    "b": 2.108,
    "e": 2.373
   },
   {
    "kind": "swipe",
    "args": [
     820,
     1100,
     300,
     1110
    ],
    "b": 2.977,
    "e": 3.242
   },
   {
    "kind": "swipe",
    "args": [
     820,
     1100,
     300,
     1110
    ],
    "b": 3.847,
    "e": 4.113
   }
  ]
 },
 "r5_compress": {
  "file": "clips/v2/r5_compress.mp4",
  "duration": 6.033,
  "touches": [
   {
    "kind": "swipe",
    "args": [
     760,
     1150,
     140,
     1190
    ],
    "b": 0.526,
    "e": 0.769
   },
   {
    "kind": "swipe",
    "args": [
     760,
     1150,
     140,
     1190
    ],
    "b": 1.222,
    "e": 1.456
   },
   {
    "kind": "swipe",
    "args": [
     760,
     1150,
     140,
     1190
    ],
    "b": 1.908,
    "e": 2.151
   },
   {
    "kind": "tap",
    "args": [
     922,
     1470
    ],
    "b": 3.453,
    "e": 3.455
   }
  ]
 },
 "g_gallery": {
  "file": "clips/v2/g_gallery.mp4",
  "duration": 6.5,
  "touches": [
   {
    "kind": "tap",
    "args": [
     990,
     1180
    ],
    "b": 3.62,
    "e": 3.621
   },
   {
    "kind": "tap",
    "args": [
     696,
     2203
    ],
    "b": 4.522,
    "e": 4.524
   }
  ]
 },
 "o_organised": {
  "file": "clips/v2/o_organised.mp4",
  "duration": 4.967,
  "touches": [
   {
    "kind": "tap",
    "args": [
     900,
     1158
    ],
    "b": 0.468,
    "e": 0.475
   },
   {
    "kind": "tap",
    "args": [
     540,
     666
    ],
    "b": 1.48,
    "e": 1.487
   },
   {
    "kind": "tap",
    "args": [
     540,
     823
    ],
    "b": 1.843,
    "e": 1.848
   },
   {
    "kind": "tap",
    "args": [
     540,
     981
    ],
    "b": 2.203,
    "e": 2.208
   },
   {
    "kind": "tap",
    "args": [
     540,
     2082
    ],
    "b": 2.812,
    "e": 2.817
   }
  ]
 },
 "m_memory": {
  "file": "clips/v2/m_memory.mp4",
  "duration": 5.967,
  "touches": [
   {
    "kind": "swipe",
    "args": [
     540,
     1750,
     540,
     600
    ],
    "b": 1.408,
    "e": 1.643
   },
   {
    "kind": "dtap",
    "args": [
     540,
     1100
    ],
    "b": 2.895,
    "e": 2.918
   },
   {
    "kind": "swipe",
    "args": [
     540,
     1750,
     540,
     600
    ],
    "b": 3.92,
    "e": 4.159
   }
  ]
 },
 "s_similar": {
  "file": "clips/v2/s_similar.mp4",
  "duration": 6.367,
  "touches": [
   {
    "kind": "tap",
    "args": [
     200,
     2090
    ],
    "b": 0.809,
    "e": 0.81
   },
   {
    "kind": "tap",
    "args": [
     120,
     1940
    ],
    "b": 1.261,
    "e": 1.262
   },
   {
    "kind": "tap",
    "args": [
     536,
     800
    ],
    "b": 2.363,
    "e": 2.364
   },
   {
    "kind": "swipe",
    "args": [
     860,
     1100,
     220,
     1100
    ],
    "b": 3.114,
    "e": 3.345
   },
   {
    "kind": "swipe",
    "args": [
     220,
     1100,
     860,
     1100
    ],
    "b": 3.996,
    "e": 4.228
   },
   {
    "kind": "tap",
    "args": [
     613,
     1993
    ],
    "b": 4.779,
    "e": 4.781
   }
  ]
 },
 "h_scroll": {
  "file": "clips/v2/h_scroll.mp4",
  "duration": 5.533,
  "touches": [
   {
    "kind": "swipe",
    "args": [
     540,
     2060,
     540,
     330
    ],
    "b": 0.683,
    "e": 2.857
   }
  ]
 },
 "s2_done": {
  "file": "clips/v2/s2_done.mp4",
  "duration": 7.033,
  "touches": [
   {
    "kind": "tap",
    "args": [
     877,
     2090
    ],
    "b": 0.813,
    "e": 0.815
   },
   {
    "kind": "tap",
    "args": [
     779,
     2253
    ],
    "b": 2.017,
    "e": 2.02
   }
  ]
 },
 "r6_done": {
  "file": "clips/v2/r6_done.mp4",
  "duration": 5.133,
  "touches": [
   {
    "kind": "tap",
    "args": [
     975,
     1380
    ],
    "b": 0.921,
    "e": 0.929
   }
  ]
 },
 "s3_similar": {
  "file": "clips/v2/s3_similar.mp4",
  "duration": 7.5,
  "touches": [
   {
    "kind": "tap",
    "args": [
     203,
     793
    ],
    "b": 2.51,
    "e": 2.512
   },
   {
    "kind": "swipe",
    "args": [
     860,
     1100,
     220,
     1100
    ],
    "b": 2.984,
    "e": 3.215
   },
   {
    "kind": "swipe",
    "args": [
     220,
     1100,
     860,
     1100
    ],
    "b": 3.686,
    "e": 3.918
   },
   {
    "kind": "tap",
    "args": [
     613,
     1993
    ],
    "b": 4.62,
    "e": 4.624
   },
   {
    "kind": "tap",
    "args": [
     466,
     1993
    ],
    "b": 5.325,
    "e": 5.327
   },
   {
    "kind": "tap",
    "args": [
     466,
     1993
    ],
    "b": 6.029,
    "e": 6.031
   }
  ]
 },
 "s3_done": {
  "file": "clips/v2/s3_done.mp4",
  "duration": 7.433,
  "touches": [
   {
    "kind": "tap",
    "args": [
     779,
     2253
    ],
    "b": 0.846,
    "e": 0.848
   }
  ]
 },
 "h_dense": {
  "file": "clips/v2/h_dense.mp4",
  "duration": 10.733,
  "touches": [
   {
    "kind": "swipe",
    "args": [
     540,
     2060,
     540,
     330
    ],
    "b": 1.042,
    "e": 4.003
   }
  ]
 },
 "r5_slow": {
  "file": "clips/v2/r5_slow.mp4",
  "duration": 17.267,
  "touches": [
   {
    "kind": "swipe",
    "args": [
     760,
     1150,
     140,
     1190
    ],
    "b": 1.503,
    "e": 2.198
   },
   {
    "kind": "swipe",
    "args": [
     760,
     1150,
     140,
     1190
    ],
    "b": 3.492,
    "e": 4.159
   },
   {
    "kind": "swipe",
    "args": [
     760,
     1150,
     140,
     1190
    ],
    "b": 5.45,
    "e": 6.146
   },
   {
    "kind": "tap",
    "args": [
     922,
     1470
    ],
    "b": 9.865,
    "e": 9.87
   }
  ]
 }
};

export const CLIPS = CLIPS_JSON as Record<string, ClipInfo>;

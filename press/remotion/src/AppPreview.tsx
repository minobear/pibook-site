import React from 'react';
import { AbsoluteFill, Audio, staticFile } from 'remotion';
import { TransitionSeries, springTiming, linearTiming } from '@remotion/transitions';
import { slide } from '@remotion/transitions/slide';
import { wipe } from '@remotion/transitions/wipe';
import { fade } from '@remotion/transitions/fade';
import { FeatureTitle } from './scenes/FeatureTitle';
import { Stage } from './scenes/Stage';
import { OpenCard, EndCard } from './scenes/Bookends';
import { ACCENTS } from './theme';

/**
 * 一段功能 ＝ 一張滿版標題卡 ＋ 一段實機錄影。
 * 標題卡負責講「這段在幹嘛」，錄影負責證明「真的是這樣」。
 */
type Beat = {
  key: keyof typeof ACCENTS;
  index: string;
  kicker: string;
  lines: string[];
  highlight?: string;
  clip: string;
  /** 從錄影的第幾秒開始播（實機操作的甜蜜點，逐段對過） */
  startFrom: number;
  stageFrames: number;
  titleFrames?: number;
  from?: 'bottom' | 'right';
};

export const BEATS: Beat[] = [
  {
    key: 'sort',
    index: '01',
    kicker: 'ORGANIZE',
    lines: ['滑一下', '就整理好一張'],
    highlight: '一張',
    clip: 'clips/review.mp4',
    startFrom: 0.3,
    stageFrames: 114,
    from: 'bottom',
  },
  {
    key: 'file',
    index: '02',
    kicker: 'FILING',
    lines: ['點一下相簿', '照片就收進去'],
    highlight: '收進去',
    clip: 'clips/album.mp4',
    startFrom: 2.4,
    stageFrames: 108,
    from: 'right',
  },
  {
    key: 'pick',
    index: '03',
    kicker: 'BEST SHOT',
    lines: ['連拍裡最美的', '自動挑好'],
    highlight: '自動挑好',
    clip: 'clips/similar.mp4',
    startFrom: 0.4,
    stageFrames: 102,
    from: 'bottom',
  },
  {
    key: 'space',
    index: '04',
    kicker: 'FREE SPACE',
    lines: ['四部影片', '省回 2 GB'],
    highlight: '2 GB',
    clip: 'clips/compress.mp4',
    startFrom: 4.4,
    stageFrames: 96,
    from: 'right',
  },
  {
    key: 'relive',
    index: '05',
    kicker: 'MEMORIES',
    lines: ['留下的照片', '自己回來找你'],
    highlight: '自己回來',
    clip: 'clips/memory.mp4',
    startFrom: 7.2,
    stageFrames: 114,
    from: 'bottom',
  },
  {
    key: 'library',
    index: '06',
    kicker: 'LIBRARY',
    lines: ['整理過的', '一眼看得到'],
    highlight: '一眼',
    clip: 'clips/library.mp4',
    startFrom: 0.5,
    stageFrames: 96,
    from: 'right',
  },
];

const TITLE_FRAMES = 42;

export const AppPreview: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#FBF7F0' }}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={64}>
          <OpenCard />
        </TransitionSeries.Sequence>

        {BEATS.map((b, i) => {
          const a = ACCENTS[b.key];
          return (
            <React.Fragment key={b.key}>
              <TransitionSeries.Transition
                presentation={slide({ direction: 'from-bottom' })}
                timing={springTiming({ config: { damping: 200 }, durationInFrames: 12, durationRestThreshold: 0.001 })}
              />
              <TransitionSeries.Sequence durationInFrames={b.titleFrames ?? TITLE_FRAMES}>
                <FeatureTitle
                  index={b.index}
                  kicker={b.kicker}
                  lines={b.lines}
                  highlight={b.highlight}
                  accent={a}
                />
              </TransitionSeries.Sequence>

              <TransitionSeries.Transition
                presentation={wipe({ direction: 'from-bottom' })}
                timing={linearTiming({ durationInFrames: 10 })}
              />
              <TransitionSeries.Sequence durationInFrames={b.stageFrames}>
                <Stage
                  clip={b.clip}
                  startFrom={b.startFrom}
                  accent={a}
                  from={b.from}
                  caption={`${b.index} · ${b.kicker}`}
                />
              </TransitionSeries.Sequence>
            </React.Fragment>
          );
        })}

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: 12 })}
        />
        <TransitionSeries.Sequence durationInFrames={78}>
          <EndCard />
        </TransitionSeries.Sequence>
      </TransitionSeries>

      {/* App Store 規定一定要有音軌，就算全靜音。 */}
      <Audio src={staticFile('silence.wav')} />
    </AbsoluteFill>
  );
};

/** 給 Root 算總長用：把所有片段長度相加、再扣掉每個轉場重疊的格數。 */
export const totalFrames = () => {
  const scenes = 64 + BEATS.reduce((n, b) => n + (b.titleFrames ?? TITLE_FRAMES) + b.stageFrames, 0) + 78;
  const overlaps = BEATS.length * (12 + 10) + 12;
  return scenes - overlaps;
};

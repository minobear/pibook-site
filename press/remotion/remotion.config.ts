import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// 音訊：App Store 規定預覽影片一定要有音軌（就算是無聲）。
Config.setCodec('h264');
Config.setPixelFormat('yuv420p');
Config.setCrf(18);

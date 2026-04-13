import { Config } from "@remotion/cli/config";

// VOLAURA Remotion config — chromium render, transparent-safe, high-quality defaults.
Config.setVideoImageFormat("jpeg");
Config.setPixelFormat("yuv420p");
Config.setCodec("h264");
Config.setCrf(18); // 15 = lossless-ish, 18 = visually lossless, 23 = default
Config.setConcurrency(null); // auto — use all cores
Config.setChromiumOpenGlRenderer("angle");
Config.setEntryPoint("src/Root.tsx");

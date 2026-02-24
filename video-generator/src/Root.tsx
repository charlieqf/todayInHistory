import "./index.css";
import { Composition } from "remotion";
import { MyComposition } from "./Composition";
import scriptData from "./current_script.json";

// Dynamically calculate total frames from the script JSON
// This ensures the video ends exactly when the audio/scenes end — no more black screens!
const totalDuration = scriptData.scenes.reduce(
  (sum: number, scene: { durationInFrames?: number }) => sum + (scene.durationInFrames || 150),
  0
);

// We use 1080x1920 since this is targeted for shorts (Douyin/Xiaohongshu/TikTok)
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="IT-History-Today-Xerox-Alto"
        component={MyComposition}
        durationInFrames={totalDuration}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};

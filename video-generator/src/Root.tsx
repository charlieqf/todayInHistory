import "./index.css";
import { Composition } from "remotion";
import { MyComposition } from "./Composition";

// ~66 seconds video at 30 fps = 1980 frames.
// We use 1080x1920 since this is targeted for shorts (Douyin/Xiaohongshu/TikTok)
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="IT-History-Today-Xerox-Alto"
        component={MyComposition}
        durationInFrames={1980}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};

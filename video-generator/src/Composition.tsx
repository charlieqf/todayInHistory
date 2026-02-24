import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  useCurrentFrame,
  staticFile,
  interpolate,
} from "remotion";
import scriptData from "./current_script.json";

export const MyComposition = () => {
  // Accumulate frames to determine exact start time for each scene sequentially
  let runningFrame = 0;
  const scenesWithFrames = scriptData.scenes.map((scene) => {
    const startFrame = runningFrame;
    const durationFrames = scene.durationInFrames || 150;
    runningFrame += durationFrames;
    return { ...scene, startFrame, durationFrames };
  });

  // Protect against empty audioUrl in testing
  const audioSource = scriptData.audioUrl ? staticFile(scriptData.audioUrl) : null;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {audioSource && <Audio src={audioSource} />}

      {scenesWithFrames.map((scene, index) => {
        return (
          <Sequence key={index} from={scene.startFrame} durationInFrames={scene.durationFrames}>
            <SceneContent scene={scene} index={index} durationInFrames={scene.durationFrames} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SceneContent: React.FC<{ scene: any; index: number; durationInFrames: number }> = ({ scene, index, durationInFrames }) => {
  const frame = useCurrentFrame();

  // Dynamic Ken Burns effect based on odd/even scene index (since JSON doesn't specify animation anymore)
  let scale = 1;
  let translateX = 0;

  if (index % 4 === 0) {
    // zoom_in
    scale = interpolate(frame, [0, durationInFrames], [1, 1.15], { extrapolateRight: "clamp" });
  } else if (index % 4 === 1) {
    // pan_right
    scale = 1.1;
    translateX = interpolate(frame, [0, durationInFrames], [-50, 50]);
  } else if (index % 4 === 2) {
    // zoom_out
    scale = interpolate(frame, [0, durationInFrames], [1.15, 1], { extrapolateRight: "clamp" });
  } else {
    // pan_left
    scale = 1.1;
    translateX = interpolate(frame, [0, durationInFrames], [50, -50]);
  }

  // Fade in text
  const opacity = interpolate(Math.min(frame, 30), [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", justifyContent: "center", alignItems: "center" }}>
      {scene.imageUrl && (
        <Img
          src={staticFile(scene.imageUrl)}
          style={{
            minWidth: "100%",
            minHeight: "100%",
            objectFit: "cover",
            transform: `scale(${scale}) translateX(${translateX}px)`,
            filter: (scriptData as any).filterStyle || "sepia(0.3) contrast(1.1) brightness(0.9) grayscale(0.2)",
          }}
        />
      )}

      {/* Caption Overlay */}
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
          paddingBottom: "15%",
          paddingLeft: "5%",
          paddingRight: "5%",
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            padding: "20px 40px",
            borderRadius: "20px",
            color: "white",
            fontSize: "42px",
            fontFamily: "sans-serif",
            fontWeight: "bold",
            textAlign: "center",
            opacity,
            textShadow: "0 2px 10px rgba(0,0,0,0.5)",
            border: "2px solid rgba(255,255,255,0.2)"
          }}
        >
          {scene.text}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

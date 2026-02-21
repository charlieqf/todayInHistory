import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
  interpolate,
  Easing,
} from "remotion";
import scriptData from "./day1_script_xerox_alto.json";

export const MyComposition = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Audio src={staticFile("audio_track.mp3")} />

      {scriptData.scenes.map((scene, index) => {
        const startFrame = scene.timestamp_start * fps;
        const durationFrames = (scene.timestamp_end - scene.timestamp_start) * Math.round(fps);

        return (
          <Sequence key={index} from={startFrame} durationInFrames={durationFrames}>
            <SceneContent scene={scene} index={index} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SceneContent: React.FC<{ scene: any; index: number }> = ({ scene, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durationInFrames = (scene.timestamp_end - scene.timestamp_start) * fps;

  // Basic "Ken Burns" variations
  let scale = 1;
  let translateX = 0;

  if (scene.animation === "zoom_in" || scene.animation === "zoom_in_slow") {
    scale = interpolate(frame, [0, durationInFrames], [1, 1.15], {
      extrapolateRight: "clamp",
    });
  } else if (scene.animation === "zoom_out_slow") {
    scale = interpolate(frame, [0, durationInFrames], [1.15, 1], {
      extrapolateRight: "clamp",
    });
  } else if (scene.animation === "pan_right") {
    scale = 1.1;
    translateX = interpolate(frame, [0, durationInFrames], [-50, 50]);
  } else if (scene.animation === "pan_left") {
    scale = 1.1;
    translateX = interpolate(frame, [0, durationInFrames], [50, -50]);
  } else {
    // Default fallback
    scale = interpolate(frame, [0, durationInFrames], [1, 1.05]);
  }

  // Fade in text
  const opacity = interpolate(Math.min(frame, 30), [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", justifyContent: "center", alignItems: "center" }}>
      <Img
        src={staticFile(scene.image_file)}
        style={{
          minWidth: "100%",
          minHeight: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translateX(${translateX}px)`,
          // Apply a unified "vintage documentary" look to bridge AI vs Real photos
          filter: "sepia(0.3) contrast(1.1) brightness(0.9) grayscale(0.2)",
        }}
      />
      {/* Caption Overlay */}
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
          paddingBottom: "15%",
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            padding: "20px 40px",
            borderRadius: "20px",
            color: "white",
            fontSize: "48px",
            fontFamily: "sans-serif",
            fontWeight: "bold",
            textAlign: "center",
            opacity,
            textShadow: "0 2px 10px rgba(0,0,0,0.5)",
            border: "2px solid rgba(255,255,255,0.2)"
          }}
        >
          {scene.caption}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

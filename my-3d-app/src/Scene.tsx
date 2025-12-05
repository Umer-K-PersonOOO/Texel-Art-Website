import {
  Html,
  OrbitControls,
  Stats,
  useAnimations,
  useProgress,
} from "@react-three/drei";
import { Canvas, useLoader } from "@react-three/fiber";
import React, { Suspense, useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";

function Loader() {
  const { progress } = useProgress();
  return <Html center>{progress.toFixed(0)} % loaded</Html>;
}

interface ModelWithAnimationProps {
  url: string;
  onLoadEnd?: () => void;
  onError?: (err: unknown) => void;
}

function ModelWithAnimation({ url, onLoadEnd, onError }: ModelWithAnimationProps) {
  const gltf = useLoader(GLTFLoader, url);
  const modelRef = useRef<THREE.Group>(null);
  const { animations } = gltf;
  const { actions } = useAnimations(animations, modelRef);

  // console.log("Loaded GLB from:", url);
  // console.log("Animations:", animations);
  // console.log("Model Scene:", gltf.scene);

  useEffect(() => {
    if (actions && animations.length > 0) {
      const actionName = animations[0].name;
      actions[actionName]?.reset().play();
    } else {
      console.warn("No animations found for:", url);
    }
    onLoadEnd?.();
  }, [actions, animations]);

  return (
    <primitive
      object={gltf.scene}
      ref={modelRef}
      position={[0, 0, 0]}
      onError={onError}
    />
  );
}


interface SceneProps {
  url: string;
  onLoadStart?: () => void;
  onLoadEnd?: () => void;
  onError?: (err: unknown) => void;
}

const Scene: React.FC<SceneProps> = ({ url, onLoadStart, onLoadEnd, onError }) => {
  useEffect(() => {
    onLoadStart?.();
  }, [url]);

  return (
    <Canvas camera={{ position: [1.3, 1.5, 1.9] }} shadows>
      <Suspense fallback={<Loader />}>
        <directionalLight
          position={[-1.3, 6.0, 4.4]}
          castShadow
          intensity={Math.PI}
        />
        <ModelWithAnimation url={url} onLoadEnd={onLoadEnd} onError={onError} />
        <OrbitControls target={[0, 1, 0]} />
        <axesHelper args={[5]} />
        <Stats />
      </Suspense>
    </Canvas>
  );
};


export default Scene;

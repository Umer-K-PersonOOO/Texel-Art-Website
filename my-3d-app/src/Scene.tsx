import {
  Html,
  OrbitControls,
  Stats,
  useProgress,
  useAnimations,
} from "@react-three/drei";
import { Canvas, useLoader } from "@react-three/fiber";
import React, { Suspense, useRef, useEffect } from "react";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";
import * as THREE from "three";

function Loader() {
  const { progress } = useProgress();
  return <Html center>{progress.toFixed(0)} % loaded</Html>;
}

interface ModelWithAnimationProps {
  url: string;
}

function ModelWithAnimation({ url }: ModelWithAnimationProps) {
  const gltf = useLoader(GLTFLoader, url);
  const modelRef = useRef<THREE.Group>(null);
  const { animations } = gltf;
  const { actions } = useAnimations(animations, modelRef);

  console.log("Loaded GLB from:", url);
  console.log("Animations:", animations);
  console.log("Model Scene:", gltf.scene);

  useEffect(() => {
    if (actions && animations.length > 0) {
      const actionName = animations[0].name;
      console.log("Playing animation:", actionName);
      actions[actionName]?.reset().play();
    } else {
      console.warn("No animations found for:", url);
    }
  }, [actions, animations]);

  return <primitive object={gltf.scene} ref={modelRef} position={[0, 0, 0]} />;
}


interface SceneProps {
  url: string;
}

const Scene: React.FC<SceneProps> = ({ url }) => {
  return (
    <Canvas camera={{ position: [1.3, 1.5, 1.9] }} shadows>
      <Suspense fallback={<Loader />}>
        <directionalLight
          position={[-1.3, 6.0, 4.4]}
          castShadow
          intensity={Math.PI}
        />
        <ModelWithAnimation url={url} />
        <OrbitControls target={[0, 0.5, 0]} />
        <axesHelper args={[5]} />
        <Stats />
      </Suspense>
    </Canvas>
  );
};

export default Scene;

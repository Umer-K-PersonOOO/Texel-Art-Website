import React, { Suspense, useRef, useEffect } from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { Html, OrbitControls, useProgress, useAnimations } from "@react-three/drei";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";

function Loader() {
  const { progress } = useProgress();
  return <Html center>{progress.toFixed(0)} % loaded</Html>;
}

function ModelWithAnimation({ url }) {
  const gltf = useLoader(GLTFLoader, url);
  const modelRef = useRef();
  const { animations } = gltf;
  const { actions } = useAnimations(animations, modelRef);

  useEffect(() => {
    if (actions && animations.length > 0) {
      actions[animations[0].name]?.reset().play();
    }
  }, [actions, animations]);

  return <primitive object={gltf.scene} ref={modelRef} position={[0, 1, 0]} />;
}

function DisplayGLTF() {
  return (
    <Canvas camera={{ position: [-0.5, 1, 2] }} shadows frameloop="demand">
      <Suspense fallback={<Loader />}>
        <directionalLight
          position={[-1.3, 6.0, 4.4]}
          castShadow
          intensity={Math.PI}
        />
        <ModelWithAnimation url="/models/testing.glb" />
        <OrbitControls target={[0, 1, 0]} />
        <axesHelper args={[5]} />
      </Suspense>
    </Canvas>
  );
}

export default DisplayGLTF;

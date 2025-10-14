import React, { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF } from '@react-three/drei'

function Model({ url }) {
  const { scene } = useGLTF(url)
  return <primitive object={scene} />
}

export default function GLBViewer({ url }) {
  return (
    <Canvas camera={{ position: [0, 0, 5] }}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} />
      <Suspense fallback={null}>
        <Model url={url} />
      </Suspense>
      <OrbitControls />
    </Canvas>
  )
}

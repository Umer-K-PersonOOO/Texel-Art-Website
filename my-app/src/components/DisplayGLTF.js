// import React, { useEffect, useRef } from "react";
// import * as THREE from "three";

// const DisplayGLTF = ({ gltfUrl }) => {
//     const mountRef = useRef(null);

//     useEffect(() => {
//         // set up the scene, camera, and renderer
//         const scene = new THREE.Scene();
//         const camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000);

//         const renderer = new THREE.WebGLRenderer();
//         renderer.setSize(window.innerWidth, window.innerHeight);
//         renderer.setAnimationLoop(animate);
//         document.body.appendChild(renderer.domElement);

//         // add lighting
//         const light = new THREE.AmbientLight(0xffffff, 1);
//         scene.add(light);

//         // load the GLTF model
//         const loader = new GLTFLoader();
//         loader.load(
//             gltfUrl,
//             (gltf) => {
//                 scene.add(gltf.scene);
//                 animate();
//             },
//             undefined,
//             (error) => {
//                 console.error('An error occurred while loading the GLTF file:', error);
//             }
//         );

//         // set up the camera position
//         camera.position.z = 5;

//         // animation loop
//         const animate = () => {
//             requestAnimationFrame(animate);
//             renderer.render(scene, camera);
//         };

//         // clean up on component unmount
//         return () => {
//             while (scene.children.length > 0) {
//                 scene.remove(scene.children[0]);
//             }
//             renderer.dispose();
//         };
//     }, [gltfUrl]);

//     return <div ref={mountRef} />;
// };

// export default DisplayGLTF;
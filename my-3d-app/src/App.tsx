import React, { useState } from "react";
import GenerateFromVideo from "./components/GenerateFromVideo";
import GLBGrid from "./components/GLBGrid";
import Scene from "./Scene";

const App: React.FC = () => {
  const [currentGLBUrl, setCurrentGLBUrl] = useState<string>("/models/base.glb");

  return (
    <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white min-h-screen">
      <header className="text-center py-6 border-b border-gray-700">
        <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-teal-300 bg-clip-text text-transparent">
          Texel Art Animation Maker
        </h1>
        <p className="text-gray-400 mt-1 text-sm">
          Upload videos, view animations, and generate 3D scenes.
        </p>
      </header>

      <main className="flex flex-col md:flex-row">
        <section className="md:w-1/2 bg-gray-100 text-black overflow-auto border-r border-gray-300">
          <GLBGrid onSelectGLB={setCurrentGLBUrl} refreshTrigger={refreshCounter}/>
        </section>

        <section className="md:w-1/2 flex flex-col bg-gray-900 p-4">
          <div className="flex-1 bg-gray-800 rounded-2xl shadow-lg p-3 mb-4">
              <Scene url={currentGLBUrl} />
          </div>
          <div className="flex-none">
              <GenerateFromVideo setGLBUrl={setCurrentGLBUrl} triggerGLBRefresh={triggerRefresh}/>
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;

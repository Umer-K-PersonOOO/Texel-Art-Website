import React, { useState } from "react";
import GenerateFromVideo from "./components/GenerateFromVideo";
import GLBGrid from "./components/GLBGrid";
import Scene from "./Scene";

const App: React.FC = () => {
  const [currentGLBUrl, setCurrentGLBUrl] = useState<string>("/models/base.glb");

  return (
    <div className="bg-gray-900 text-white min-h-screen">
      <div className="text-center text-4xl font-bold py-5">
        Texel Art Animation Maker
      </div>

      <div className="flex">
        <div className="flex w-1/2 bg-slate-300 overflow-auto">
          <GLBGrid onSelectGLB={setCurrentGLBUrl} />
        </div>

        <div className="flex w-1/2 bg-slate-600 h-[90vh]">
          <div className="flex-col">
            <div className="h-1/2 w-[50vw]">
              <Scene url={currentGLBUrl} />
            </div>
            <div className="h-1/2 w-[50vw]">
              <GenerateFromVideo setGLBUrl={setCurrentGLBUrl} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;

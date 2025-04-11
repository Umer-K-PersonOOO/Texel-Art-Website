import React from "react";
import UploadMesh from "./UploadMesh";
import Grid from "./components/Grid";
import SelectMesh from "./components/SelectMesh";

function App() {
  return (
    <div className="bg-gray-900 text-white min-h-screen">
      {/* Main Title */}
      <div className="text-center text-4xl font-bold py-5">
        Texel Art Animation Maker
      </div>
      {/* Select Mesh Component */}
      <SelectMesh />
    </div>
  );
}

export default App;

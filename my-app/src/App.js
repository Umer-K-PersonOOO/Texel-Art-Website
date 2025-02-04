import React from "react";
import UploadMesh from "./UploadMesh";

function App() {
    return (
        <div className="bg-gray-900 text-white min-h-screen flex flex-col items-center">
            <header className="w-full py-5 text-center bg-gradient-to-r from-purple-500 to-blue-500 shadow-lg">
                <h1 className="text-3xl font-bold">TEXEL Arts Animation Processor</h1>
                <p className="text-gray-200">Upload animation files and armatures to generate stunning results.</p>
            </header>

            <main className="flex flex-col items-center justify-center flex-grow w-full p-6">
                <UploadMesh />
            </main>

            <footer className="w-full py-4 text-center bg-gray-800">
            </footer>
        </div>
    );
}

export default App;
// top imports unchanged
import React, { useEffect, useRef, useState } from "react";
import "./Scene";
import Scene from "./Scene";
import GenerateFromVideo from "./components/GenerateFromVideo";

interface FileEntry {
  id: number;
  name: string;
  glbBlob: Blob;
  videoBlob: Blob;
  glbUrl?: string;      // object URL string
  videoUrl?: string;    // object URL string
}

const App: React.FC = () => {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [currentGLBUrl, setCurrentGLBUrl] = useState<string>("/models/base.glb");
  const [currentVideoUrl, setCurrentVideoUrl] = useState<string>("");
  const [refreshCounter, setRefreshCounter] = useState(0);


  // keep track of created object URLs so we can revoke them on unmount or reload
  const createdUrlsRef = useRef<string[]>([]);

  const triggerRefresh = () => setRefreshCounter((prev) => prev + 1);

  useEffect(() => {
    let cancelled = false;

    async function loadFiles() {
      const res = await fetch("http://127.0.0.1:8000/joints");
      const metadata = await res.json();

      const enriched: FileEntry[] = await Promise.all(
        metadata.map(async (file: { id: number; name: string }) => {
          const [glbRes, videoRes] = await Promise.all([
            fetch(`http://127.0.0.1:8000/transform/rig?id=${file.id}&name=${encodeURIComponent(file.name)}`),
            fetch(`http://127.0.0.1:8000/video/${file.id}`)
          ]);

          const glbBlob = await glbRes.blob();
          const videoBlob = await videoRes.blob();

          // create object URLs once here (not in render)
          const glbUrl = URL.createObjectURL(glbBlob);
          const videoUrl = URL.createObjectURL(videoBlob);

          // remember to revoke later
          createdUrlsRef.current.push(glbUrl, videoUrl);

          return {
            id: file.id,
            name: file.name,
            glbBlob,
            videoBlob,
            glbUrl,
            videoUrl
          } as FileEntry;
        })
      );

      if (!cancelled) setFiles(enriched);
    }

    loadFiles();

    return () => {
      cancelled = true;
      // cleanup: revoke object URLs created earlier
      createdUrlsRef.current.forEach((u) => {
        try { URL.revokeObjectURL(u); } catch { /* ignore */ }
      });
      createdUrlsRef.current = [];
    };
  }, [refreshCounter]); // re-run when you trigger refresh

  return (
    <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white min-h-screen">
      <header className="text-center py-6 border-b border-gray-700">
        <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-teal-300 bg-clip-text text-transparent">
          Texel Art Animation Maker
        </h1>
      </header>

      <main className="flex flex-col md:flex-row">
        <section className="md:w-1/2 bg-gray-100 text-black overflow-auto border-r border-gray-300">
          <div className="p-6 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {files.map((file) => {
              // use the pre-created URLs from state
              const glbObjectUrl = file.glbUrl!;
              const videoObjectUrl = file.videoUrl!;

              return (
                <div
                  key={file.id}
                  onClick={() => {
                    // set both in a single handler so React batches
                    setCurrentGLBUrl(glbObjectUrl);
                    setCurrentVideoUrl(videoObjectUrl);
                  }}
                  className="rounded-xl bg-white shadow hover:shadow-lg hover:-translate-y-1 transition-transform duration-200 cursor-pointer p-4"
                >
                  <p className="text-center text-gray-800 font-medium truncate">{file.name}</p>
                </div>
              );
            })}

            {files.length === 0 && (
              <p className="col-span-full text-center text-gray-500">
                No animations found.
              </p>
            )}
          </div>
        </section>

        <section className="md:w-1/2 flex flex-col bg-gray-900 p-4 space-y-4">
          <div className="flex-1 flex flex-col md:flex-row gap-4">
            <div className="flex-1 bg-gray-800 rounded-2xl shadow-lg p-0 flex">
              {/* Video Section */}
              <div className="w-1/2 flex items-center justify-center overflow-hidden">
                {currentVideoUrl && (
                  <video autoPlay loop muted 
                    className="w-full h-full object-contain" 
                    key={currentVideoUrl}
                  >
                    <source src={currentVideoUrl} type="video/mp4" />
                  </video>
                )}
              </div>
              {/* 3D Scene Section */}
              <div className="w-1/2 flex items-center justify-center overflow-hidden">
                <Scene key={currentGLBUrl} url={currentGLBUrl}/>
              </div>
            </div>
          </div>


          <div className="flex-none">
            <GenerateFromVideo
              setGLBUrl={(u) => setCurrentGLBUrl(u)}
              triggerGLBRefresh={triggerRefresh}
            />
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;

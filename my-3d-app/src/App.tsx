// top imports unchanged
import React, { useEffect, useRef, useState } from "react";
import "./Scene";
import Scene from "./Scene";
import GenerateFromVideo from "./components/GenerateFromVideo";

interface FileEntry {
  id: number;
  name: string;
  glbUrl?: string;      // object URL string
  videoUrl?: string;    // object URL string
}

const App: React.FC = () => {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [currentGLBUrl, setCurrentGLBUrl] = useState<string>("/models/base.glb");
  const [currentVideoUrl, setCurrentVideoUrl] = useState<string>("");
  const [refreshCounter, setRefreshCounter] = useState(0);
  const [gridLoading, setGridLoading] = useState<boolean>(true);
  const [loadingCardId, setLoadingCardId] = useState<number | null>(null);


  // track created URLs for cleanup
  const createdUrlsRef = useRef<string[]>([]);

  // cache loaded GLB + video per file
  const cacheRef = useRef<Record<number, { glbUrl: string; videoUrl: string }>>({});

  const triggerRefresh = () => setRefreshCounter((prev) => prev + 1);
  

  useEffect(() => {
    let cancelled = false;

    async function loadMetadata() {
      setGridLoading(true);

      const res = await fetch("http://127.0.0.1:8000/joints");
      const metadata: { id: number; name: string }[] = await res.json();

      if (!cancelled) {
        setFiles(metadata); // only store id + name
        setGridLoading(false);
      }
    }

    loadMetadata();

    return () => {
      cancelled = true;
      // cleanup created object URLs
      createdUrlsRef.current.forEach((u) => {
        try { URL.revokeObjectURL(u); } catch {}
      });
      createdUrlsRef.current = [];
      cacheRef.current = {};
    };
  }, [refreshCounter]);

  // handler to fetch GLB + video on click (with caching)
  const handleCardClick = async (file: FileEntry) => {
    if (loadingCardId !== null) return;
    setLoadingCardId(file.id);

    // already cached?
    if (cacheRef.current[file.id]) {
      const { glbUrl, videoUrl } = cacheRef.current[file.id];
      setCurrentGLBUrl(glbUrl);
      setCurrentVideoUrl(videoUrl);
      return;
    }

    // fetch both GLB + video
    const [glbRes, videoRes] = await Promise.all([
      fetch(`http://127.0.0.1:8000/transform/rig?id=${file.id}&name=${encodeURIComponent(file.name)}`),
      fetch(`http://127.0.0.1:8000/video/${file.id}`)
    ]);

    const glbBlob = await glbRes.blob();
    const videoBlob = await videoRes.blob();

    const glbUrl = URL.createObjectURL(glbBlob);
    const videoUrl = URL.createObjectURL(videoBlob);

    // save to cache + cleanup list
    cacheRef.current[file.id] = { glbUrl, videoUrl };
    createdUrlsRef.current.push(glbUrl, videoUrl);

    setCurrentGLBUrl(glbUrl);
    setCurrentVideoUrl(videoUrl);
    setLoadingCardId(null);
  };


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
            {files.map((file) => (
              <div
                key={file.id}
                onClick={() => handleCardClick(file)}
                className={`
                  rounded-xl bg-white shadow hover:shadow-lg hover:-translate-y-1
                  transition-all duration-500 cursor-pointer p-4
                  opacity-0 animate-[fadeIn_0.4s_ease-out_forwards]
                  ${loadingCardId !== null && loadingCardId !== file.id ? "cursor-not-allowed opacity-50" : ""}
                `}
              >
                <p className="text-center text-gray-800 font-medium truncate">{file.name}</p>
              </div>
            ))}


            {gridLoading && (
              <p className="col-span-full text-center text-gray-500">Loading...</p>
            )}

            {!gridLoading && files.length === 0 && (
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
              <div className="w-1/2 flex items-center justify-center overflow-hidden bg-gray-900">
                {currentVideoUrl ? (
                  <video autoPlay loop muted className="w-full h-full object-contain" key={currentVideoUrl}>
                    <source src={currentVideoUrl} type="video/mp4" />
                  </video>
                ) : (
                  <p className="text-gray-400 text-center text-lg">Select a video to play</p>
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
              triggerGLBRefresh={triggerRefresh}
            />
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;

import React, { useEffect, useState } from "react";
import Scene from "../Scene";

interface JointFile {
  id: number;
  name: string;
}

interface GLBGridProps {
  onSelectGLB: (glbUrl: string, videoUrl: string) => void;
  refreshTrigger: number; // increment to trigger refetch
}

const GLBGrid: React.FC<GLBGridProps> = ({ onSelectGLB, refreshTrigger }) => {
  const [files, setFiles] = useState<JointFile[]>([]);

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/joints/");
        const data = await res.json();
        setFiles(data);
      } catch (error) {
        console.error("Failed to fetch joint files", error);
      }
    };

    fetchFiles();
  }, [refreshTrigger]);

  return (
    <div className="p-6 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
      {files.map((file) => {
        console.log("123456" + file.name)
        const glbUrl = `http://127.0.0.1:8000/transform/rig?id=${file.id}&name=${file.name}`;
        const videoUrl = `http://127.0.0.1:8000/video/${file.id}`
        return (
          <div
            key={file.id}
            onClick={() => onSelectGLB(glbUrl, videoUrl)}
            className="rounded-xl bg-white shadow hover:shadow-lg hover:-translate-y-1 transition-transform duration-200 cursor-pointer"
          >
            <div className="aspect-square rounded-t-xl overflow-hidden bg-gray-100">
              <Scene url={glbUrl} />
            </div>
            <div className="p-2">
              <p className="text-center text-gray-800 font-medium truncate">
                {file.name}
              </p>
            </div>
          </div>
        );
      })}
      {files.length === 0 && (
        <p className="col-span-full text-center text-gray-500">
          No animations found.
        </p>
      )}
    </div>
  );
};

export default GLBGrid;

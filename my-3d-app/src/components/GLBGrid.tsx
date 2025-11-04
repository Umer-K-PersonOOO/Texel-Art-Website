import React, { useEffect, useState } from "react";
import Scene from "../Scene";

interface JointFile {
  id: number;
  name: string;
}

interface GLBGridProps {
  onSelectGLB: (url: string) => void;
}

const GLBGrid: React.FC<GLBGridProps> = ({ onSelectGLB }) => {
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
  }, []);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6">
      {files.map((file) => {
        const fileUrl = `http://127.0.0.1:8000/transform/rig?name=${file.name}`; // change this.
        return (
          <div
            key={file.id}
            onClick={() => onSelectGLB(fileUrl)}
            className="border rounded-lg shadow-md bg-white p-2 w-full max-w-[200px] mx-auto cursor-pointer hover:scale-105 transition-transform aspect-square"
          >
            <div className="aspect-square w-full">
              <Scene url={fileUrl} />
            </div>
            <p className="text-center mt-2 text-sm text-black truncate">{file.name}</p>
          </div>
        );
      })}
    </div>
  );
};

export default GLBGrid;

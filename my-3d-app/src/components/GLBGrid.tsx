import React, { useEffect, useState } from "react";
import Scene from "../Scene";

interface JointFile {
  id: number;
  name: string;
}

interface GLBGridProps {
  onSelectGLB: (url: string) => void;
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
        const fileUrl = `http://127.0.0.1:8000/transform/rig?name=${file.name}`;
        return (
          <div
            key={file.id}
            onClick={() => onSelectGLB(fileUrl)}
            className="rounded-xl bg-white shadow hover:shadow-lg hover:-translate-y-1 transition-transform duration-200 cursor-pointer"
          >
            <div className="aspect-square rounded-t-xl overflow-hidden bg-gray-100">
              <Scene url={fileUrl} />
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

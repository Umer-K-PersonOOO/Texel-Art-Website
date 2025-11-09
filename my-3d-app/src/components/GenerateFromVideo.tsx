import React, { ChangeEvent, FormEvent, useState } from "react";

interface GenerateFromVideoProps {
  setGLBUrl: (url: string) => void;
}

const GenerateFromVideo: React.FC<GenerateFromVideoProps> = ({ setGLBUrl }) => {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [animationName, setAnimationName] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [status, setStatus] = useState<string>("");

  const isValidName = (name: string) => /^[a-zA-Z0-9_-]+$/.test(name);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setStatus("");

    if (!videoFile) return setError("Please upload a video file.");
    const ext = videoFile.name.split(".").pop()?.toLowerCase();
    if (!["mp4", "mov"].includes(ext || "")) return setError("Only .mp4 and .mov files are allowed.");
    if (!animationName.trim()) return setError("Please enter an animation name.");
    if (!isValidName(animationName)) return setError("Name can only contain letters, numbers, dashes, or underscores.");

    const formData = new FormData();
    formData.append("file", videoFile);
    formData.append("name", animationName);

    try {
      const res = await fetch("https://fb11-128-62-106-72.ngrok-free.app/process/video/", {
          method: "POST",
          body: formData,
      });
      const data = await res.json();

      if (res.ok) {
        setStatus(`✅ Animation saved as: ${data.name}`);
        
        // Now call transform/rig
        const rigUrl = `https://fb11-128-62-106-72.ngrok-free.app/transform/rig?name=${data.name}`;
        setGLBUrl(rigUrl);
      } else {
        setError(data.error || "Something went wrong.");
      }
    } catch {
      setError("Upload failed. Server error.");
    }
  };

  return (
    <div className="bg-gray-800 text-white rounded-xl shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4 text-center">
        Upload Video to Animate
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-gray-300 mb-1">Animation Name</label>
          <input
            type="text"
            value={animationName}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setAnimationName(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 focus:ring-2 focus:ring-blue-500 outline-none text-white placeholder-gray-400"
            placeholder="e.g., my_animation"
            required
          />
        </div>

        <div>
          <label className="block text-sm text-gray-300 mb-1">Video File (.mp4 or .mov)</label>
          <input
            type="file"
            accept=".mp4,.mov"
            onChange={(e: ChangeEvent<HTMLInputElement>) => {
              if (e.target.files && e.target.files[0]) {
                setVideoFile(e.target.files[0]);
              }
            }}
            className="w-full bg-gray-700 border border-gray-600 p-2 rounded-md text-white"
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 transition-colors py-2 rounded-md font-medium"
        >
          Submit
        </button>

        {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
        {status && <p className="text-green-400 text-sm mt-2">{status}</p>}
      </form>
    </div>
  );
};

export default GenerateFromVideo;

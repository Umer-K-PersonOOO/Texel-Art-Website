import React, { useState, ChangeEvent, FormEvent } from "react";

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
    <div className="max-w-md mx-auto mt-10 p-6 bg-white shadow-lg rounded-xl">
      <h2 className="text-2xl font-semibold mb-4 text-center text-black">Upload Video to Animate</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Animation Name</label>
          <input
            type="text"
            value={animationName}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setAnimationName(e.target.value)}
            className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none text-black"
            placeholder="e.g., my_animation"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Video File (.mp4 or .mov)</label>
          <input
            type="file"
            accept=".mp4,.mov"
            onChange={(e: ChangeEvent<HTMLInputElement>) => {
              if (e.target.files && e.target.files[0]) {
                setVideoFile(e.target.files[0]);
              }
            }}
            className="w-full border border-gray-300 p-2 rounded-md"
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition"
        >
          Submit
        </button>

        {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        {status && <p className="text-green-600 text-sm mt-2">{status}</p>}
      </form>
    </div>
  );
};

export default GenerateFromVideo;

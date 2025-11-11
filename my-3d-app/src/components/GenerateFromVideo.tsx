import React, { ChangeEvent, FormEvent, useState } from "react";

interface GenerateFromVideoProps {
  setGLBUrl: (url: string) => void;
  triggerGLBRefresh: () => void;
}

const GenerateFromVideo: React.FC<GenerateFromVideoProps> = ({ setGLBUrl, triggerGLBRefresh }) => {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [animationName, setAnimationName] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const isValidName = (name: string) => /^[a-zA-Z0-9_-]+$/.test(name);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (loading) return; // prevent spam submissions
    setError("");
    setStatus("");
    setLoading(true);

    if (!videoFile) return setError("Please upload a video file.");
    const ext = videoFile.name.split(".").pop()?.toLowerCase();
    if (!["mp4", "mov"].includes(ext || "")) return setError("Only .mp4 and .mov files are allowed.");
    if (!animationName.trim()) return setError("Please enter an animation name.");
    if (!isValidName(animationName)) return setError("Name can only contain letters, numbers, dashes, or underscores.");

    const formData = new FormData();
    formData.append("file", videoFile);
    formData.append("name", animationName);

    try {
      const res = await fetch("http://127.0.0.1:8000/process/video/", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (res.ok) {
        setStatus(`✅ Animation saved as: ${data.name}`);
        const rigUrl = `http://127.0.0.1:8000/transform/rig?id=${data.id}&name=${data.name}`;
        setGLBUrl(rigUrl);
        triggerGLBRefresh();
      } else {
        setError(data.error || "Something went wrong.");
      }
    } catch {
      setError("Upload failed. Server error.");
    } finally {
      setLoading(false);
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
            onChange={(e: ChangeEvent<HTMLInputElement>) => e.target.files && setVideoFile(e.target.files[0])}
            className="w-full bg-gray-700 border border-gray-600 p-2 rounded-md text-white"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading} // disable button while loading
          className={`w-full py-2 rounded-md font-medium transition-colors ${
            loading ? "bg-gray-500 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Processing..." : "Submit"}
        </button>

        {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
        {status && <p className="text-green-400 text-sm mt-2">{status}</p>}
      </form>
    </div>
  );
};

export default GenerateFromVideo;

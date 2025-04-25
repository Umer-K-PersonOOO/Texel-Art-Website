import React, { useState } from "react";

const VideoUploader = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [animationName, setAnimationName] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const isValidName = (name) => /^[a-zA-Z0-9_-]+$/.test(name); // no special chars

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setStatus("");

    if (!videoFile) return setError("Please upload a video file.");
    const ext = videoFile.name.split(".").pop().toLowerCase();
    if (!["mp4", "mov"].includes(ext)) return setError("Only .mp4 and .mov files are allowed.");
    if (!animationName.trim()) return setError("Please enter an animation name.");
    if (!isValidName(animationName)) return setError("Name can only contain letters, numbers, dashes, or underscores.");

    const formData = new FormData();
    formData.append("file", videoFile);
    formData.append("name", animationName);

    // TODO: Make sure to do this for demo: ngrok http 8080
    try {
      const res = await fetch("http://127.0.0.1:8000/process/video/", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok) setStatus(`✅ Animation saved as: ${data.name}`);
      else setError(data.error || "Something went wrong.");
    } catch {
      setError("Upload failed. Server error.");
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white shadow-lg rounded-xl">
      <h2 className="text-2xl font-semibold mb-4 text-center">Upload Video to Animate</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Animation Name</label>
          <input
            type="text"
            value={animationName}
            onChange={(e) => setAnimationName(e.target.value)}
            className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="e.g., my_animation"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Video File (.mp4 or .mov)</label>
          <input
            type="file"
            accept=".mp4,.mov"
            onChange={(e) => setVideoFile(e.target.files[0])}
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

export default VideoUploader;

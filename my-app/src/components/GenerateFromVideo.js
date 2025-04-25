import React, { useState } from "react";

const GenerateFromVideo = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [animationName, setAnimationName] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const isValidName = (name) => /^[a-zA-Z0-9_-]+$/.test(name); // no special chars

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setStatus("");

    if (!videoFile) {
      setError("Please upload a video file.");
      return;
    }

    const fileExt = videoFile.name.split(".").pop().toLowerCase();
    if (!["mp4", "mov"].includes(fileExt)) {
      setError("Only .mp4 and .mov files are allowed.");
      return;
    }

    if (!animationName.trim()) {
      setError("Please enter a valid animation name.");
      return;
    }

    if (!isValidName(animationName)) {
      setError(
        "Animation name can only contain letters, numbers, dashes, or underscores."
      );
      return;
    }

    const formData = new FormData();
    formData.append("file", videoFile);
    formData.append("name", animationName);

    try {
      const res = await fetch("/process/video/", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        setStatus(`Success! Animation saved as: ${data.name}`);
      } else {
        setError(data.error || "Something went wrong.");
      }
    } catch (err) {
      setError("Failed to upload. Server error.");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Animation Name:
        <input
          type="text"
          value={animationName}
          onChange={(e) => setAnimationName(e.target.value)}
          required
        />
      </label>
      <br />
      <label>
        Upload Video (.mp4 or .mov):
        <input
          type="file"
          accept=".mp4,.mov"
          onChange={(e) => setVideoFile(e.target.files[0])}
          required
        />
      </label>
      <br />
      <button type="submit">Submit</button>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {status && <p style={{ color: "green" }}>{status}</p>}
    </form>
  );
};

export default GenerateFromVideo;

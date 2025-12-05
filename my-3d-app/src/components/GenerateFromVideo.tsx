import React, { ChangeEvent, FormEvent, useEffect, useState } from "react";

interface GenerateFromVideoProps {
  changeRigId: (id: number) => void;
  triggerGLBRefresh: () => void;
}

interface RigEntry {
  id: number;
  name: string;
  rigUrl?: string;      // object URL string
}

const GenerateFromVideo: React.FC<GenerateFromVideoProps> = ({ changeRigId, triggerGLBRefresh }) => {
  const [rigs, setRigs] = useState<RigEntry[]>([]);
  const [selectedRigId, setSelectedRigId] = useState<number | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [animationName, setAnimationName] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [rigUploadLoading, setRigUploadLoading] = useState(false);

  const isValidName = (name: string) => /^[a-zA-Z0-9_-]+$/.test(name);

  useEffect(() => {
    async function loadMetadata() {
      try {
        const res = await fetch("http://127.0.0.1:8000/rigs");
        const metadata = await res.json();
        if (Array.isArray(metadata)) {
          setRigs(metadata);
          if (metadata.length > 0) {
            setSelectedRigId(metadata[0].id);
            changeRigId(metadata[0].id);
          } else {
            setSelectedRigId(null);
          }
        } else {
          console.error("Unexpected rigs payload", metadata);
          setRigs([]);
          setSelectedRigId(null);
        }
      } catch (err) {
        console.error("Failed to load rigs", err);
        setRigs([]);
        setSelectedRigId(null);
      }
    }

    loadMetadata();
  }, []);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (loading) return; // prevent spam submissions
    setError("");
    setStatus("");
    setLoading(true);

    if (!videoFile) return setError("Please upload a video file."), setLoading(false);
    const ext = videoFile.name.split(".").pop()?.toLowerCase();
    if (!["mp4", "mov"].includes(ext || "")) return setError("Only .mp4 and .mov files are allowed.");
    if (!animationName.trim()) return setError("Please enter an animation name.");
    if (!isValidName(animationName)) return setError("Name can only contain letters, numbers, dashes, or underscores.");
    if (selectedRigId === null) {
      setError("Please select a rig first.");
      setLoading(false);
      return;
    }

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
      <h2 className="text-lg font-semibold text-gray-200">
        Rig Selection
      </h2>
      <div>
        <label className="block text-sm text-gray-300 mb-1">Choose Existing Rig</label>
        <select
          value={selectedRigId ?? ""}
          className="w-full px-3 py-2 rounded-md bg-gray-700 border border-gray-600 
                    focus:ring-2 focus:ring-blue-500 outline-none text-white"
          disabled={!rigs.length}
          onChange={(e) => {
            const id = Number(e.target.value);
            setSelectedRigId(id);
            changeRigId(id);
          }}
        >
          <option value="" disabled>
            {rigs.length ? "Select a rig" : "No rigs available"}
          </option>
          {Array.isArray(rigs) && rigs.map((rig) => (
            <option key={rig.id} value={rig.id}>{rig.name}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-gray-300 mb-1 mt-3">Or Upload Custom Rig (.blend)</label>
        <input
          type="file"
          accept=".blend"
          className="w-full bg-gray-700 border border-gray-600 p-2 rounded-md text-white"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;

            setRigUploadLoading(true);
            setError("");

            const formData = new FormData();
            formData.append("file", file);
            formData.append("name", file.name);

            try {
              const res = await fetch("http://127.0.0.1:8000/upload/rig", {
                method: "POST",
                body: formData,
              });
              const data = await res.json();

              if (res.ok) {
                changeRigId(data.id);
                setSelectedRigId(data.id);
                // refresh dropdown
                setRigs(prev => [...prev, { id: data.id, name: data.name }]);
              } else {
                setError(data.detail || "Something went wrong.");
              }
            } catch {
              setError("Upload failed. Server error.");
            } finally {
              setRigUploadLoading(false);
            }
          }}
        />
      </div>


      <h2 className="text-lg font-semibold text-gray-200 mt-6">
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

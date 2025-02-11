import React, { useState } from "react";

function UploadMesh() {
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const handleUpload = (e) => {
        e.preventDefault();
        const videoFile = e.target[0].files[0];
        const allowedExtensions = /(\.mp4|\.mov)$/i;

        if (!allowedExtensions.exec(videoFile.name)) {
            setError("Invalid file type. Only .mp4 and .mov files are allowed.");
            return;
        }

        setMessage("Files uploaded successfully! (Placeholder)");
        setError("");
    };

    return (
        <div className="bg-gray-900 text-white min-h-screen flex flex-col items-center justify-center p-10">
            {/* Flex container for Upload + Bone Mapping */}
            <div className="flex flex-col gap-10 w-full max-w-4xl">
                {/* Upload Section */}
                <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full">
                    <h2 className="text-2xl font-semibold text-center mb-4">Upload Your Mesh</h2>

                    <form onSubmit={handleUpload} className="space-y-4">
                        {/* Video File Input */}
                        <div className="flex flex-col">
                            <label className="text-gray-300 mb-1">Upload Video File</label>
                            <input
                                type="file"
                                className="file:bg-blue-500 file:text-white file:border-none file:py-2 file:px-4 rounded-md shadow-sm cursor-pointer"
                                required
                            />
                            <p className="text-gray-400 text-sm mt-1">Allowed file types: .mp4, .mov</p>
                        </div>

                        {/* FPX File Input */}
                        <div className="flex flex-col">
                            <label className="text-gray-300 mb-1">Upload .FPX File</label>
                            <input
                                type="file"
                                className="file:bg-blue-500 file:text-white file:border-none file:py-2 file:px-4 rounded-md shadow-sm cursor-pointer"
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className="w-full py-2 bg-green-500 text-white font-semibold rounded-md hover:bg-green-600 transition duration-200"
                        >
                            Submit
                        </button>
                    </form>

                    {message && <p className="text-green-400 mt-3 text-center">{message}</p>}
                    {error && <p className="text-red-400 mt-3 text-center">{error}</p>}
                </div>

                {/* Bone Mapping Section */}
                <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full">
                    <h2 className="text-xl font-semibold mb-2 text-center">Bone-Joint Mapping</h2>

                    {/* Subtitle (Smaller Explanation) */}
                    <p className="text-gray-400 text-sm text-center mb-4">
                        Select which bones in the uploaded mesh correspond to human joints.
                    </p>

                    <div className="overflow-x-auto flex justify-center">
                        <table className="w-auto border-collapse bg-gray-700 rounded-md">
                            <thead>
                                <tr className="text-white">
                                    <th className="p-3 text-center w-40">Bone</th>
                                    <th className="p-3 text-center w-40">Human Joint</th>
                                </tr>
                            </thead>
                            <tbody className="bg-gray-800">
                                <tr className="border-b border-gray-600">
                                    <td className="p-3">
                                        <select className="bg-gray-700 text-white p-2 rounded-md w-full">
                                            <option>Sample Bone 1</option>
                                            <option>Sample Bone 2</option>
                                        </select>
                                    </td>
                                    <td className="p-3">
                                        <select className="bg-gray-700 text-white p-2 rounded-md w-full">
                                            <option>Sample Joint 1</option>
                                            <option>Sample Joint 2</option>
                                        </select>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <button className="mt-4 w-full py-2 bg-blue-500 text-white font-semibold rounded-md hover:bg-blue-600 transition duration-200">
                        Next Page
                    </button>
                </div>
            </div>

            {/* Preview Section (Centered Below Both) */}
            <div className="bg-gray-800 p-6 mt-10 rounded-lg shadow-lg w-full max-w-lg text-center">
                <h2 className="text-xl font-semibold mb-2">Preview Screen</h2>
                <div className="w-full h-40 bg-gray-700 rounded-md flex items-center justify-center">
                    <p className="text-gray-400">[ Mesh Preview Here ]</p>
                </div>
            </div>
        </div>
    );
}

export default UploadMesh;
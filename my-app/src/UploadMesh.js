import React, { useState } from "react";

function UploadMesh() {
    const [message, setMessage] = useState("");

    const handleUpload = (e) => {
        e.preventDefault();
        setMessage("Files uploaded successfully! (Placeholder)");
    };

    return (
        <div className="bg-gray-900 text-white min-h-screen flex flex-col items-center justify-center p-10">
            {/* Upload Section */}
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-lg">
                <h2 className="text-2xl font-semibold text-center mb-4">Upload Mesh</h2>

                <form onSubmit={handleUpload} className="space-y-4">
                    {/* Video File Input */}
                    <div className="flex flex-col">
                        <label className="text-gray-300 mb-1">Upload Video File</label>
                        <input
                            type="file"
                            className="file:bg-blue-500 file:text-white file:border-none file:py-2 file:px-4 rounded-md shadow-sm cursor-pointer"
                            required
                        />
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
            </div>

            {/* Preview Section */}
            <div className="bg-gray-800 p-6 mt-10 rounded-lg shadow-lg w-full max-w-lg text-center">
                <h2 className="text-xl font-semibold mb-2">Preview Screen</h2>
                <div className="w-full h-40 bg-gray-700 rounded-md flex items-center justify-center">
                    <p className="text-gray-400">[ Mesh Preview Here ]</p>
                </div>
            </div>

            {/* Bone Mapping Section */}
            <div className="bg-gray-800 p-6 mt-10 rounded-lg shadow-lg w-full max-w-2xl">
                <h2 className="text-xl font-semibold mb-4 text-center">Bone-Joint Mapping</h2>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-700 text-white">
                                <th className="p-3">Bone</th>
                                <th className="p-3">Human Joint</th>
                            </tr>
                        </thead>
                        <tbody>
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
    );
}

export default UploadMesh;
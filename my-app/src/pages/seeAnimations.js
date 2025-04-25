import React, { useState } from 'react';

const DisplayGLTF = () => {
    const [mesh, setMesh] = useState(null);

    const handleMeshUpload = (uploadedMesh) => {
        setMesh(uploadedMesh);
    };

    return (
        <div style={{ display: 'flex', height: '100vh' }}>
            {/* Left Panel for Grid */}
            <div style={{ flex: 2, position: 'relative' }}>
                <Grid />
            </div>
            {/* Right Panel for Display */}
            <div style={{ flex: 2, position: 'relative' }}>
                <DisplayGLTF />
            </div>
        </div>
    );
};

export default DisplayGLTF;
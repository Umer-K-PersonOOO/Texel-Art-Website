import React from "react";
function SelectMesh() {
    const images = [
        '../assets/XBot.png'
        // '../assets/img2.jpg',
        // '../assets/img3.jpg',
        // '../assets/img4.jpg',
        // '../assets/img5.jpg',
        // '../assets/img6.jpg',
        // '../assets/img7.jpg',
        // '../assets/img8.jpg'
      ];
    
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
          <div className="group relative inline-block p-4 bg-gray-200 rounded-xl cursor-pointer">
            <div className="text-black font-semibold">Select a Rig</div>
            <div className="absolute left-0 top-full mt-2 opacity-0 group-hover:opacity-100 transition duration-300 grid grid-cols-4 gap-2 bg-white p-4 rounded-lg shadow-lg z-10">
              {images.map((src, idx) => (
                <img
                  key={idx}
                  src={src}
                  alt={`Option ${idx + 1}`}
                  className="w-16 h-16 object-cover rounded cursor-pointer hover:scale-105 transition"
                />
              ))}
            </div>
          </div>
        </div>
  );
}

export default SelectMesh;

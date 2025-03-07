import React from "react";

function Grid() {
    
    // Run JS here


    return (
        // JSX elements go here
        // <div className="px-full bg-lime-500 py-5 border-width-2 border-solid border-black">
        // <div className="px-full bg-orange-500 py-5 border-width-2 border-solid border-black"></div>
            
        // </div>

        <div className=" bg-lime-500 border-2 border-solid border-black">
            {/* Grid Container */}
            <div className="grid grid-cols-4 gap-2">
                {/* Grid Items */}
                {Array.from({ length: 16 }).map((_, index) => (
                    <div 
                        key={index} 
                        className="flex items-center justify-center bg-orange-500 text-white font-bold border-2 border-black h-16"
                    >
                        {index + 1}
                    </div>
                ))}
            </div>
        </div>


    )
}

export default Grid;
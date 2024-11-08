import logo from "./logo.svg";
import { useState } from 'react';

function UploadMesh() {

  const [meshFile, setMeshFile] = useState(null);


/*
  -- Way for upload
  -- Preview on Upload
  -- Backend task: Send file and then return list of bones
  -- Table for selecting which bone in mesh relates to which human joint
  -- Backend task make sure they fill everything out and send it to back end
  -- Submit and go to next page
*/
  return (
    <div className="">
     <div className="flex">
      <div className="w-1/3"> <input type="file" id="file" name="file" multiple /> </div>
      <div className="w-2/3 py-10"> <div className="bg-gray-600 w-[90%]"> hhe</div></div>
      
     </div>
    </div>
  );
}

export default UploadMesh;

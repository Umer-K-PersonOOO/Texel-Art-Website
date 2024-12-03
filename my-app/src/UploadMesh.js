import logo from "./logo.svg";
import { useState } from 'react';


function VideoUploader({ onFileSelect }) { 
  const handleFileChange = (e) => { const file = e.target.files[0]; 
    if (file && file.type.startsWith('video')) { 
      onFileSelect(file); 
    } 
    else { 
      alert("Please upload a valid video file."); 
    } 
  }; 
  return ( 
  <div className="uploader"> 
  <label htmlFor="videoFile">Upload Video File:</label> 
  <input type="file" id="videoFile" accept="video/*" onChange={handleFileChange} /> 
  </div> ); 
  }

  function FPXUploader({ onFileSelect }) { 
    const handleFileChange = (e) => { const file = e.target.files[0]; 
      if (file && file.type.startsWith('.fpx')) { 
        onFileSelect(file); 
      } 
      else { 
        alert("Please upload a valid .fpx file."); 
      } 
    }; 
    return ( 
    <div className="uploader"> 
    <label htmlFor="fpxFile">Upload .FPX File:</label> 
    <input type="file" id="fpxFile" accept=".fpx" onChange={handleFileChange} /> 
    </div> 
    ); 
    }


function UploadMesh() {

  const [videoFile, setVideoFile] = useState(null);
  const [fpxFile, setFpxFile] = useState(null);

  const handleSubmit = async () => {
    if (!videoFile || !fpxFile) {
      alert("Please upload both video and .fpx files before submitting.");
      return;
    }

    const formData = new FormData();
    formData.append("videoFile", videoFile);
    formData.append("fpxFile", fpxFile);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      console.log("Response from server:", result);
    } catch (error) {
      console.error("Error uploading files:", error);
    }
  };


/*
  -- Way for upload ( one should be movie file and the other should be a .fpx)
  -- Preview on Upload
  -- Backend task: Send file and then return list of bones
  -- Table for selecting which bone in mesh relates to which human joint
  -- Backend task make sure they fill everything out and send it to back end
  -- Submit and go to next page
*/
  return (
    
    <div className="">
  <h1>Upload Mesh</h1>
      <VideoUploader onFileSelect={setVideoFile} />
      <FPXUploader onFileSelect={setFpxFile} />
      <button onClick={handleSubmit}>Submit</button>

     <div className="flex">
      <div className="w-1/3"> 
        <input type="file" id="file" name="file" multiple /> 
      </div>
      <div className="w-2/3 py-10"> 
        <div className="bg-gray-600 w-[90%]"> preview screen</div>
      </div>
      <p> Choose which bone in the mesh relates to which human joint </p>
      <div></div>
      <table>
      <thead>
        <tr>
          <th>Bone</th>
          <th>Human Joint</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <select>
              <option value="Option">Sample Bone 1</option>
              <option value="opt2">Sample Bone 2</option>
              <option value ="opt3">Sample Bone 3</option>
            </select>
          </td>
          <td>
            <select>
              <option value="opt1">Sample Joint</option>
              <option value="opt2">Sample joint2</option>
              <option value="opt3">Sample joint3</option>
            </select>
          </td>
        </tr>
      </tbody>
    </table>
    <button>
      <a type="button" href="nextPage.html">Next Page</a>
    </button>
    </div>
  </div>
);

}

export default UploadMesh;

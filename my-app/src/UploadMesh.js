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

from fastapi import FastAPI, UploadFile, File, Form, Depends
from sqlalchemy import Column, Integer, String, create_engine, UniqueConstraint, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import subprocess
import shutil
from fastapi.responses import FileResponse

# FastAPI App
app = FastAPI()


# Database Configuration
DATABASE_URL = "postgresql://myuser:citrus@localhost/mocap_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Upload Directory
UPLOAD_DIR = "/home/personooo/blender_tmp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# JointsFile Table 
class JointsFile(Base):
    __tablename__ = "joints_files"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    filedata = Column(LargeBinary)  # Store binary data
    __table_args__ = (UniqueConstraint('name', name='unique_name'),)


# Create Table
Base.metadata.create_all(bind=engine)

# Dependency to Get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Generate Unique Name
def generate_unique_name(db: Session, base_name: str):
    count = 0
    unique_name = base_name
    while db.query(JointsFile).filter(JointsFile.name == unique_name).first():
        count += 1
        unique_name = f"{base_name}_{count}"
    return unique_name

# Run Blender Mocap (Your original implementation kept)
def run_blender_mocap(collection_name, file_name):
    script_path = "/home/personooo/Desktop/Code/Texel-Art-Website/default/Texel-Art-Website/backend/Texel-Art-Media/src/addon_script.py"
    try:
        print("Running Blender script...")
        command = [
            "blender", "--python", script_path, "--", collection_name, file_name
        ]
        subprocess.run(" ".join(command), shell=True, check=True)
        return {"message": "Mocap processing completed successfully"}
    except subprocess.CalledProcessError as e:
        return {"error in script": f"Blender execution failed: {e}"}

# Process Video and Save Joints File
@app.post("/process/video/")
def process_video(file: UploadFile = File(...), name: str = Form(...), db: Session = Depends(get_db)):
    try:
        # Save uploaded video temporarily
        file_location = f"{UPLOAD_DIR}/{file.filename}"
        print(f"Saving file to {file_location}")
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Generate collection name and output path
        datetime_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        collection_name = f"cgt_DRIVERS_{file.filename}_{datetime_str}"
        output_dir = os.path.expanduser(os.path.join("~", "blender_tmp"))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{collection_name}.blend")

        # Run Blender
        result = run_blender_mocap(collection_name, file_location)
        if result.get("error in script"):
            return result

        # Read .blend file as binary
        with open(output_path, "rb") as f:
            filedata = f.read()

        # Generate unique name
        unique_name = generate_unique_name(db, name)

        # Save to DB
        joints_file = JointsFile(name=unique_name, filedata=filedata)
        db.add(joints_file)
        db.commit()
        db.refresh(joints_file)

        return {
            "message": "Mocap processing and joints file saved successfully",
            "id": joints_file.id,
            "name": unique_name
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/transform/rig/")
def transform_rig(name: str = Form(...)):
    try:
        output_dir = os.path.expanduser(os.path.join("~", "blender_tmp"))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{name}.glb")

        script_path = "/home/personooo/Desktop/Code/Texel-Art-Website/default/Texel-Art-Website/backend/Texel-Art-Media/src/transform_addon_script.py"
        command = [
            "blender", "--python", script_path, "--", name
        ]

        subprocess.run(" ".join(command), shell=True, check=True)

        return FileResponse(
            path=output_path,
            filename=f"{name}.glb",
            media_type="model/gltf-binary"
        )

    except subprocess.CalledProcessError as e:
        return {"error in script": f"Blender execution failed: {e}"}
    except Exception as e:
        return {"error": str(e)}



# Get all joints files
@app.get("/joints/")
def get_joints_files(db: Session = Depends(get_db)):
    return db.query(JointsFile).all()

@app.get("/joints/{file_id}")
def download_joints_file(file_id: int, db: Session = Depends(get_db)):
    joints_file = db.query(JointsFile).filter(JointsFile.id == file_id).first()
    if not joints_file:
        return {"error": "File not found"}

    output_path = f"/tmp/{joints_file.name}.blend"
    with open(output_path, "wb") as f:
        f.write(joints_file.filedata)

    return {"message": "File restored", "filepath": output_path}


# Hello World
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

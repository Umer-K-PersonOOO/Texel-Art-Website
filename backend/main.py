from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import shutil
import bpy
import subprocess

bpy.ops.wm.read_factory_settings(use_empty=True)  # Clears default Blender scene


# FastAPI App
app = FastAPI()

# Database Configuration
DATABASE_URL = "postgresql://myuser:citrus@localhost/mocap_db"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# File Storage Path
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Database Models
class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)

class Rig(Base):
    __tablename__ = "rigs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)

# Create DB Tables
Base.metadata.create_all(bind=engine)

# Dependency to Get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Upload Video Endpoint
@app.post("/upload/video/")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Save metadata in DB
    video = Video(filename=file.filename, filepath=file_location)
    db.add(video)
    db.commit()
    db.refresh(video)

    return {"message": "Video uploaded successfully", "id": video.id, "filename": file.filename}

def extract_bones_from_rig(filepath):
    bpy.ops.import_scene.fbx(filepath=filepath)


    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break

    if armature:
        return [bone.name for bone in armature.data.bones]
    return []

@app.post("/upload/rig/")
async def upload_rig(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Save metadata in DB
    rig = Rig(filename=file.filename, filepath=file_location)
    db.add(rig)
    db.commit()
    db.refresh(rig)

    # Extract bones from file
    bone_names = extract_bones_from_rig(file_location)

    return {"message": "Rig uploaded successfully", "id": rig.id, "filename": file.filename, "bones": bone_names}


# Get All Uploaded Videos
@app.get("/videos/")
def get_videos(db: Session = Depends(get_db)):
    return db.query(Video).all()

# Get All Uploaded Rigs
@app.get("/rigs/")
def get_rigs(db: Session = Depends(get_db)):
    return db.query(Rig).all()

# Hello World Endpoint
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


def run_blender_mocap(video_path):
    script_path = "~/Desktop/Code/Texel-Art-Media/src/addon_script.py"  # Path to your Blender script    

    command = [
                "sudo", "blender", "--python", script_path
    ]

    try:
        print("Running Blender script...")
        subprocess.run(" ".join(command), shell=True, check=True)
        return {"message": "Mocap processing completed successfully"}
    except subprocess.CalledProcessError as e:
        return {"error": f"Blender execution failed: {e}"}

@app.post("/process/video/{video_id}")
def process_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    # if not video:
    #     return {"error": "Video not found"}

    # result = run_blender_mocap(video.filepath)
    try:
        result = run_blender_mocap("")
        return result
    except Exception as e:
        return {"error": str(e)}
    
    



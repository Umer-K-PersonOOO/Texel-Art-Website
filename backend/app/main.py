# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import Column, Integer, String, LargeBinary, UniqueConstraint, create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime
import os, subprocess, shutil, pathlib

# ----------------------------
# Configuration (env-driven)
# ----------------------------
ADDON_MODULE = os.getenv("ADDON_MODULE", "BlendArMocap")
BLENDER_ADDON_SCRIPT = os.getenv("BLENDER_ADDON_SCRIPT", "/opt/addons/BlendArMocap/addon_script.py")
BLENDER_TRANSFORM_SCRIPT = os.getenv("BLENDER_TRANSFORM_SCRIPT", "/opt/addons/BlendArMocap/transform_addon_script.py")
HEADLESS = os.getenv("HEADLESS", "1") == "1"

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/shared/in")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/shared/out")
LEGACY_OUT = os.path.expanduser(os.path.join("~", "blender_tmp"))  # to support existing addon behavior

DEFAULT_SQLITE = "sqlite:////app/backend/mocap.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE)

# Ensure IO dirs exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LEGACY_OUT, exist_ok=True)

# ----------------------------
# Database
# ----------------------------
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite:"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class JointsFile(Base):
    __tablename__ = "joints_files"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    filedata = Column(LargeBinary)
    __table_args__ = (UniqueConstraint('name', name='unique_name'),)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# Blender helpers
# ----------------------------
def _blender_base_cmd() -> list[str]:
    # Run with virtual display when headless so GUI-bound add-on code still works
    xvfb_prefix = ["xvfb-run", "-s", "-screen 0 1920x1080x24"] if HEADLESS else []
    return xvfb_prefix + ["blender", "--factory-startup", "--addons", ADDON_MODULE]

def run_blender_script(script_path: str, *args: str) -> None:
    cmd = _blender_base_cmd() + ["--python", script_path, "--", *args]
    # Use list form (no shell); raise on error
    subprocess.run(cmd, check=True)

def safe_name(name: str) -> str:
    # Strip path components and spaces
    return pathlib.Path(name).stem.replace(" ", "_")

def find_output_blend(basename: str) -> str | None:
    # Check OUTPUT_DIR first, then legacy directory
    cand1 = os.path.join(OUTPUT_DIR, f"{basename}.blend")
    cand2 = os.path.join(LEGACY_OUT, f"{basename}.blend")
    if os.path.exists(cand1): return cand1
    if os.path.exists(cand2): return cand2
    return None

def output_glb_path(basename: str) -> str:
    return os.path.join(OUTPUT_DIR, f"{basename}.glb")

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Utilities
# ----------------------------
def generate_unique_name(db: Session, base_name: str) -> str:
    count = 0
    unique_name = base_name
    while db.query(JointsFile).filter(JointsFile.name == unique_name).first():
        count += 1
        unique_name = f"{base_name}_{count}"
    return unique_name

# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/process/video/")
async def process_video(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Save upload
        original = os.path.basename(file.filename)
        safe_base = safe_name(original)
        upload_path = os.path.join(UPLOAD_DIR, original)
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Collection/output basename
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        collection_name = f"cgt_DRIVERS_{safe_base}_{stamp}"

        # Run Blender mocap script
        run_blender_script(BLENDER_ADDON_SCRIPT, collection_name, upload_path)

        # Find produced .blend
        blend_path = find_output_blend(collection_name)
        if not blend_path:
            return {"error": f"Expected output .blend not found for '{collection_name}' in {OUTPUT_DIR} or {LEGACY_OUT}"}

        # Read and store in DB under a unique logical name
        with open(blend_path, "rb") as f:
            filedata = f.read()

        unique_name = generate_unique_name(db, name)
        record = JointsFile(name=unique_name, filedata=filedata)
        db.add(record)
        db.commit()
        db.refresh(record)

        return {"message": "Processed and saved successfully", "id": record.id, "name": unique_name}

    except subprocess.CalledProcessError as e:
        return {"error in script": f"Blender execution failed (returncode {e.returncode})."}
    except Exception as e:
        return {"error": str(e)}

def _transform_to_glb(name: str, db: Session) -> FileResponse | dict:
    try:
        base = safe_name(name)
        glb_path = output_glb_path(base)
        blend_input = os.path.join(OUTPUT_DIR, f"{base}.blend")

        # Cache
        if os.path.exists(glb_path):
            return FileResponse(path=glb_path, filename=f"{base}.glb", media_type="model/gltf-binary")

        # Pull .blend from DB
        rec = db.query(JointsFile).filter(JointsFile.name == name).first()
        if not rec:
            return {"error": f"No .blend stored under name '{name}'"}

        with open(blend_input, "wb") as f:
            f.write(rec.filedata)

        # Run Blender transform script
        run_blender_script(BLENDER_TRANSFORM_SCRIPT, base, blend_input)

        # Serve result
        if not os.path.exists(glb_path):
            return {"error": f"Transform complete but {glb_path} not found"}
        return FileResponse(path=glb_path, filename=f"{base}.glb", media_type="model/gltf-binary")

    except subprocess.CalledProcessError as e:
        return {"error in script": f"Blender transform failed (returncode {e.returncode})."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/transform/rig/")
def transform_rig_get(name: str, db: Session = Depends(get_db)):
    return _transform_to_glb(name, db)

@app.post("/transform/rig/")
def transform_rig_post(name: str = Form(...), db: Session = Depends(get_db)):
    return _transform_to_glb(name, db)

@app.get("/joints/")
def get_joints_files(db: Session = Depends(get_db)):
    files = db.query(JointsFile).all()
    return [{"id": f.id, "name": f.name} for f in files]

@app.get("/joints/{file_id}")
def download_joints_file(file_id: int, db: Session = Depends(get_db)):
    rec = db.query(JointsFile).filter(JointsFile.id == file_id).first()
    if not rec:
        return {"error": "File not found"}
    out = os.path.join("/tmp", f"{rec.name}.blend")
    with open(out, "wb") as f:
        f.write(rec.filedata)
    return {"message": "File restored", "filepath": out}

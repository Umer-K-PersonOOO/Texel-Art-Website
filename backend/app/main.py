# backend/app/main.py
from fastapi import FastAPI, UploadFile, HTTPException, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import Column, Integer, String, LargeBinary, UniqueConstraint, create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime
import os, subprocess, shutil, pathlib, sys, shlex, time, signal
from typing import Optional
from fastapi import Body

# Configuration
ADDON_MODULE = os.getenv("ADDON_MODULE", "BlendArMocap")
BLENDER_BIN = shutil.which("blender") or "/usr/local/bin/blender"
XVFB_RUN = shutil.which("xvfb-run")
HEADLESS = os.getenv("HEADLESS", "1") == "1"
XVFB_SCREEN = os.getenv("XVFB_WHD", "1920x1080x24")
ALLOWED_RIG_EXTS = {".blend", ".fbx", ".obj"}
RIGS_DIR = os.getenv("RIGS_DIR", "/shared/rigs")
os.makedirs(RIGS_DIR, exist_ok=True)

# NOTE: default to the installed add-on inside Blender's addons dir
MOCAP_SCRIPT = os.getenv(
    "MOCAP_SCRIPT",
    "/root/.config/blender/4.1/scripts/addons/BlendArMocap/addon_script.py",
)
TRANSFORM_SCRIPT = os.getenv(
    "TRANSFORM_SCRIPT",
    "/root/.config/blender/4.1/scripts/addons/BlendArMocap/src/transform_addon_script.py",
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/shared/in")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/shared/out")
LEGACY_OUT = os.path.expanduser(os.path.join("~", "blender_tmp"))  # legacy fallback

DEFAULT_SQLITE = "sqlite:////app/backend/mocap.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE)

# Ensure IO dirs exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LEGACY_OUT, exist_ok=True)

# Database
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

# Helpers
def safe_name(name: str) -> str:
    return pathlib.Path(name).stem.replace(" ", "_")

def find_output_blend(basename: str) -> str | None:
    cand1 = os.path.join(OUTPUT_DIR, f"{basename}.blend")
    cand2 = os.path.join(LEGACY_OUT, f"{basename}.blend")
    if os.path.exists(cand1): return cand1
    if os.path.exists(cand2): return cand2
    return None

def output_glb_path(basename: str) -> str:
    return os.path.join(OUTPUT_DIR, f"{basename}.glb")

def generate_unique_name(db: Session, base_name: str) -> str:
    count = 0
    unique_name = base_name
    while db.query(JointsFile).filter(JointsFile.name == unique_name).first():
        count += 1
        unique_name = f"{base_name}_{count}"
    return unique_name

# Blender runners (robust, with Xvfb)
def _save_rig_upload(file: UploadFile) -> str:
    ext = pathlib.Path(file.filename).suffix.lower()
    if ext not in ALLOWED_RIG_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported rig format: {ext}")
    safe = safe_name(file.filename) + ext
    dest = os.path.join(RIGS_DIR, safe)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest

def _blender_cmd(extra: list[str]) -> list[str]:
    base = [BLENDER_BIN, "--factory-startup", "--addons", ADDON_MODULE]
    cmd = base + extra
    if HEADLESS and XVFB_RUN:
        return [XVFB_RUN, "-a", "-s", f"-screen 0 {XVFB_SCREEN}"] + cmd
    return cmd

def _run(cmd: list[str]) -> None:
    # Optional: env var to tune timeout; default 15 min
    timeout_s = int(os.getenv("BLENDER_TIMEOUT", "900"))

    # Don’t PIPE; start a new process group so we can kill Xvfb+Blender together
    p = subprocess.Popen(
        cmd,
        stdout=None,
        stderr=None,
        preexec_fn=os.setsid
    )
    try:
        rc = p.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        # Kill the whole group: xvfb-run, Xvfb, and blender
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        raise HTTPException(status_code=504, detail="Blender transform timed out")

    if rc != 0:
        raise HTTPException(status_code=500, detail=f"Blender exited with code {rc}")

def run_blender_mocap(collection_name: str, file_path: str) -> None:
    if not os.path.exists(MOCAP_SCRIPT):
        raise HTTPException(status_code=500, detail=f"addon_script not found at {MOCAP_SCRIPT}")
    cmd = _blender_cmd(["--python", MOCAP_SCRIPT, "--", collection_name, file_path])
    _run(cmd)

def run_blender_transform(name: str, blend_input_path: str) -> None:
    if not os.path.exists(TRANSFORM_SCRIPT):
        raise HTTPException(status_code=500, detail=f"transform_addon_script not found at {TRANSFORM_SCRIPT}")
    cmd = _blender_cmd(["--python", TRANSFORM_SCRIPT, "--", name, blend_input_path])
    _run(cmd)

# FastAPI
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """
    Purpose: Health Check
    """
    return {"message": "Hello, World!"}


@app.post("/process/video/")
async def process_video(
    file: UploadFile = File(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Purpose: Upload and process a video into a .blend file (stored in DB)
    """
    # store upload
    original = os.path.basename(file.filename)
    safe_base = safe_name(original)
    upload_path = os.path.join(UPLOAD_DIR, original)
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # collection/output basename
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    collection_name = f"cgt_DRIVERS_{safe_base}_{stamp}"

    # run Blender
    run_blender_mocap(collection_name, upload_path)

    # find produced .blend
    blend_path = find_output_blend(collection_name)
    if not blend_path:
        raise HTTPException(
            status_code=500,
            detail=f"Expected output .blend not found for '{collection_name}' in {OUTPUT_DIR} or {LEGACY_OUT}",
        )

    # save to DB with unique logical name
    with open(blend_path, "rb") as f:
        filedata = f.read()

    unique_name = generate_unique_name(db, name)
    record = JointsFile(name=unique_name, filedata=filedata)
    db.add(record)
    db.commit()
    db.refresh(record)

    return {"message": "Processed and saved successfully", "id": record.id, "name": unique_name}

def _transform_to_glb(name: str, db: Session):
    base = safe_name(name)
    glb_path = output_glb_path(base)
    blend_input = os.path.join(OUTPUT_DIR, f"{base}.blend")

    # cached?
    if os.path.exists(glb_path):
        return FileResponse(path=glb_path, filename=f"{base}.glb", media_type="model/gltf-binary")

    # fetch .blend from DB
    rec = db.query(JointsFile).filter(JointsFile.name == name).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"No .blend stored under name '{name}'")

    with open(blend_input, "wb") as f:
        f.write(rec.filedata)

    # run Blender transform
    run_blender_transform(base, blend_input)

    if not os.path.exists(glb_path):
        raise HTTPException(status_code=500, detail=f"Transform completed but {glb_path} not found")

    return FileResponse(path=glb_path, filename=f"{base}.glb", media_type="model/gltf-binary")

@app.get("/transform/rig")
def transform_rig_get(name: str, db: Session = Depends(get_db)):
    """
    Gets .glb file using rig

    For ease of implementation.
    NOT A SAFE IMPLEMENTATION, please implement a backend-handled method.
    """
    return _transform_to_glb(name, db)

@app.post("/transform/rig/")
def transform_rig_post(
    name: str = Form(...),
    rig_ref: Optional[str] = Form(None),
    rig_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Purpose: Transform an existing .blend (from DB) into .glb using a rig
    """
    # resolve rig path (upload or reference)
    rig_path = None
    if rig_file is not None:
        rig_path = _save_rig_upload(rig_file)
    elif rig_ref:
        cand = os.path.join(RIGS_DIR, os.path.basename(rig_ref))
        if not os.path.exists(cand):
            raise HTTPException(status_code=404, detail=f"rig_ref not found: {rig_ref}")
        rig_path = cand

    if rig_path is None:
        # fall back to env RIG_BLEND_PATH (backwards compatible)
        rig_path = os.getenv("RIG_BLEND_PATH")
        if not rig_path or not os.path.exists(rig_path):
            raise HTTPException(status_code=400, detail="No rig provided. Upload rig_file or pass rig_ref.")

    # write the .blend from DB to OUTPUT_DIR/base.blend (as you already do)
    base = safe_name(name)
    glb_path = output_glb_path(base)
    blend_input = os.path.join(OUTPUT_DIR, f"{base}.blend")

    # cache?
    if os.path.exists(glb_path):
        return FileResponse(path=glb_path, filename=f"{base}.glb", media_type="model/gltf-binary")

    rec = db.query(JointsFile).filter(JointsFile.name == name).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"No .blend stored under name '{name}'")
    with open(blend_input, "wb") as f:
        f.write(rec.filedata)

    # run Blender transform with the rig path
    cmd = _blender_cmd(["--python", TRANSFORM_SCRIPT, "--", base, blend_input, rig_path])
    _run(cmd)

    if not os.path.exists(glb_path):
        raise HTTPException(status_code=500, detail=f"Transform completed but {glb_path} not found")
    return FileResponse(path=glb_path, filename=f"{base}.glb", media_type="model/gltf-binary")


@app.get("/joints/")
def get_joints_files(db: Session = Depends(get_db)):
    """
    Purpose: Access database: list all processed joint files in DB
    """
    files = db.query(JointsFile).all()
    return [{"id": f.id, "name": f.name} for f in files]

@app.get("/joints/{file_id}")
def download_joints_file(file_id: int, db: Session = Depends(get_db)):
    """
    Purpose: Retrieve a specific .blend file from DB
    """
    rec = db.query(JointsFile).filter(JointsFile.id == file_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    out = os.path.join("/tmp", f"{rec.name}.blend")
    with open(out, "wb") as f:
        f.write(rec.filedata)
    return {"message": "File restored", "filepath": out}


@app.post("/rigs/upload")
async def upload_rig(file: UploadFile = File(...)):
    """
    Purpose: Upload a rig file (.blend) for later use
    """
    path = _save_rig_upload(file)
    # optional: cheap validation (just existence); real validation happens in Blender
    return {"ok": True, "rig_ref": os.path.basename(path), "path": path}

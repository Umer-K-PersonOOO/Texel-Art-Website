# texel-art-website/Dockerfile
FROM ubuntu:22.04
ARG BLENDER_VERSION=4.1.1

ENV DEBIAN_FRONTEND=noninteractive \
    BLENDER_DIR=/opt/blender \
    PATH=/opt/blender:$PATH \
    PYTHONNOUSERSITE=1 \
    ADDON_MODULE=BlendArMocap \
    UPLOAD_DIR=/shared/in \
    OUTPUT_DIR=/shared/out \
    HEADLESS=1
ENV XDG_RUNTIME_DIR=/tmp

# 1) System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates xvfb xauth ffmpeg curl \
    libgl1 libxi6 libxrender1 libxfixes3 libxkbcommon0 libx11-6 libxxf86vm1 \
    libxcursor1 libxrandr2 libsm6 libice6 libglu1-mesa libegl1 \
    python3 python3-pip python3-venv build-essential git && \
    rm -rf /var/lib/apt/lists/*

# 2) Blender
RUN wget -q https://download.blender.org/release/Blender4.1/blender-${BLENDER_VERSION}-linux-x64.tar.xz -O /tmp/blender.tar.xz && \
    tar -xf /tmp/blender.tar.xz -C /opt && \
    mv /opt/blender-${BLENDER_VERSION}-linux-x64 ${BLENDER_DIR} && \
    ln -s ${BLENDER_DIR}/blender /usr/local/bin/blender

WORKDIR /app

# 3) Backend
COPY backend /app/backend

# 4) Add-on
COPY Texel-Art-Media /opt/addons/${ADDON_MODULE}
RUN mkdir -p /root/.config/blender/4.1/scripts/addons && \
    rm -rf /root/.config/blender/4.1/scripts/addons/${ADDON_MODULE} && \
    cp -r /opt/addons/${ADDON_MODULE} /root/.config/blender/4.1/scripts/addons/

# 5) API deps (system Python)
RUN pip3 install --no-cache-dir -r /app/backend/requirements.txt

# 6) Blender’s Python deps
# If your add-on requirements file exists and is NON-empty, it will be used.
COPY Texel-Art-Media/requirements.txt /tmp/texel-addon-reqs.txt
RUN blender -b --python-expr "import ensurepip,sys,subprocess; ensurepip.bootstrap(); subprocess.check_call([sys.executable,'-m','pip','install','--upgrade','pip'])" && \
    bash -lc 'if [ -s /tmp/texel-addon-reqs.txt ]; then \
                 blender -b --python-expr "import sys,subprocess; subprocess.check_call([sys.executable,\"-m\",\"pip\",\"install\",\"-r\",\"/tmp/texel-addon-reqs.txt\"])"; \
              else \
                 blender -b --python-expr "import sys,subprocess; subprocess.check_call([sys.executable,\"-m\",\"pip\",\"install\",\"mediapipe\",\"opencv-contrib-python-headless\",\"numpy\",\"protobuf==3.20.2\"])"; \
              fi'

EXPOSE 8000
WORKDIR /app/backend
CMD ["python3","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

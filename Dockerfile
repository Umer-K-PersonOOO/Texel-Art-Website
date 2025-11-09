# texel-art-website/Dockerfile
FROM ubuntu:22.04
ARG BLENDER_VERSION=4.1.1

ENV DEBIAN_FRONTEND=noninteractive \
    BLENDER_DIR=/opt/blender \
    PATH=/opt/blender:$PATH \
    ADDON_MODULE=BlendArMocap \
    UPLOAD_DIR=/shared/in \
    OUTPUT_DIR=/shared/out \
    HEADLESS=1 \
    XDG_RUNTIME_DIR=/tmp

# 1) System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates xvfb xauth ffmpeg curl \
    libgl1 libxi6 libxrender1 libxfixes3 libxkbcommon0 libx11-6 libxxf86vm1 \
    libxcursor1 libxrandr2 libsm6 libice6 libglu1-mesa libegl1 \
    python3 python3-pip build-essential git && \
    rm -rf /var/lib/apt/lists/*

# 2) Blender
RUN wget -q https://download.blender.org/release/Blender4.1/blender-${BLENDER_VERSION}-linux-x64.tar.xz -O /tmp/blender.tar.xz && \
    tar -xf /tmp/blender.tar.xz -C /opt && \
    mv /opt/blender-${BLENDER_VERSION}-linux-x64 ${BLENDER_DIR} && \
    ln -s ${BLENDER_DIR}/blender /usr/local/bin/blender

# 3) Backend
WORKDIR /app
COPY backend /app/backend

# 4) Add-on
COPY Texel-Art-Media /opt/addons/${ADDON_MODULE}
RUN mkdir -p /root/.config/blender/4.1/scripts/addons && \
    rm -rf /root/.config/blender/4.1/scripts/addons/${ADDON_MODULE} && \
    cp -r /opt/addons/${ADDON_MODULE} /root/.config/blender/4.1/scripts/addons/

# 5) Python environment for Blender add-on
RUN ${BLENDER_DIR}/4.1/python/bin/python3.11 -m ensurepip && \
    ${BLENDER_DIR}/4.1/python/bin/python3.11 -m pip install --upgrade pip setuptools wheel && \
    ${BLENDER_DIR}/4.1/python/bin/python3.11 -m pip install \
    numpy \
    opencv-contrib-python-headless \
    protobuf \
    mediapipe

# 6) Backend dependencies (system Python)
RUN python3 -m pip install --no-cache-dir -r /app/backend/requirements.txt

EXPOSE 8000
WORKDIR /app/backend

# 8) Run backend server
CMD ["python3","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]

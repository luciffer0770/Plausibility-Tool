# Bosch Plausibility Check — Codespaces: Python + Tk + noVNC stack
FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    xvfb \
    fluxbox \
    x11vnc \
    novnc \
    xterm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir websockify

# Context is workspace root (see devcontainer.json build.context)
COPY .devcontainer/start-pruf-desktop.sh /usr/local/bin/start-pruf-desktop.sh
RUN chmod +x /usr/local/bin/start-pruf-desktop.sh

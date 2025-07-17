FROM node:lts-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin/playwright_browsers

# 1. Install System Dependencies (Least frequent changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    xvfb \
    x11vnc \
    openbox \
    python3 \
    python3-pip \
    python3-tk \
    scrot \
    xclip \
    libxtst6 \
    libxrandr2 \
    libxfixes3 \
    libxdamage1 \
    libxcursor1 \
    libnss3 \
    libgtk-3-0 \
    libasound2 \
    supervisor \
    xauth \
    x11-xserver-utils \
    util-linux \
    bsdutils \
    gnome-screenshot \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 1.5. Install noVNC for web-based VNC access
RUN git clone https://github.com/novnc/noVNC.git /usr/local/novnc \
    && git clone https://github.com/novnc/websockify.git /usr/local/novnc/utils/websockify \
    && chmod +x /usr/local/novnc/utils/websockify/run

# 2. Install Node.js Dependencies (Infrequent changes)
WORKDIR /app
COPY docker_assets/browser/package.json docker_assets/browser/package-lock.json* ./
RUN npm install .

# 3. Install Playwright (Infrequent changes)
RUN npx playwright install --with-deps

# 4. Install Python base packages (Infrequent changes)
RUN pip3 install --break-system-packages --no-cache-dir \
    autogen-core \
    docker \
    playwright==1.53.0 \
    pydantic \
    loguru \
    pyautogui==0.9.54 \
    python3-xlib \
    Pillow \
    websockets

# 5. Install the vision_assistant package (Changes when setup.py changes)
COPY vision_assistant/setup.py /app/vision_assistant/setup.py
COPY vision_assistant/src /app/vision_assistant/src
COPY vision_assistant/emr_templates /app/emr_templates
RUN pip3 install --break-system-packages /app/vision_assistant

# 6. Copy Application Code and Scripts (Most frequent changes)
COPY vision_assistant /app/vision_assistant
COPY docker_assets/browser/ /app/

# Set up file permissions and configurations
RUN chmod +x /app/start.sh \
    && chmod +x /app/x11-setup.sh \
    && chmod +x /app/entrypoint.sh
COPY docker_assets/browser/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN mkdir -p /root/.config/openbox
COPY docker_assets/browser/openbox-rc.xml /root/.config/openbox/rc.xml

# Set PYTHONPATH to include the vision assistant's src directory
ENV PYTHONPATH="/app/vision_assistant/src:/app/vision_assistant:/app/src:${PYTHONPATH}"

# Set EMR templates directory for vision_assistant
ENV VISION_ASSISTANT_TEMPLATES="/app/emr_templates"

# Set up the workspace and entrypoint
WORKDIR /workspace
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/app/start.sh"]
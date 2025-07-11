FROM node:lts-slim

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    xvfb \
    x11vnc \
    openbox \
    supervisor \
    python3 \
    python3-pip \
    util-linux \
    xauth \
    x11-xserver-utils \
    scrot \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Install noVNC
RUN git clone --depth 1 --branch v1.6.0 https://github.com/novnc/noVNC.git /usr/local/novnc \
    && git clone --depth 1 --branch v0.13.0 https://github.com/novnc/websockify /usr/local/novnc/utils/websockify

# Set up working directory
WORKDIR /app

# Install Playwright
COPY package.json package-lock.json* ./
RUN npm install .
RUN npm install \
    && npm install playwright \
    && npx playwright install --with-deps

# Install browsers with dependencies
RUN npx playwright install --with-deps chromium

# Set up supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy scripts
COPY start.sh /app/start.sh
COPY playwright-server.js /app/playwright-server.js
COPY x11-setup.sh /usr/bin/x11-setup.sh
RUN chmod +x /usr/bin/x11-setup.sh

# Make scripts executable
RUN chmod +x /app/start.sh

# Create a simple openbox configuration to only show the browser window
RUN mkdir -p /root/.config/openbox
COPY openbox-rc.xml /root/.config/openbox/rc.xml

# Expose ports: noVNC web interface, and Playwright server
EXPOSE 6080 37367

ENV PLAYWRIGHT_WS_PATH="default"

# Set the display environment variable
ENV DISPLAY=:99

RUN mkdir -p /workspace
WORKDIR /workspace

# Install pyautogui and its dependencies
RUN pip3 install --break-system-packages pyautogui python3-xlib

# Copy your application scripts
COPY pyautogui_app.py /app/pyautogui_app.py
COPY test_x11.py /app/test_x11.py

# Remove the redundant copy of playwright-server.js

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Start services
CMD ["/app/start.sh"]
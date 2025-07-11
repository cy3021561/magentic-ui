#!/bin/bash

# Wait for Xvfb to be ready
for i in $(seq 1 30); do
  if xset -q &>/dev/null; then
    echo "X server is ready!"
    break
  fi
  echo "Waiting for X server... (attempt $i/30)"
  sleep 2
done

if ! xset -q &>/dev/null; then
  echo "X server not available after 30 attempts, exiting."
  exit 1
fi

# Ensure DISPLAY is set (default :99)
if [ -z "$DISPLAY" ]; then
  export DISPLAY=:99
fi

# Configure X11 authentication ------------------------------
export XAUTHORITY=/root/.Xauthority

# Create the Xauthority file with a valid magic cookie if it does not exist
if [ ! -f "$XAUTHORITY" ]; then
  touch "$XAUTHORITY"
fi

# Add (or update) a magic cookie for the current DISPLAY.
# mcookie generates a random 128-bit hexadecimal key.
xauth add "$DISPLAY" . "$(mcookie)"

# Verify the Xauthority file was created successfully
if [ ! -f "$XAUTHORITY" ]; then
  echo "ERROR: Failed to create Xauthority file"
  exit 1
fi

echo "Xauthority file created successfully at $XAUTHORITY"

# Basic desktop tweaks --------------------------------------
# Set a plain background and disable screen savers / DPMS to avoid the screen blanking
xsetroot -solid grey
xset s off
xset -dpms
xset s noblank

echo "X11 environment configured with proper Xauthority."
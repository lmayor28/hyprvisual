#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/lmayor28/hyprvisual.git"
INSTALL_DIR="$HOME/.local/share/hyprvisual"
BIN_DIR="$HOME/.local/bin"

echo "Installing hyprvisual..."

if ! command -v git &> /dev/null; then
    echo "Error: git is not installed." && exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed." && exit 1
fi

# Clone or update
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating existing installation in $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull origin master 2>/dev/null || git -C "$INSTALL_DIR" pull origin main
else
    echo "Cloning repository to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Setup virtual environment
echo "Setting up Python environment..."
if command -v uv &> /dev/null; then
    uv --project "$INSTALL_DIR" sync
else
    python3 -m venv "$INSTALL_DIR/.venv"
    "$INSTALL_DIR/.venv/bin/pip" install -q textual
fi

# Create executable wrapper
mkdir -p "$BIN_DIR"
cat << EOF > "$BIN_DIR/hyprvisual"
#!/usr/bin/env bash
if command -v uv &> /dev/null; then
    exec uv --project "$INSTALL_DIR" run "$INSTALL_DIR/main.py" "\$@"
else
    exec "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/main.py" "\$@"
fi
EOF
chmod +x "$BIN_DIR/hyprvisual"

# Install .desktop file for app launchers
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"
cp "$INSTALL_DIR/hyprvisual.desktop" "$APPS_DIR/hyprvisual.desktop"

echo ""
echo "hyprvisual installed successfully."
echo "Run it with: hyprvisual"
echo "(Make sure '$BIN_DIR' is in your PATH)"

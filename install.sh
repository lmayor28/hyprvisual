#!/usr/bin/env bash
set -e

echo "🚀 Installing hyprmonitor..."

# Change this to your actual GitHub repository URL once uploaded
REPO_URL="https://github.com/yourusername/hyprmonitor.git"
INSTALL_DIR="$HOME/.local/share/hyprmonitor"
BIN_DIR="$HOME/.local/bin"

# 1. Ensure Dependencies
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed."
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed."
    exit 1
fi

# 2. Clone or Update Repository
if [ -d "$INSTALL_DIR" ]; then
    echo "🔄 Updating existing installation in $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull origin master || git pull origin main
else
    echo "📥 Cloning repository to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Setup Virtual Environment
echo "📦 Setting up Python virtual environment..."
cd "$INSTALL_DIR/display-tui"

if command -v uv &> /dev/null; then
    echo "⚡ Using 'uv' for lightning-fast setup..."
    uv venv
    uv pip install -e .
else
    echo "🐍 Using standard 'pip'..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
fi

# 4. Create Executable Wrapper
echo "🔗 Creating command-line wrapper..."
mkdir -p "$BIN_DIR"

cat << 'EOF' > "$BIN_DIR/hyprmonitor"
#!/usr/bin/env bash
cd "$HOME/.local/share/hyprmonitor/display-tui"

# Use uv if available, otherwise fallback to standard venv python
if command -v uv &> /dev/null; then
    exec uv run main.py "$@"
else
    exec "$HOME/.local/share/hyprmonitor/display-tui/.venv/bin/python" main.py "$@"
fi
EOF

chmod +x "$BIN_DIR/hyprmonitor"

export PATH="$BIN_DIR:$PATH"

echo ""
echo "✅ hyprmonitor installed successfully! 🎉"
echo ""
echo "You can now launch the layout controller from anywhere by running:"
echo "    hyprmonitor"
echo ""
echo "⚠️  Ensure '$BIN_DIR' is in your PATH in ~/.bashrc or ~/.zshrc if the command isn't found."

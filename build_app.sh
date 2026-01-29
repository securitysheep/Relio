#!/bin/bash
# ============================================================
# Relio - macOS Application Build Script
# Relationship Intelligence Orchestrator
# ============================================================
# Usage: ./build_app.sh
#
# This script will:
# 1. Check and install required build tools
# 2. Generate application icon from logo.png
# 3. Build the application using PyInstaller
# 4. Move the packaged .app to project root
# ============================================================

set -e  # Exit on error

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored messages
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
header() { echo -e "${CYAN}$1${NC}"; }

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

header "============================================================"
header "  Relio - Relationship Intelligence Orchestrator"
header "  macOS Application Builder"
header "============================================================"
echo ""

# ============================================================
# Step 1: Check Python environment
# ============================================================
info "Checking Python environment..."

# Try to activate conda environment
if [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniforge3/etc/profile.d/conda.sh"
    conda activate data_science 2>/dev/null || warn "Could not activate data_science environment, using current environment"
fi

# Check Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    error "Python not found. Please install Python 3.9+"
fi

PYTHON_CMD=$(command -v python3 || command -v python)
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
info "Using Python: $PYTHON_VERSION"

# ============================================================
# Step 2: Install PyInstaller
# ============================================================
info "Checking PyInstaller..."

if ! $PYTHON_CMD -c "import PyInstaller" 2>/dev/null; then
    warn "PyInstaller not installed, installing..."
    $PYTHON_CMD -m pip install pyinstaller -q
    success "PyInstaller installed"
else
    info "PyInstaller is ready"
fi

# ============================================================
# Step 3: Generate application icon from logo.png
# ============================================================
info "Generating application icon..."

LOGO_PATH="logo.png"
ICON_PATH="assets/AppIcon.icns"

if [ -f "$LOGO_PATH" ]; then
    info "Found logo.png, generating icns..."
    
    # Create iconset directory
    ICONSET_DIR="assets/AppIcon.iconset"
    mkdir -p "$ICONSET_DIR"
    
    # Generate different sizes using sips
    sips -z 16 16     "$LOGO_PATH" --out "$ICONSET_DIR/icon_16x16.png" 2>/dev/null
    sips -z 32 32     "$LOGO_PATH" --out "$ICONSET_DIR/icon_16x16@2x.png" 2>/dev/null
    sips -z 32 32     "$LOGO_PATH" --out "$ICONSET_DIR/icon_32x32.png" 2>/dev/null
    sips -z 64 64     "$LOGO_PATH" --out "$ICONSET_DIR/icon_32x32@2x.png" 2>/dev/null
    sips -z 128 128   "$LOGO_PATH" --out "$ICONSET_DIR/icon_128x128.png" 2>/dev/null
    sips -z 256 256   "$LOGO_PATH" --out "$ICONSET_DIR/icon_128x128@2x.png" 2>/dev/null
    sips -z 256 256   "$LOGO_PATH" --out "$ICONSET_DIR/icon_256x256.png" 2>/dev/null
    sips -z 512 512   "$LOGO_PATH" --out "$ICONSET_DIR/icon_256x256@2x.png" 2>/dev/null
    sips -z 512 512   "$LOGO_PATH" --out "$ICONSET_DIR/icon_512x512.png" 2>/dev/null
    sips -z 1024 1024 "$LOGO_PATH" --out "$ICONSET_DIR/icon_512x512@2x.png" 2>/dev/null
    
    # Generate icns file
    iconutil -c icns "$ICONSET_DIR" -o "$ICON_PATH" 2>/dev/null
    
    # Clean up iconset
    rm -rf "$ICONSET_DIR"
    
    if [ -f "$ICON_PATH" ]; then
        success "Application icon generated"
    else
        warn "Icon generation failed, will use default"
    fi
else
    warn "logo.png not found, checking for existing icon..."
    if [ -f "$ICON_PATH" ]; then
        info "Using existing AppIcon.icns"
    else
        warn "No icon available, will use system default"
    fi
fi

# ============================================================
# Step 4: Clean old build files
# ============================================================
info "Cleaning old build files..."
rm -rf build dist
rm -rf "Relio.app" "对话决策系统.app"
success "Cleaned"

# ============================================================
# Step 5: Build application
# ============================================================
info "Building Relio..."
echo ""

$PYTHON_CMD -m PyInstaller "Relio.spec" --noconfirm

# ============================================================
# Step 6: Move build result
# ============================================================
if [ -d "dist/Relio.app" ]; then
    # Move new app to project root
    mv "dist/Relio.app" .
    
    # Clean build directories
    rm -rf build dist
    
    # Get app size
    APP_SIZE=$(du -sh "Relio.app" | cut -f1)
    
    success "============================================================"
    success "  Build Complete!"
    success "============================================================"
    echo ""
    info "Application: ${SCRIPT_DIR}/Relio.app"
    info "Size: ${APP_SIZE}"
    echo ""
    info "You can now:"
    info "  1. Double-click Relio.app to run"
    info "  2. Drag it to /Applications folder to install"
    echo ""
else
    error "Build failed, Relio.app not found"
fi

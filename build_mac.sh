#!/usr/bin/env bash
# build_mac.sh — Build RF-DIAG.app for macOS
# Usage:  cd Version9 && bash build_mac.sh
set -euo pipefail

echo "RF-DIAG macOS Build"
echo "==================="
echo ""

# Prefer python3.12 if available (CoreWLAN works reliably on 3.12)
PYTHON=$(command -v python3.12 2>/dev/null || command -v python3)
echo "Python: $($PYTHON --version)"
echo ""

# Install / upgrade required packages
echo "Installing dependencies..."
$PYTHON -m pip install --quiet --upgrade \
    flask \
    paramiko \
    pyinstaller \
    pyobjc-framework-CoreWLAN

echo "Dependencies OK."
echo ""

# Clean previous build artifacts
rm -rf build/ dist/

# Run PyInstaller
echo "Building RF-DIAG.app ..."
$PYTHON -m PyInstaller RF_DIAG.spec --noconfirm

echo ""
echo "Build complete."
echo ""
echo "  App location: dist/RF-DIAG.app"
echo ""
echo "Next steps:"
echo "  1.  open dist/RF-DIAG.app"
echo "  2.  macOS will ask for Location Services permission — click Allow"
echo "  3.  Your browser opens automatically at http://127.0.0.1:5001"
echo ""
echo "To allow Location Services after first launch:"
echo "  System Settings > Privacy & Security > Location Services > RF-DIAG"

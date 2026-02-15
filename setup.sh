#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Taisho Canon Digest Detection Pipeline Setup ==="
echo

# --- CBETA XML Corpus ---
if [ -d "xml/T" ] && [ "$(ls xml/T/ 2>/dev/null | head -1)" ]; then
    echo "[OK] CBETA XML corpus already present at xml/T/"
else
    echo "[1/2] Downloading CBETA TEI P5b XML corpus (~2.4 GB)..."
    echo "      Source: https://github.com/cbeta-org/xml-p5"
    if [ ! -d "cbeta-xml-p5" ]; then
        git clone --depth 1 https://github.com/cbeta-org/xml-p5.git cbeta-xml-p5
    else
        echo "      (cbeta-xml-p5/ already cloned)"
    fi
    echo "[2/2] Linking Taisho volume into xml/T/..."
    mkdir -p xml
    ln -sfn "$(pwd)/cbeta-xml-p5/T" xml/T
    echo "[OK] CBETA corpus ready at xml/T/"
fi

echo

# --- Python dependencies ---
echo "Checking Python dependencies..."
python3 -c "import lxml, tqdm, numpy" 2>/dev/null && echo "[OK] All Python dependencies installed" || {
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
}

echo
echo "=== Setup complete ==="
echo
echo "Run the pipeline:"
echo "  python3 -m digest_detector.pipeline"
echo
echo "Run tests:"
echo "  python3 -m pytest tests/ -v"

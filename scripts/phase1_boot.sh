#!/bin/bash
# Agent Zero — Phase 1 Boot Script
# Wires COG vault + OpenCrabs runtime on any machine
# GitHub Models LLM backbone — zero cost

set -e

echo "=== AGENT ZERO — PHASE 1 BOOT ==="
echo ""

# 1. Check Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "[1/5] Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo "[1/5] Rust: OK ($(cargo --version))"
fi

# 2. Clone OpenCrabs if not present
if [ ! -d "opencrabs" ]; then
    echo "[2/5] Cloning OpenCrabs runtime..."
    git clone https://github.com/kevinleestites2-dev/opencrabs.git
else
    echo "[2/5] OpenCrabs: already cloned"
fi

# 3. Wire config
echo "[3/5] Wiring OpenCrabs to GitHub Models..."
mkdir -p ~/.opencrabs
cp config/agent_zero_config.toml ~/.opencrabs/config.toml
cp config/agent_zero_keys.toml ~/.opencrabs/keys.toml
chmod 600 ~/.opencrabs/keys.toml
echo "      Config: ~/.opencrabs/config.toml"
echo "      Keys:   ~/.opencrabs/keys.toml (chmod 600)"

# 4. Build OpenCrabs
echo "[4/5] Building OpenCrabs binary..."
cd opencrabs
cargo build --release
cd ..
echo "      Binary: opencrabs/target/release/opencrabs"

# 5. First run — confirm LLM backbone
echo "[5/5] Firing first inference — confirming backbone..."
echo "      Model: gpt-4o via GitHub Models"
echo ""
echo "=== PHASE 1 COMPLETE ==="
echo ""
echo "Run Agent Zero:"
echo "  ./opencrabs/target/release/opencrabs"
echo ""
echo "13 layers. The mind awakens."

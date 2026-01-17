#!/bin/bash
set -e

echo "====================PYTHON START===================="

echo "====================PYTHON 3.13===================="

apt clean && apt-get update && apt-get -y upgrade

# install python 3.13 globally
apt-get install -y --no-install-recommends \
    python3.13 python3.13-venv 
    #python3.13-dev


echo "====================PYTHON 3.13 VENV===================="

# create and activate default venv
python3.13 -m venv /opt/venv
source /opt/venv/bin/activate

# upgrade pip and install static packages
pip install --no-cache-dir --upgrade pip ipython requests

echo "====================PYTHON PYVENV===================="

# Install pyenv build dependencies.
apt-get install -y --no-install-recommends \
    make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv globally
git clone https://github.com/pyenv/pyenv.git /opt/pyenv

# Setup environment variables for pyenv to be available system-wide
cat > /etc/profile.d/pyenv.sh <<'EOF'
export PYENV_ROOT="/opt/pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
EOF

# fix permissions
chmod +x /etc/profile.d/pyenv.sh

# Source pyenv environment to make it available in this script
source /etc/profile.d/pyenv.sh

# Install Python 3.12.4
echo "====================PYENV 3.12 VENV===================="
pyenv install 3.12.4

/opt/pyenv/versions/3.12.4/bin/python -m venv /opt/venv-a0
source /opt/venv-a0/bin/activate

# upgrade pip and install static packages
pip install --no-cache-dir --upgrade pip

# Install some packages in specific variants
pip install --no-cache-dir \
    torch==2.4.0 \
    torchvision==0.19.0 \
    --index-url https://download.pytorch.org/whl/cpu

echo "====================PYTHON UV ===================="

curl -Ls https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh

# clean up pip cache
pip cache purge

echo "====================PYTHON END===================="

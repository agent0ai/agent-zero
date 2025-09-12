#!/bin/bash
set -e

echo "====================PYENV START===================="

# Install pyenv build dependencies.
apt-get install -y --no-install-recommends \
    make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv for root user
git clone https://github.com/pyenv/pyenv.git /root/.pyenv

# Setup environment variables for pyenv to be available system-wide
cat > /etc/profile.d/pyenv.sh <<'EOF'
export PYENV_ROOT="/root/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
EOF

chmod +x /etc/profile.d/pyenv.sh

# Source pyenv environment to make it available in this script
source /etc/profile.d/pyenv.sh

# Install Python 3.12.4
echo "====================PYENV INSTALLING PYTHON 3.12.4===================="
pyenv install 3.12.4

/root/.pyenv/versions/3.12.4/bin/python -m venv /opt/venv-a0

echo "====================PYENV END===================="
#!/bin/bash
set -e

# Keep this final cleanup as a safeguard for future install steps. Each current
# apt installation layer also removes its own lists before that layer ends.
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

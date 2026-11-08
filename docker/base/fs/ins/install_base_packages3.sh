#!/bin/bash
set -e

echo "====================BASE PACKAGES3 START===================="

# Node and bundled npm are copied from the official Node image by Dockerfile.
node --version
npm --version

echo "====================BASE PACKAGES3 END===================="

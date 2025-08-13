#!/bin/bash

cd $(dirname $0)

if [ ! -d "./mcp/dav-mcp-server" ]; then
  git clone https://github.com/jahfer/dav-mcp-server ./mcp/dav-mcp-server
fi

cd ./mcp/dav-mcp-server

if [ ! -d "node_modules" ]; then
  npm install
  npm link
fi

if [ ! -d "build" ]; then
  npm run build
fi

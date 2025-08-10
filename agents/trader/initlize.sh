#!/bin/bash

cd $(dirname $0)

mkdir ./mcp
cd ./mcp

git clone https://github.com/TermiX-official/binance-mcp
git clone https://github.com/kukapay/crypto-feargreed-mcp
git clone https://github.com/kukapay/crypto-indicators-mcp
git clone https://github.com/kukapay/cryptopanic-mcp-server
git clone https://github.com/Nayshins/mcp-server-ccxt
git clone https://github.com/kukapay/uniswap-pools-mcp
git clone https://github.com/kukapay/uniswap-trader-mcp

for package_json in $(ls -d */package.json); do
  dir=$(dirname $package_json)
  echo "Initializing $dir"
  cd $dir
  npm install
  cd ..
done

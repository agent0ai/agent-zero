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
git clone https://github.com/Nayshins/mcp-server-ccxt
git clone https://github.com/snjyor/binance-mcp
# git clone https://github.com/kydlikebtc/mcp-server-bn
git clone https://github.com/TermiX-official/binance-mcp mcp-server-binance


for package_json in $(ls -d */package.json); do
  dir=$(dirname $package_json)
  if [ "$dir" == "crypto-indicators-mcp" ]; then
    npm install indicatorts --save
  fi
  echo "Initializing $dir"
  cd $dir
  npm install
  npm install @binance/connector-typescript --save
  npm run build || true
  npm link
  cd ..
done

export function generateSalt(web3) {
  return web3.utils.randomHex(32);
}

export function buildCommitment(web3, move, salt, account, gameId) {
  return web3.utils.soliditySha3(
    { type: "uint8", value: Number(move) },
    { type: "bytes32", value: salt },
    { type: "address", value: account },
    { type: "uint256", value: gameId }
  );
}

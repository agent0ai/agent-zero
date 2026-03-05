require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const MUMBAI_RPC_URL = process.env.MUMBAI_RPC_URL || "";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "";

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks: {
    hardhat: {},
    mumbai: {
      url: MUMBAI_RPC_URL,
      chainId: 80001,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
  },
};

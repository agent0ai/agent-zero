import Web3 from "web3";
import rockPaperScissorsAbi from "../contracts/rockPaperScissorsAbi.json";

export async function connectWallet() {
  if (!window.ethereum) {
    throw new Error("MetaMask is required");
  }

  const web3 = new Web3(window.ethereum);
  await window.ethereum.request({ method: "eth_requestAccounts" });
  const [account] = await web3.eth.getAccounts();
  const chainId = await web3.eth.getChainId();

  return { web3, account, chainId: Number(chainId) };
}

export function getGameContract(web3) {
  const contractAddress = import.meta.env.VITE_GAME_CONTRACT_ADDRESS;
  if (!contractAddress) {
    throw new Error("VITE_GAME_CONTRACT_ADDRESS is not set");
  }
  return new web3.eth.Contract(rockPaperScissorsAbi, contractAddress);
}

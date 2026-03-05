<template>
  <v-app>
    <v-main>
      <v-container class="py-8">
        <v-row>
          <v-col cols="12" md="6">
            <v-card class="mb-4">
              <v-card-title>Wallet + Lobby</v-card-title>
              <v-card-text>
                <v-btn color="primary" @click="connectWalletAction">Connect MetaMask</v-btn>
                <p class="mt-3 mb-1"><strong>Account:</strong> {{ account || "Not connected" }}</p>
                <p class="mb-4"><strong>Chain ID:</strong> {{ chainId || "-" }}</p>

                <v-text-field
                  v-model="wagerAmount"
                  label="Wager (USDC)"
                  hint="Lobby matching allows +/-10%"
                  persistent-hint
                />
                <v-btn color="secondary" @click="matchLobby">Find Match / Open Room</v-btn>

                <div v-if="room" class="mt-4">
                  <p><strong>Room:</strong> {{ room.id }}</p>
                  <p><strong>Status:</strong> {{ room.status }}</p>
                  <p><strong>Creator:</strong> {{ room.creator_wallet }}</p>
                  <p><strong>Opponent:</strong> {{ room.opponent_wallet || "Waiting..." }}</p>
                </div>
              </v-card-text>
            </v-card>

            <v-card>
              <v-card-title>Live Lobby Feed</v-card-title>
              <v-card-text>
                <v-list density="compact" lines="two">
                  <v-list-item v-for="event in liveEvents" :key="event.id">
                    <v-list-item-title>{{ event.event }}</v-list-item-title>
                    <v-list-item-subtitle>
                      room={{ event.payload.id }} status={{ event.payload.status }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="6">
            <v-card class="mb-4">
              <v-card-title>On-Chain Game Actions</v-card-title>
              <v-card-text>
                <v-text-field
                  v-model="contractGameId"
                  label="Contract Game ID"
                  hint="Set after create/join"
                  persistent-hint
                />
                <v-btn class="mr-2 mb-2" color="primary" @click="createOnchainGame">Create Game</v-btn>
                <v-btn class="mb-2" color="secondary" @click="joinOnchainGame">Join Game</v-btn>

                <v-select
                  v-model="selectedMove"
                  :items="moveOptions"
                  item-title="label"
                  item-value="value"
                  label="Select Move"
                />
                <v-text-field v-model="salt" label="Salt (bytes32 hex)" />
                <v-btn class="mr-2 mb-2" @click="generateNewSalt">Generate Salt</v-btn>
                <v-btn class="mr-2 mb-2" color="primary" @click="commitOnchainMove">Commit Move</v-btn>
                <v-btn class="mr-2 mb-2" color="secondary" @click="revealOnchainMove">Reveal Move</v-btn>
                <v-btn class="mb-2" color="warning" @click="forceSettleGame">Force Settle</v-btn>
              </v-card-text>
            </v-card>

            <v-card>
              <v-card-title>Monetization Endpoints</v-card-title>
              <v-card-text>
                <v-text-field v-model="swap.fromToken" label="From Token Address" />
                <v-text-field v-model="swap.toToken" label="To Token Address" />
                <v-text-field v-model="swap.amount" label="Amount (base units)" />
                <v-btn class="mb-3" color="primary" @click="fetchSwapQuote">Get 1inch Quote</v-btn>
                <pre v-if="lastQuote">{{ lastQuote }}</pre>

                <v-divider class="my-4" />
                <v-text-field v-model="yieldForm.principalWei" label="Principal (wei)" />
                <v-text-field v-model="yieldForm.aprBps" label="APR (bps)" />
                <v-text-field v-model="yieldForm.days" label="Days" />
                <v-btn color="secondary" @click="estimateYield">Estimate Aave Yield</v-btn>
                <p v-if="lastYieldEstimate" class="mt-3">
                  Estimated Yield: {{ lastYieldEstimate.estimated_yield_wei }} wei
                </p>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <v-alert class="mt-4" type="info" variant="tonal" v-if="statusMessage">
          {{ statusMessage }}
        </v-alert>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "./services/api";
import { connectWallet, getGameContract } from "./services/web3";
import { buildCommitment, generateSalt } from "./utils/commitment";

const account = ref("");
const chainId = ref(null);
const web3 = ref(null);
const contract = ref(null);
const room = ref(null);
const liveEvents = ref([]);
const statusMessage = ref("");

const wagerAmount = ref("10.0");
const contractGameId = ref("");
const selectedMove = ref(1);
const salt = ref("");

const moveOptions = [
  { label: "Rock", value: 1 },
  { label: "Paper", value: 2 },
  { label: "Scissors", value: 3 },
];

const swap = ref({
  fromToken: "0x0000000000000000000000000000000000001010",
  toToken: "0x0000000000000000000000000000000000001011",
  amount: "1000000",
});
const lastQuote = ref("");

const yieldForm = ref({
  principalWei: "1000000000000000000",
  aprBps: "600",
  days: "30",
});
const lastYieldEstimate = ref(null);

function deriveWsUrl() {
  const configured = import.meta.env.VITE_BACKEND_WS_URL;
  if (configured) return configured;
  const apiUrl = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000/api";
  const base = apiUrl.replace("/api", "");
  return base.replace("http://", "ws://").replace("https://", "wss://");
}

function usdcToBaseUnits(amountString) {
  const parsed = Number(amountString);
  if (Number.isNaN(parsed) || parsed <= 0) {
    throw new Error("Invalid USDC amount");
  }
  return Math.round(parsed * 1_000_000).toString();
}

function prependEvent(event, payload) {
  liveEvents.value = [{ id: `${Date.now()}-${Math.random()}`, event, payload }, ...liveEvents.value].slice(0, 20);
}

async function connectWalletAction() {
  try {
    const connected = await connectWallet();
    web3.value = connected.web3;
    account.value = connected.account;
    chainId.value = connected.chainId;
    contract.value = getGameContract(web3.value);
    statusMessage.value = "Wallet connected. Ensure your contract address/env is set.";
    if (!salt.value) {
      salt.value = generateSalt(web3.value);
    }
  } catch (error) {
    statusMessage.value = `Wallet connect failed: ${error.message}`;
  }
}

async function matchLobby() {
  if (!account.value) {
    statusMessage.value = "Connect your wallet first.";
    return;
  }
  try {
    const response = await api.post("/lobby/match/", {
      wallet_address: account.value,
      wager_amount: wagerAmount.value,
    });
    room.value = response.data.room;
    statusMessage.value = response.data.matched ? "Matched with an existing room." : "Opened new room.";
  } catch (error) {
    statusMessage.value = `Lobby match failed: ${error.message}`;
  }
}

async function createOnchainGame() {
  if (!contract.value || !account.value) {
    statusMessage.value = "Connect wallet first.";
    return;
  }
  try {
    const wagerBaseUnits = usdcToBaseUnits(wagerAmount.value);
    await contract.value.methods.createGame(wagerBaseUnits).send({ from: account.value });
    const currentCounter = await contract.value.methods.gameCounter().call();
    contractGameId.value = String(currentCounter);
    statusMessage.value = `On-chain game created (id=${contractGameId.value}).`;
  } catch (error) {
    statusMessage.value = `Create game failed: ${error.message}`;
  }
}

async function joinOnchainGame() {
  if (!contract.value || !account.value) {
    statusMessage.value = "Connect wallet first.";
    return;
  }
  try {
    await contract.value.methods.joinGame(contractGameId.value).send({ from: account.value });
    statusMessage.value = "Joined on-chain game.";
  } catch (error) {
    statusMessage.value = `Join game failed: ${error.message}`;
  }
}

function generateNewSalt() {
  if (!web3.value) {
    statusMessage.value = "Connect wallet first.";
    return;
  }
  salt.value = generateSalt(web3.value);
}

async function commitOnchainMove() {
  if (!contract.value || !web3.value || !account.value || !contractGameId.value || !salt.value) {
    statusMessage.value = "Missing wallet/game/move/salt.";
    return;
  }
  try {
    const commitment = buildCommitment(web3.value, selectedMove.value, salt.value, account.value, contractGameId.value);
    await contract.value.methods.commitMove(contractGameId.value, commitment).send({ from: account.value });
    statusMessage.value = "Move committed.";
  } catch (error) {
    statusMessage.value = `Commit failed: ${error.message}`;
  }
}

async function revealOnchainMove() {
  if (!contract.value || !account.value) {
    statusMessage.value = "Connect wallet first.";
    return;
  }
  try {
    await contract.value.methods
      .revealMove(contractGameId.value, selectedMove.value, salt.value)
      .send({ from: account.value });
    statusMessage.value = "Move revealed.";
  } catch (error) {
    statusMessage.value = `Reveal failed: ${error.message}`;
  }
}

async function forceSettleGame() {
  if (!contract.value || !account.value) {
    statusMessage.value = "Connect wallet first.";
    return;
  }
  try {
    await contract.value.methods.forceSettle(contractGameId.value).send({ from: account.value });
    statusMessage.value = "Force-settle transaction sent.";
  } catch (error) {
    statusMessage.value = `Force settle failed: ${error.message}`;
  }
}

async function fetchSwapQuote() {
  if (!account.value) {
    statusMessage.value = "Connect wallet first.";
    return;
  }
  try {
    const response = await api.post("/swap/quote/", {
      wallet_address: account.value,
      from_token: swap.value.fromToken,
      to_token: swap.value.toToken,
      amount: swap.value.amount,
      chain_id: 137,
    });
    lastQuote.value = JSON.stringify(response.data, null, 2);
    statusMessage.value = "Fetched 1inch quote and logged swap metadata.";
  } catch (error) {
    statusMessage.value = `Swap quote failed: ${error.message}`;
  }
}

async function estimateYield() {
  if (!account.value) {
    statusMessage.value = "Connect wallet first.";
    return;
  }
  try {
    const response = await api.post("/yield/estimate/", {
      wallet_address: account.value,
      principal_wei: yieldForm.value.principalWei,
      apr_bps: Number(yieldForm.value.aprBps),
      days: Number(yieldForm.value.days),
    });
    lastYieldEstimate.value = response.data;
    statusMessage.value = "Yield estimate stored.";
  } catch (error) {
    statusMessage.value = `Yield estimate failed: ${error.message}`;
  }
}

function connectLobbySocket() {
  const wsUrl = `${deriveWsUrl()}/ws/lobby/`;
  const socket = new WebSocket(wsUrl);
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    prependEvent(data.event, data.payload);
  };
}

onMounted(() => {
  connectLobbySocket();
});
</script>

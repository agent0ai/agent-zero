# Rock-Paper-Scissors USDC Wagering (Polygon Starter)

This folder contains a full starter stack for a fair, commit-reveal Rock-Paper-Scissors wagering game:

- **Smart contract** (Solidity + Hardhat)
- **Backend API** (Django + DRF + Channels)
- **Frontend app** (Vue + Vuetify + Web3.js)

## 1) Architecture Highlights

### Fairness (commit-reveal)
- Players submit a commitment hash (`move + salt + player + gameId`) first.
- Players reveal the original move and salt later.
- Contract verifies reveal hashes match commitments.

### Security controls
- Uses `SafeERC20` + `ReentrancyGuard`.
- Timeouts for commit and reveal phases.
- `forceSettle` path prevents games from staying stuck.

### Fee model
- `feePercentage = 15` with scale `1000` => **1.5%**
- Fee is applied to winner payouts and tracked in `accumulatedFees`.

### Monetization endpoints
- Backend endpoint for **1inch quote** capture + swap metadata logging.
- Backend endpoint for **Aave yield estimate** logging (replace estimator with live reserve reads in production).

---

## 2) Project Layout

```text
rps-wagering/
  contracts/   # Hardhat + Solidity + tests + deploy script
  backend/     # Django API + Channels websocket + tests
  frontend/    # Vue app with wallet + lobby + game controls
```

---

## 3) Smart Contract (Mumbai)

### Setup
```bash
cd rps-wagering/contracts
cp .env.example .env
npm install
```

Edit `.env`:
- `MUMBAI_RPC_URL` (Alchemy/Infura URL)
- `PRIVATE_KEY` (deployer key)
- `USDC_MUMBAI` (Mumbai USDC test token or mock token)

### Test locally
```bash
npm run test
```

### Deploy to Mumbai
```bash
npm run deploy:mumbai
```

Save the deployed contract address and place it in:
- `frontend/.env` as `VITE_GAME_CONTRACT_ADDRESS`

---

## 4) Backend (Django + Channels)

### Setup
```bash
cd rps-wagering/backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
```

### Run tests
```bash
python3 manage.py test
```

### Run server
```bash
python3 manage.py runserver 0.0.0.0:8000
```

### API endpoints
- `GET /api/health/`
- `POST /api/lobby/match/` (match within +/-10% wager)
- `GET /api/lobby/rooms/`
- `POST /api/swap/quote/` (1inch quote + swap log)
- `POST /api/yield/estimate/`

### WebSocket
- `ws://localhost:8000/ws/lobby/`

> Redis is supported via `CHANNEL_LAYER_BACKEND=redis`, but local default is in-memory for easy startup.

---

## 5) Frontend (Vue + Vuetify + Web3.js)

### Setup
```bash
cd rps-wagering/frontend
cp .env.example .env
npm install
```

Update `.env`:
- `VITE_BACKEND_API_URL=http://localhost:8000/api`
- `VITE_BACKEND_WS_URL=ws://localhost:8000`
- `VITE_GAME_CONTRACT_ADDRESS=<deployed_contract>`

### Run
```bash
npm run dev
```

### Build
```bash
npm run build
```

---

## 6) Deployment Notes

### Backend (Heroku)
- Add environment variables from `backend/.env.example`.
- Set `CHANNEL_LAYER_BACKEND=redis` and provision Redis.
- Run `python3 manage.py migrate` in release phase.

### Frontend (Vercel)
- Set Vite env vars in Vercel project settings.
- Build command: `npm run build`
- Output directory: `dist`

---

## 7) Next Steps for Production Readiness

- Add wallet signature auth / nonce challenge to backend.
- Add explicit on-chain room/game linking in backend DB.
- Integrate live Aave reserve/APY reads through Web3.
- Add quote-to-swap execution flow with affiliate fee tracking.
- Add monitoring/alerting for failed settles and stuck rooms.

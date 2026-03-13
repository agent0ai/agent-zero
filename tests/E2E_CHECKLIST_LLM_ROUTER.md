# LLM Router — Manual E2E Validation Checklist

Use this checklist after automated tests pass to validate the full UI → API → Service integration.

## Prerequisites

- [ ] App running: `python run_ui.py` or Docker container (`docker run -p 50080:80`)
- [ ] Ollama running locally: `ollama serve` (and at least one model pulled, e.g., `ollama pull qwen2.5-coder:3b`)
- [ ] At least one cloud API key configured (OpenAI/Anthropic) — optional but recommended
- [ ] Browser open at `http://localhost:50080` (or your port)

---

## 1. Settings Toggle (fixes "cannot convert undefined to object")

| # | Step | Expected | Pass |
|---|------|----------|------|
| 1.1 | Open **Settings** → **LLM Router** tab | Dashboard loads without JS console errors | ☐ |
| 1.2 | Toggle **"Enable LLM Router"** ON | Toggle flips, no error toast, stat cards appear | ☐ |
| 1.3 | Check browser console (F12) | No `"cannot convert undefined to object"` error | ☐ |
| 1.4 | Reload page, re-open LLM Router settings | Toggle shows ON (persisted) | ☐ |
| 1.5 | Toggle OFF, reload, re-check | Toggle shows OFF (persisted) | ☐ |

---

## 2. Dashboard Stat Cards (camelCase fix)

| # | Step | Expected | Pass |
|---|------|----------|------|
| 2.1 | With router ON, view dashboard | **Total Models**, **Local**, **Cloud** cards display numbers (possibly 0) | ☐ |
| 2.2 | Check **Usage** cards | **Last Hour** and **Last 24h** show calls count and cost | ☐ |
| 2.3 | Open Network tab (F12), find `/llm_router_dashboard` POST | Response has `byProvider`, `totalCount`, `localCount`, `cloudCount` (camelCase) | ☐ |
| 2.4 | Verify NO snake_case keys in response | No `by_provider`, `total_count`, `local_count` | ☐ |

---

## 3. Model Discovery

| # | Step | Expected | Pass |
|---|------|----------|------|
| 3.1 | Click **"Discover Models"** (or **"Auto Configure"**) | Loading spinner, then models populate in the providers table | ☐ |
| 3.2 | Verify Ollama models appear | At least one model under "ollama" provider | ☐ |
| 3.3 | (If cloud keys set) Verify cloud models appear | Models under "openai" or "anthropic" sections | ☐ |
| 3.4 | Check stat cards update | `totalCount`, `localCount`, `cloudCount` reflect discovered models | ☐ |

---

## 4. Default Model Assignment

| # | Step | Expected | Pass |
|---|------|----------|------|
| 4.1 | In dashboard defaults grid, select a model for **Chat** role | Dropdown shows discovered models, selection saves | ☐ |
| 4.2 | Reload and re-check | Chat default still shows the selected model | ☐ |
| 4.3 | Check Network: `/llm_router_set_default` POST | Response: `{success: true, role: "chat", ...}` | ☐ |

---

## 5. Model Selector (Chat Picker)

| # | Step | Expected | Pass |
|---|------|----------|------|
| 5.1 | Open chat, click **model picker** in top bar | Dropdown opens showing available models grouped by provider | ☐ |
| 5.2 | Type in search box | Models filter by name/provider | ☐ |
| 5.3 | Select a different model | "Model switched" toast appears | ☐ |
| 5.4 | Check Network: `/model_selector_quick_switch` POST | Response: `{success: true, model: {provider, name}}` | ☐ |

---

## 6. Model Badge on Messages

| # | Step | Expected | Pass |
|---|------|----------|------|
| 6.1 | With router **ON**, send a message (e.g., "Hello") | Agent responds | ☐ |
| 6.2 | Check agent response heading | Small **model badge** shows `provider/model_name` (e.g., `ollama/qwen2.5-coder:3b`) | ☐ |
| 6.3 | Badge styling | Small, semi-transparent background, rounded corners, inside heading | ☐ |
| 6.4 | Toggle router **OFF**, send another message | Badge still appears but shows configured `chat_model` provider/name | ☐ |
| 6.5 | Check KVP table (click to expand message details) | `_model` key should NOT appear in the key-value pairs table | ☐ |

---

## 7. Failover (requires cloud API)

| # | Step | Expected | Pass |
|---|------|----------|------|
| 7.1 | Set chat default to a non-existent model (e.g., `openai/gpt-nonexistent`) | Default saved | ☐ |
| 7.2 | Send a message | Agent still responds (via fallback to a working model) | ☐ |
| 7.3 | Check model badge | Badge shows the **fallback** model, not `gpt-nonexistent` | ☐ |
| 7.4 | Reset chat default to a valid model | System returns to normal | ☐ |

---

## 8. API Smoke Test Script

| # | Step | Expected | Pass |
|---|------|----------|------|
| 8.1 | Run: `python scripts/smoke_test_llm_router.py --base-url http://localhost:50080` | Script connects, runs all 11 endpoints | ☐ |
| 8.2 | Check output | All read-only endpoints PASS | ☐ |
| 8.3 | State-changing endpoints | `discover`, `auto_configure` PASS; `set_default`, `quick_switch` may PASS or FAIL (depends on registered models) | ☐ |
| 8.4 | Run with `--skip-state-changing` | Only read-only endpoints tested, all PASS | ☐ |

---

## Results Summary

| Area | Status | Notes |
|------|--------|-------|
| Settings toggle | ☐ Pass / ☐ Fail | |
| Dashboard camelCase | ☐ Pass / ☐ Fail | |
| Model discovery | ☐ Pass / ☐ Fail | |
| Default assignment | ☐ Pass / ☐ Fail | |
| Model selector | ☐ Pass / ☐ Fail | |
| Model badge | ☐ Pass / ☐ Fail | |
| Failover | ☐ Pass / ☐ Fail | |
| Smoke test script | ☐ Pass / ☐ Fail | |

**Tested by:** _______________
**Date:** _______________
**Branch:** `feature/pro-tier-hardening`

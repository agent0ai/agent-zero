# Token Usage & Cost Tracking - Design Document

## Overview

This document outlines the design for implementing comprehensive token usage tracking and cost prediction with real-time UI visualization in Agent Zero, while maintaining compatibility with the API-agnostic LiteLLM architecture.

---

## ⚠️ CRITICAL FIXES IDENTIFIED (Design Review)

The following issues were identified during design review and MUST be addressed:

### Fix 1: Enable Usage in Streaming Mode
**Issue**: LiteLLM does NOT return usage data in streaming mode by default!
**Solution**: Add `stream_options={"include_usage": True}` to streaming calls.

```python
# In models.py acompletion call:
_completion = await acompletion(
    model=self.model_name,
    messages=msgs_conv,
    stream=stream,
    stream_options={"include_usage": True} if stream else None,  # ADD THIS
    **call_kwargs,
)
```

### Fix 2: Capture Final Usage Chunk in Streaming
**Issue**: In streaming mode, usage comes in a SEPARATE final chunk with empty choices.
**Solution**: Detect and capture this special chunk.

```python
# In streaming loop:
final_usage = None
async for chunk in _completion:
    # Check if this is the usage-only final chunk
    if hasattr(chunk, 'usage') and chunk.usage:
        if not chunk.choices or len(chunk.choices) == 0:
            # This is the usage-only chunk
            final_usage = chunk.usage
            continue
    # ... rest of streaming logic
```

### Fix 3: Use Callback Pattern for Context Access
**Issue**: `LiteLLMChatWrapper` doesn't have access to `context_id`.
**Solution**: Add `usage_callback` parameter (follows existing callback pattern).

```python
# In unified_call signature:
usage_callback: Callable[[dict], Awaitable[None]] | None = None,

# At end of unified_call:
if usage_callback and final_usage:
    await usage_callback({
        "prompt_tokens": final_usage.prompt_tokens,
        "completion_tokens": final_usage.completion_tokens,
        "total_tokens": final_usage.total_tokens,
        "model": self.model_name,
    })
```

### Fix 4: Handle Missing Usage Gracefully
**Issue**: Some providers/scenarios may not return usage data.
**Solution**: Fallback to tiktoken approximation.

```python
if not final_usage:
    final_usage = {
        "prompt_tokens": approximate_tokens(str(msgs_conv)),
        "completion_tokens": approximate_tokens(result.response),
        "total_tokens": 0,  # Will be calculated
        "estimated": True  # Flag for UI to show "~" prefix
    }
    final_usage["total_tokens"] = final_usage["prompt_tokens"] + final_usage["completion_tokens"]
```

### Fix 5: Handle Zero-Cost (Local) Models
**Issue**: Ollama/LM Studio models have $0 cost.
**Solution**: Display "Free" in UI instead of "$0.0000".

```javascript
formatCost(cost) {
    if (cost === 0) return "Free";
    if (cost < 0.01) return `$${(cost * 1000).toFixed(4)}m`;
    return `$${cost.toFixed(4)}`;
}
```

### Deferred Items (Out of Scope for MVP)
- Browser model tracking (goes through browser-use library, complex integration)
- Embedding model tracking (different API format)
- Persistent storage (SQLite/JSON file)
- Historical usage charts

---

## Current State Analysis

### ✅ What We Have

1. **LiteLLM Integration**: All model calls go through LiteLLM's `completion()` and `acompletion()`
2. **Token Approximation**: `python/helpers/tokens.py` provides `approximate_tokens()` using tiktoken
3. **Rate Limiting**: Token-based rate limiting already tracks approximate input/output tokens
4. **Polling System**: `/poll` endpoint provides real-time updates to UI every 300ms
5. **Log System**: Structured logging with `context.log` that streams to UI
6. **Model Configuration**: `ModelConfig` dataclass with provider, name, and kwargs

### 🔴 What's Missing

1. **Actual Token Counts**: Not capturing real token usage from LiteLLM responses
2. **Cost Calculation**: No cost tracking or prediction
3. **Persistent Storage**: No database for historical token/cost data
4. **UI Components**: No visualization of token usage or costs
5. **Context-Level Tracking**: No aggregation of tokens per conversation

## Architecture Design

### 1. Token/Cost Data Flow

```
┌─────────────────┐
│  LiteLLM Call   │
│  (models.py)    │
└────────┬────────┘
         │
         ├─ Extract usage from response
         │  (response.usage.prompt_tokens)
         │  (response.usage.completion_tokens)
         │
         ▼
┌─────────────────┐
│ TokenTracker    │
│ (new helper)    │
├─────────────────┤
│ - Track tokens  │
│ - Calculate $   │
│ - Store data    │
└────────┬────────┘
         │
         ├─ Update context stats
         │
         ▼
┌─────────────────┐
│ AgentContext    │
│ (agent.py)      │
├─────────────────┤
│ + token_stats   │
│ + cost_stats    │
└────────┬────────┘
         │
         ├─ Stream via /poll
         │
         ▼
┌─────────────────┐
│  UI Component   │
│  (webui/)       │
├─────────────────┤
│ - Token gauge   │
│ - Cost display  │
│ - Charts        │
└─────────────────┘
```

### 2. Data Structures

#### TokenUsageRecord
```python
@dataclass
class TokenUsageRecord:
    """Single model call token usage"""
    timestamp: datetime
    context_id: str
    model_provider: str
    model_name: str
    
    # Token counts (from LiteLLM response.usage)
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    # Cached tokens (if supported by provider)
    cached_prompt_tokens: int = 0
    
    # Cost calculation
    prompt_cost_usd: float = 0.0
    completion_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    
    # Metadata
    call_type: str = "chat"  # chat, utility, embedding, browser
    tool_name: Optional[str] = None
    success: bool = True
```

#### ContextTokenStats
```python
@dataclass
class ContextTokenStats:
    """Aggregated stats for a conversation context"""
    context_id: str
    
    # Totals
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    
    # By model type
    chat_tokens: int = 0
    chat_cost_usd: float = 0.0
    utility_tokens: int = 0
    utility_cost_usd: float = 0.0
    
    # Tracking
    call_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    records: List[TokenUsageRecord] = field(default_factory=list)
```

### 3. Implementation Components

#### A. Backend: TokenTracker Helper

**File**: `python/helpers/token_tracker.py`

```python
class TokenTracker:
    """
    Centralized token usage and cost tracking.
    Works with LiteLLM's response.usage object.
    """
    
    # In-memory storage (per context)
    _context_stats: Dict[str, ContextTokenStats] = {}
    
    @classmethod
    def track_completion(
        cls,
        context_id: str,
        model_config: ModelConfig,
        response: ModelResponse,  # LiteLLM response
        call_type: str = "chat",
        tool_name: Optional[str] = None
    ) -> TokenUsageRecord:
        """
        Track a single completion call.
        Extracts usage from LiteLLM response and calculates cost.
        """
        # Extract token usage from response
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
        
        # Handle cached tokens if available
        cached_tokens = getattr(usage, 'prompt_tokens_details', {}).get('cached_tokens', 0)
        
        # Calculate cost using LiteLLM's cost_per_token
        prompt_cost, completion_cost = cost_per_token(
            model=f"{model_config.provider}/{model_config.name}",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        # Create record
        record = TokenUsageRecord(
            timestamp=datetime.now(timezone.utc),
            context_id=context_id,
            model_provider=model_config.provider,
            model_name=model_config.name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cached_prompt_tokens=cached_tokens,
            prompt_cost_usd=prompt_cost,
            completion_cost_usd=completion_cost,
            total_cost_usd=prompt_cost + completion_cost,
            call_type=call_type,
            tool_name=tool_name,
            success=True
        )
        
        # Update context stats
        cls._update_context_stats(context_id, record)
        
        return record
    
    @classmethod
    def get_context_stats(cls, context_id: str) -> ContextTokenStats:
        """Get aggregated stats for a context"""
        return cls._context_stats.get(context_id, ContextTokenStats(context_id=context_id))
    
    @classmethod
    def estimate_cost(
        cls,
        model_config: ModelConfig,
        prompt_text: str,
        estimated_completion_tokens: int = 500
    ) -> dict:
        """
        Estimate cost for a prompt before making the call.
        Useful for budget warnings.
        """
        # Count prompt tokens
        prompt_tokens = approximate_tokens(prompt_text)
        
        # Estimate cost
        prompt_cost, completion_cost = cost_per_token(
            model=f"{model_config.provider}/{model_config.name}",
            prompt_tokens=prompt_tokens,
            completion_tokens=estimated_completion_tokens
        )
        
        return {
            "estimated_prompt_tokens": prompt_tokens,
            "estimated_completion_tokens": estimated_completion_tokens,
            "estimated_total_tokens": prompt_tokens + estimated_completion_tokens,
            "estimated_prompt_cost_usd": prompt_cost,
            "estimated_completion_cost_usd": completion_cost,
            "estimated_total_cost_usd": prompt_cost + completion_cost
        }
```

#### B. Integration: Modify models.py

**File**: `models.py` (unified_call method)

```python
async def unified_call(
    self,
    messages: List[BaseMessage] | None = None,
    system_message: str | None = None,
    user_message: str | None = None,
    response_callback: Callable[[str, str], Awaitable[None]] | None = None,
    reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
    tokens_callback: Callable[[str, int], Awaitable[None]] | None = None,
    rate_limiter_callback: Callable | None = None,
    usage_callback: Callable[[dict], Awaitable[None]] | None = None,  # NEW
    **kwargs: Any,
) -> Tuple[str, str]:

    # ... existing setup code ...

    stream = reasoning_callback is not None or response_callback is not None or tokens_callback is not None

    # Track usage for callback
    final_usage = None

    # call model - ADD stream_options for usage tracking
    _completion = await acompletion(
        model=self.model_name,
        messages=msgs_conv,
        stream=stream,
        stream_options={"include_usage": True} if stream else None,  # NEW
        **call_kwargs,
    )

    if stream:
        async for chunk in _completion:
            # Check if this is the usage-only final chunk (NEW)
            if hasattr(chunk, 'usage') and chunk.usage:
                choices = getattr(chunk, 'choices', [])
                if not choices or len(choices) == 0:
                    final_usage = chunk.usage
                    continue  # Don't process as content

            # ... existing streaming chunk processing ...
            got_any_chunk = True
            parsed = _parse_chunk(chunk)
            output = result.add_chunk(parsed)
            # ... callbacks ...
    else:
        # Non-streaming: response has usage directly
        parsed = _parse_chunk(_completion)
        output = result.add_chunk(parsed)
        if hasattr(_completion, 'usage'):
            final_usage = _completion.usage

    # Call usage callback if provided (NEW)
    if usage_callback:
        if final_usage:
            await usage_callback({
                "prompt_tokens": getattr(final_usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(final_usage, 'completion_tokens', 0),
                "total_tokens": getattr(final_usage, 'total_tokens', 0),
                "model": self.model_name,
                "estimated": False
            })
        else:
            # Fallback to approximation
            await usage_callback({
                "prompt_tokens": approximate_tokens(str(msgs_conv)),
                "completion_tokens": approximate_tokens(result.response),
                "total_tokens": approximate_tokens(str(msgs_conv)) + approximate_tokens(result.response),
                "model": self.model_name,
                "estimated": True  # Flag for UI to show approximation indicator
            })

    return result.response, result.reasoning
```

#### C. Context Integration: agent.py

**File**: `agent.py` (AgentContext class)

```python
class AgentContext:
    # ... existing fields ...
    
    def get_token_stats(self) -> dict:
        """Get token/cost stats for this context"""
        from python.helpers.token_tracker import TokenTracker
        stats = TokenTracker.get_context_stats(self.id)
        
        return {
            "total_tokens": stats.total_tokens,
            "total_cost_usd": stats.total_cost_usd,
            "prompt_tokens": stats.total_prompt_tokens,
            "completion_tokens": stats.total_completion_tokens,
            "call_count": stats.call_count,
            "chat_cost_usd": stats.chat_cost_usd,
            "utility_cost_usd": stats.utility_cost_usd,
            "last_updated": stats.last_updated.isoformat()
        }
```

#### D. API Endpoint: python/api/token_stats.py

```python
class TokenStats(ApiHandler):
    """
    Get token usage and cost statistics.
    
    Actions:
    - get_context: Get stats for specific context
    - get_all: Get stats for all contexts
    - estimate: Estimate cost for a prompt
    """
    
    async def process(self, input: dict, request: Request) -> dict:
        action = input.get("action", "get_context")
        
        if action == "get_context":
            context_id = input.get("context_id")
            if not context_id:
                return {"error": "context_id required"}
            
            context = AgentContext.get(context_id)
            if not context:
                return {"error": "Context not found"}
            
            return {
                "success": True,
                "stats": context.get_token_stats()
            }
        
        elif action == "estimate":
            # Estimate cost for a prompt
            model_provider = input.get("model_provider")
            model_name = input.get("model_name")
            prompt = input.get("prompt", "")
            
            # ... implementation ...
            
        return {"error": "Unknown action"}
```

#### E. Poll Integration: python/api/poll.py

**File**: `python/api/poll.py` (modify response)

```python
# In the poll response, add token stats
return {
    # ... existing fields ...
    "token_stats": context.get_token_stats() if context else None,
}
```

### 4. UI Components

#### A. Token Stats Store

**File**: `webui/components/chat/token-stats/token-stats-store.js`

```javascript
import { createStore } from "/js/AlpineStore.js";

const model = {
  // State
  totalTokens: 0,
  totalCostUsd: 0,
  promptTokens: 0,
  completionTokens: 0,
  callCount: 0,
  chatCostUsd: 0,
  utilityCostUsd: 0,
  lastUpdated: null,
  
  // Update from poll
  updateFromPoll(tokenStats) {
    if (!tokenStats) return;
    
    this.totalTokens = tokenStats.total_tokens || 0;
    this.totalCostUsd = tokenStats.total_cost_usd || 0;
    this.promptTokens = tokenStats.prompt_tokens || 0;
    this.completionTokens = tokenStats.completion_tokens || 0;
    this.callCount = tokenStats.call_count || 0;
    this.chatCostUsd = tokenStats.chat_cost_usd || 0;
    this.utilityCostUsd = tokenStats.utility_cost_usd || 0;
    this.lastUpdated = tokenStats.last_updated;
  },
  
  // Format cost for display
  formatCost(cost) {
    if (cost < 0.01) {
      return `$${(cost * 1000).toFixed(4)}m`; // Show in millicents
    }
    return `$${cost.toFixed(4)}`;
  },
  
  // Format tokens with K/M suffix
  formatTokens(tokens) {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(2)}M`;
    } else if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  }
};

const store = createStore("tokenStatsStore", model);
export { store };
```

#### B. Token Stats Component

**File**: `webui/components/chat/token-stats/token-stats.html`

```html
<div x-data class="token-stats-widget">
  <div class="token-stats-header">
    <span class="token-stats-icon">📊</span>
    <span class="token-stats-title">Usage</span>
  </div>
  
  <div class="token-stats-content">
    <!-- Total Cost -->
    <div class="stat-item stat-cost">
      <span class="stat-label">Cost:</span>
      <span class="stat-value" x-text="$store.tokenStatsStore.formatCost($store.tokenStatsStore.totalCostUsd)"></span>
    </div>
    
    <!-- Total Tokens -->
    <div class="stat-item">
      <span class="stat-label">Tokens:</span>
      <span class="stat-value" x-text="$store.tokenStatsStore.formatTokens($store.tokenStatsStore.totalTokens)"></span>
    </div>
    
    <!-- Token Breakdown (expandable) -->
    <div class="stat-breakdown" x-show="$store.tokenStatsStore.totalTokens > 0">
      <div class="stat-bar">
        <div class="stat-bar-fill stat-bar-prompt" 
             :style="`width: ${($store.tokenStatsStore.promptTokens / $store.tokenStatsStore.totalTokens * 100)}%`">
        </div>
        <div class="stat-bar-fill stat-bar-completion" 
             :style="`width: ${($store.tokenStatsStore.completionTokens / $store.tokenStatsStore.totalTokens * 100)}%`">
        </div>
      </div>
      <div class="stat-legend">
        <span class="legend-item">
          <span class="legend-color legend-prompt"></span>
          Input: <span x-text="$store.tokenStatsStore.formatTokens($store.tokenStatsStore.promptTokens)"></span>
        </span>
        <span class="legend-item">
          <span class="legend-color legend-completion"></span>
          Output: <span x-text="$store.tokenStatsStore.formatTokens($store.tokenStatsStore.completionTokens)"></span>
        </span>
      </div>
    </div>
    
    <!-- Call Count -->
    <div class="stat-item stat-meta">
      <span class="stat-label">Calls:</span>
      <span class="stat-value" x-text="$store.tokenStatsStore.callCount"></span>
    </div>
  </div>
</div>
```

#### C. Styling

**File**: `webui/css/token-stats.css`

```css
.token-stats-widget {
  background: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  font-size: 0.9em;
}

.token-stats-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.token-stats-icon {
  font-size: 1.2em;
}

.token-stats-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: var(--color-text-secondary);
}

.stat-value {
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-cost .stat-value {
  color: var(--color-accent);
  font-size: 1.1em;
}

.stat-bar {
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
  display: flex;
  margin: 4px 0;
}

.stat-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.stat-bar-prompt {
  background: linear-gradient(90deg, #4CAF50, #66BB6A);
}

.stat-bar-completion {
  background: linear-gradient(90deg, #2196F3, #42A5F5);
}

.stat-legend {
  display: flex;
  gap: 12px;
  font-size: 0.85em;
  color: var(--color-text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-prompt {
  background: #4CAF50;
}

.legend-completion {
  background: #2196F3;
}

.stat-meta {
  font-size: 0.85em;
  color: var(--color-text-tertiary);
}
```

#### D. Integration in index.js

**File**: `webui/index.js` (modify poll function)

```javascript
// Import token stats store
import { store as tokenStatsStore } from "/components/chat/token-stats/token-stats-store.js";

// In poll() function, update token stats
export async function poll() {
  // ... existing code ...
  
  // Update token stats if available
  if (response.token_stats) {
    tokenStatsStore.updateFromPoll(response.token_stats);
  }
  
  // ... rest of existing code ...
}
```

#### E. Add to Chat Top Section

**File**: `webui/components/chat/top-section/chat-top.html`

```html
<!-- Existing content -->
<div id="chat-top-section">
  <!-- ... existing elements ... -->
  
  <!-- Token Stats Widget -->
  <x-component path="chat/token-stats/token-stats.html"></x-component>
</div>
```

## Implementation Plan

### Phase 0: Design & Review ✅ COMPLETE
- [x] Research LiteLLM response format and usage data availability
- [x] Investigate existing codebase (models.py, agent.py, poll endpoint)
- [x] Design token tracking architecture
- [x] Create design document
- [x] **Design Review**: Identified 5 critical fixes (streaming, callbacks, fallbacks)
- [x] Update design document with fixes

### Phase 1: Backend Foundation 🔄 CURRENT
- [ ] Modify `models.py` to add `stream_options={"include_usage": True}`
- [ ] Add `usage_callback` parameter to `unified_call`
- [ ] Create `python/helpers/token_tracker.py`
- [ ] Add `TokenUsageRecord` and `ContextTokenStats` dataclasses
- [ ] Implement `TokenTracker.track_completion()` with cost calculation
- [ ] Integrate callback with `Agent.call_chat_model()` and `Agent.call_utility_model()`
- [ ] Test with multiple providers (OpenAI, Anthropic, Ollama)

### Phase 2: Context & API Integration
- [ ] Add `get_token_stats()` to `AgentContext`
- [ ] Modify `/poll` endpoint to include token stats
- [ ] Create `/token_stats` API endpoint (optional, for detailed view)
- [ ] Test real-time updates

### Phase 3: UI Components
- [ ] Create token stats Alpine.js store
- [ ] Build token stats widget component
- [ ] Add CSS styling (match existing dark theme)
- [ ] Handle "Free" display for local models
- [ ] Handle "~" prefix for estimated tokens
- [ ] Integrate with poll updates
- [ ] Test responsiveness and real-time updates

### Phase 4: Advanced Features (Future)
- [ ] Add cost estimation before calls
- [ ] Implement budget warnings
- [ ] Add historical charts
- [ ] Export token usage data
- [ ] Persistent storage (SQLite/JSON)

## Handling API-Agnostic Complexity

### Challenge: Different Providers, Different Response Formats

**Solution**: LiteLLM normalizes all responses to a standard format:

```python
# All providers return this structure
response.usage = {
    "prompt_tokens": int,
    "completion_tokens": int,
    "total_tokens": int,
    "prompt_tokens_details": {  # Optional, provider-specific
        "cached_tokens": int
    }
}
```

### Challenge: Streaming vs Non-Streaming

**Solution**: 
- **Streaming**: Usage data comes in the LAST chunk
- **Non-Streaming**: Usage data in the response object
- Our implementation handles both cases

### Challenge: Cost Calculation Across Providers

**Solution**: Use LiteLLM's built-in `cost_per_token()` function:
- Maintains up-to-date pricing from api.litellm.ai
- Handles all 100+ providers automatically
- Falls back gracefully for unknown models

### Challenge: Models Without Usage Data

**Solution**: Fallback to approximation:
```python
if not hasattr(response, 'usage') or not response.usage:
    # Fallback to tiktoken approximation
    prompt_tokens = approximate_tokens(prompt_text)
    completion_tokens = approximate_tokens(completion_text)
```

## Testing Strategy

### Unit Tests
```python
# test_token_tracker.py
def test_track_completion():
    # Mock LiteLLM response
    mock_response = MockResponse(
        usage=Usage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
    )
    
    record = TokenTracker.track_completion(
        context_id="test",
        model_config=ModelConfig(...),
        response=mock_response
    )
    
    assert record.total_tokens == 150
    assert record.total_cost_usd > 0
```

### Integration Tests
- Test with real OpenAI calls
- Test with real Anthropic calls
- Test streaming vs non-streaming
- Test cost calculation accuracy

### UI Tests
- Verify real-time updates
- Test formatting functions
- Test responsive design
- Test with large token counts

## Future Enhancements

1. **Persistent Storage**: Save token usage to SQLite/PostgreSQL
2. **Historical Charts**: Visualize usage over time
3. **Budget Alerts**: Warn when approaching limits
4. **Cost Optimization**: Suggest cheaper models for simple tasks
5. **Export Reports**: CSV/JSON export of usage data
6. **Multi-User Tracking**: Per-user cost tracking
7. **Caching Metrics**: Track cache hit rates and savings

## Security Considerations

1. **Cost Data Privacy**: Token stats are per-context, not shared
2. **API Key Protection**: Never log API keys in token records
3. **Rate Limiting**: Existing rate limiter prevents abuse
4. **Data Retention**: Consider TTL for old token records

## Performance Considerations

1. **In-Memory Storage**: Fast access, but limited by RAM
2. **Polling Overhead**: Token stats add ~100 bytes to poll response
3. **Calculation Cost**: LiteLLM's cost_per_token is cached
4. **UI Rendering**: Minimal impact, updates only on change

## Conclusion

This design provides:
- ✅ **Real token counts** from LiteLLM responses
- ✅ **Accurate cost calculation** using LiteLLM's pricing data
- ✅ **Real-time UI updates** via existing poll mechanism
- ✅ **API-agnostic** works with all 100+ LiteLLM providers
- ✅ **Minimal overhead** leverages existing infrastructure
- ✅ **Extensible** foundation for advanced features

The implementation is straightforward because we leverage:
1. LiteLLM's standardized response format
2. Existing poll/log streaming infrastructure
3. Alpine.js reactive stores for UI
4. Existing token approximation utilities

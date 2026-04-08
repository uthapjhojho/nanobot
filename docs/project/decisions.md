# Architectural Decisions

## ADR-001: Dashscope Provider Strategy

**Status:** Adopted (v0.1.5)

### Context

nanobot historically used litellm as a universal provider abstraction to support multiple LLM providers including Dashscope (Alibaba's Qwen models). However, the upstream codebase (v0.1.5) removes the litellm dependency in favor of native provider implementations.

Dashscope is a key provider for the Chinese market and requires continued support.

### Decision

Support Dashscope using the native OpenAI-compatible provider abstraction instead of litellm.

Dashscope exposes an OpenAI-compatible API endpoint at:
```
https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

This endpoint accepts the same request/response format as OpenAI's API, allowing us to treat Dashscope as a standard OpenAI-compatible provider in the registry.

### Rationale

1. **Upstream Alignment:** The v0.1.5 merge removes litellm and replaces it with native provider implementations. Keeping litellm would require maintaining a dependency that upstream has abandoned.

2. **Simplicity:** Dashscope's OpenAI-compatible endpoint means no special handling is needed. It integrates naturally into the provider registry.

3. **Reduced Dependencies:** Removing litellm reduces the overall dependency tree and surface area for maintenance.

4. **Performance:** Native providers eliminate the litellm abstraction layer, providing lower latency and more direct control over provider-specific behavior.

5. **Consistency:** All providers now follow the same pattern: look up a `ProviderSpec` in the registry, then use the appropriate SDK or OpenAI-compatible client.

### Implementation

#### ProviderSpec for Dashscope

```python
ProviderSpec(
    name="dashscope",
    keywords=("qwen", "dashscope"),
    env_key="DASHSCOPE_API_KEY",
    display_name="DashScope",
    backend="openai_compat",
    default_api_base="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    litellm_prefix="dashscope",
    skip_prefixes=("dashscope/",),
)
```

#### Configuration Example

Users can configure Dashscope in their nanobot config:

```json
{
  "providers": {
    "dashscope": {
      "apiKey": "sk-...",
      "apiBase": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    }
  }
}
```

Or via environment variable:
```bash
export DASHSCOPE_API_KEY=sk-...
```

#### Model Usage

Users can specify Qwen models by name:
```python
agent = Nanobot.from_config()
await agent.chat(model="qwen-turbo", ...)
```

The provider registry automatically matches "qwen" keyword and routes to Dashscope.

### Trade-offs

**Advantages:**
- No external dependency needed
- Simpler codebase
- Aligned with upstream
- Natural integration with OpenAI-compatible abstraction

**Disadvantages:**
- None of Dashscope's newer features (if any emerge) are automatically available
- Would require manual provider spec updates if Dashscope's API changes

This trade-off is acceptable given that Dashscope maintains API compatibility with OpenAI.

### Verification

The decision is verified by:
- Registry lookup tests confirming Dashscope detection
- Integration tests with actual Qwen models
- Functional parity with litellm-based implementation

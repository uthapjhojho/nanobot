# nanobot Architecture

## Provider System

The provider system is the heart of nanobot's multi-provider support. It decouples provider detection, configuration, and implementation into clean, testable layers.

### Overview

```
┌─────────────────────────────────────────────┐
│          Agent / Application Layer          │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  Provider Resolution │  (registry lookup)
        └──────────────────────┘
                   │
                   ↓
        ┌──────────────────────────────────────┐
        │      LLMProvider ABC                 │
        │  (chat, completion, tool calling)    │
        └──────────────────────────────────────┘
                   │
        ┌──────────┬──────────┬──────────┬──────────┐
        │          │          │          │          │
        ↓          ↓          ↓          ↓          ↓
    Anthropic  OpenAI    OpenAI     Azure        GitHub
    Provider   Provider  Compat     OpenAI       Copilot
                         Provider   Provider     Provider
```

### Layer 1: Provider Registry

The **registry** (`providers/registry.py`) contains metadata about all available providers:

```python
@dataclass(frozen=True)
class ProviderSpec:
    # Identity
    name: str                    # Config field name, e.g., "dashscope"
    keywords: tuple[str, ...]   # Model-name keywords for matching
    env_key: str                # Env var for API key
    display_name: str           # Shown in CLI
    
    # Implementation
    backend: str                # "openai_compat", "anthropic", etc.
    
    # Detection
    is_gateway: bool            # Routes any model (OpenRouter, AiHubMix)
    is_local: bool              # Local deployment (vLLM, Ollama)
    detect_by_key_prefix: str   # Match api_key prefix
    detect_by_base_keyword: str # Match api_base URL keyword
    
    # LiteLLM routing
    litellm_prefix: str         # Prefix for model routing
    skip_prefixes: tuple[str, ...]  # Don't auto-add these prefixes
```

#### Registry Functions

**`find_by_name(name: str) -> ProviderSpec | None`**

Find a provider by its config field name (e.g., "dashscope").

```python
spec = find_by_name("dashscope")
```

**`find_by_model(model: str) -> ProviderSpec | None`**

Find a provider by matching model-name keywords.

```python
spec = find_by_model("gpt-4-turbo")         # Matches "openai"
spec = find_by_model("claude-opus-4-5")     # Matches "anthropic"
spec = find_by_model("qwen-turbo")          # Matches "dashscope"
```

**`find_gateway(provider_name, api_key, api_base) -> ProviderSpec | None`**

Detect a gateway provider by config name, api_key prefix, or api_base keyword.

```python
spec = find_gateway(api_key="sk-or-abc123")  # Matches "openrouter" by prefix
spec = find_gateway(api_base="https://aihubmix.com")  # Matches by URL
```

### Layer 2: LLMProvider Abstract Base Class

The **LLMProvider** (`providers/base.py`) defines the interface all providers must implement:

```python
class LLMProvider(ABC):
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send a chat completion request."""
        ...
```

Key features:
- Async-first design
- Unified tool calling format
- Provider-agnostic request/response

### Layer 3: Concrete Provider Implementations

nanobot includes 5 concrete provider implementations:

#### 1. **Anthropic Provider** (`providers/anthropic_provider.py`)

- Uses Anthropic's native SDK
- Direct support for Anthropic models (Claude)
- Prompt caching support

```python
provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = await provider.chat(
    messages=[...],
    model="claude-opus-4-5",
)
```

#### 2. **OpenAI Provider** (`providers/openai_provider.py`)

- Uses OpenAI's native SDK
- Direct support for OpenAI models (GPT-4, etc.)
- `max_completion_tokens` support

```python
provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
response = await provider.chat(
    messages=[...],
    model="gpt-4-turbo",
)
```

#### 3. **OpenAI-Compatible Provider** (`providers/openai_compat_provider.py`)

- Routes any OpenAI-compatible endpoint
- Supports Dashscope, DeepSeek, Mistral, and others
- Customizable `api_base` for self-hosted solutions

```python
provider = OpenAICompatProvider(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    api_base="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
response = await provider.chat(
    messages=[...],
    model="qwen-turbo",
)
```

#### 4. **Azure OpenAI Provider** (`providers/azure_openai_provider.py`)

- Direct Azure OpenAI deployment support
- Azure-specific auth and request formatting

```python
provider = AzureOpenAIProvider(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_base="https://xxx.openai.azure.com",
)
```

#### 5. **GitHub Copilot Provider** (`providers/github_copilot_provider.py`)

- OAuth-based authentication
- Direct GitHub Copilot API support

```python
provider = GitHubCopilotProvider()
response = await provider.chat(messages=[...])
```

### Layer 4: Provider Configuration

Providers are configured via `ProvidersConfig` in `config/schema.py`:

```python
class ProvidersConfig(BaseConfig):
    anthropic: AnthropicConfig | None = None
    openai: OpenAIConfig | None = None
    dashscope: DashscopeConfig | None = None
    # ... etc
```

Each provider config includes:
- `api_key` (or path to API key file)
- `api_base` (for OpenAI-compatible providers)
- Provider-specific settings

### Resolution Flow

When the agent needs to use a provider:

1. **Load config** → Get provider spec from command line or config file
2. **Look up registry** → Use `find_by_name()`, `find_by_model()`, or `find_gateway()`
3. **Instantiate provider** → Create concrete provider instance
4. **Execute request** → Call `provider.chat()`

Example:

```python
# From config
provider_name = "dashscope"
spec = find_by_name(provider_name)  # Get ProviderSpec

# From model string
spec = find_by_model("qwen-turbo")  # Also finds dashscope

# Create provider based on spec
if spec.backend == "openai_compat":
    provider = OpenAICompatProvider(
        api_key=config.get(provider_name).api_key,
        api_base=config.get(provider_name).api_base,
    )
elif spec.backend == "anthropic":
    provider = AnthropicProvider(
        api_key=config.get(provider_name).api_key,
    )
# ... etc
```

### Adding a New Provider

To add support for a new provider:

1. **Create ProviderSpec** in `providers/registry.py`:
   ```python
   ProviderSpec(
       name="myai",
       keywords=("myai",),
       env_key="MYAI_API_KEY",
       display_name="MyAI",
       backend="openai_compat",
       default_api_base="https://api.myai.com/v1",
   )
   ```

2. **Add config class** in `config/schema.py`:
   ```python
   class MyAIConfig(ProviderConfig):
       api_key: str = Field(...)
   ```

3. **Implement provider** (if not using `openai_compat`):
   ```python
   class MyAIProvider(LLMProvider):
       async def chat(self, ...): ...
   ```

4. **Update provider factory** in `providers/__init__.py` to instantiate your provider

5. **Add tests** for provider detection and execution

## Design Principles

### Separation of Concerns

- **Registry:** Metadata and detection only (no provider logic)
- **Providers:** Implementation only (no detection logic)
- **Config:** User-provided settings (no provider selection logic)

### Extensibility

- New providers can be added without modifying existing code
- Registry-based lookup prevents hard-coded provider chains
- OpenAI-compat pattern allows supporting new endpoints with zero code

### Testability

- Providers are easily mockable
- Registry lookup can be tested in isolation
- No circular dependencies between layers

### User-Friendliness

- Model names are matched by keyword (no need to know provider internals)
- Environment variables follow a consistent `{PROVIDER}_API_KEY` pattern
- Gateway detection is automatic (no manual configuration needed for OpenRouter, etc.)

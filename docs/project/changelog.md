# nanobot Changelog

## v0.1.5 (Upstream Merge)

### Major Changes

#### Provider Architecture
- **Removed:** litellm dependency
- **Added:** Native support for Anthropic, OpenAI, and OpenAI-compatible endpoints
- **New Registry:** Provider resolution via `ProviderSpec` registry with keyword-based matching
- **Custom Providers:** Support for custom OpenAI-compatible endpoints via `api_base` override
- **Dashscope Support:** Qwen models now supported via OpenAI-compatible provider at `dashscope-intl.aliyuncs.com/compatible-mode/v1`

#### Agent Core
- **Rewrite:** runner.py, hook.py, and loop.py merged into unified agent execution model
- **Improved:** Hook system with clearer execution phases
- **Enhanced:** Request/response cycle with better error handling

#### Memory System
- **Added:** `Dream` class for asynchronous memory consolidation
- **Added:** `Consolidator` class for multi-stage memory processing
- **Improved:** Two-layer memory system (instant consolidation + scheduled dreaming)
- **Enhanced:** Better separation between session history and long-term memory

#### Channels
- **New:** WeChat Official Account (weixin) channel
- **New:** WeCom (Enterprise WeChat) channel
- **Enhanced:** All 9 channels follow unified BaseChannel abstraction

#### CLI
- **New:** StreamRenderer (stream.py) for flicker-free streaming output
- **New:** Interactive onboarding wizard (onboard.py)
- **New:** Token counting and context limit utilities (models.py)
- **Improved:** Windows UTF-8 encoding support
- **Enhanced:** Provider auto-detection in CLI

#### Infrastructure
- **Updated:** Dockerfile with Node.js 20, optimized layer caching
- **Updated:** docker-compose.yml with three services (gateway, api, cli) and resource limits
- **Improved:** Security posture with non-root user (nanobot:1000)

### Test Coverage
- **93%** test suite passing
- All core modules syntax validated
- End-to-end integration tests passing

### Documentation
- CHANNEL_PLUGIN_GUIDE.md: Updated channel plugin development guide
- MEMORY.md: Comprehensive memory system documentation
- PYTHON_SDK.md: SDK usage examples

### Breaking Changes
- litellm is no longer a dependency
- Provider configuration now uses registry-based resolution
- `api_base` is now the standard way to configure custom OpenAI-compatible endpoints

### Migration Path
- Existing litellm configurations can be migrated to native provider configurations
- Custom OpenAI-compatible providers use the `custom` provider type with explicit `api_base`

"""Configuration migration utilities for upgrading from v0.1.3 to v0.1.5."""

import re
from typing import Any, Dict


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def migrate_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate configuration from v0.1.3 to v0.1.5 format.

    - Converts snake_case keys to camelCase
    - Adds default provider if missing
    - Adds default dream config if missing
    - Preserves channel configurations

    Args:
        config_dict: Configuration dictionary to migrate

    Returns:
        Migrated configuration dictionary
    """
    migrated = {}

    # Migrate top-level keys to camelCase
    for key, value in config_dict.items():
        camel_key = snake_to_camel(key)

        # Handle nested dictionaries (e.g., channel configs)
        if isinstance(value, dict) and key not in ('channels', 'channel'):
            migrated[camel_key] = migrate_config(value)
        else:
            migrated[camel_key] = value

    # Add default provider if missing
    if 'provider' not in migrated:
        migrated['provider'] = 'anthropic'

    # Add default dream config if missing
    if 'dream' not in migrated:
        migrated['dream'] = {
            'enabled': False,
            'model': 'claude-opus-4-5',
            'max_tokens': 16000,
        }

    # Ensure channels config exists
    if 'channels' not in migrated and 'channel' in migrated:
        migrated['channels'] = migrated.pop('channel')

    return migrated


def migrate_provider_key(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate provider configuration to new format.

    v0.1.3: provider='litellm', model='anthropic/claude-opus'
    v0.1.5: provider='anthropic', model='claude-opus-4-5'
    """
    if 'provider' not in config_dict:
        return config_dict

    provider = config_dict.get('provider', '')

    # Migration rules
    if provider == 'litellm':
        model = config_dict.get('model', '')

        # Detect actual provider from model string
        if 'anthropic' in model:
            config_dict['provider'] = 'anthropic'
            # Extract model name after /
            config_dict['model'] = model.split('/')[-1] if '/' in model else 'claude-opus-4-5'
        elif 'openai' in model:
            config_dict['provider'] = 'openai'
            config_dict['model'] = model.split('/')[-1] if '/' in model else 'gpt-4'
        elif 'dashscope' in model:
            config_dict['provider'] = 'dashscope'
            config_dict['model'] = model.split('/')[-1] if '/' in model else 'qwen-max'

    return config_dict

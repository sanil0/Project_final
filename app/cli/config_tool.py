"""Configuration validation and management CLI tool."""

import click
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import logging

from app.config import Settings
from app.services.configuration import ConfigurationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """DDoS Protection Service configuration management tool."""
    pass

@cli.command()
@click.option('--env-file', '-e', type=str, help='Path to .env file to validate')
def validate(env_file: Optional[str]):
    """Validate configuration settings."""
    try:
        # Load environment variables from file if provided
        if env_file:
            if not os.path.exists(env_file):
                logger.error(f"Environment file not found: {env_file}")
                sys.exit(1)
                
            # Load variables from file
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        
        # Attempt to create settings
        settings = Settings()
        
        # Validate all settings
        settings_dict = settings.model_dump()
        
        click.echo("Configuration validation successful!")
        click.echo("\nCurrent settings:")
        
        # Print settings by category
        categories = {
            "Core Settings": ["upstream_base_url", "admin_api_key", "target_url"],
            "Rate Limiting": ["base_rate_limit", "rate_window_seconds", "burst_multiplier"],
            "Blocking Rules": ["block_duration_minutes", "block_threshold_violations", 
                             "progressive_blocking", "max_block_duration_hours"],
            "ML Model": ["model_path", "model_update_interval_hours", "enable_model_cache",
                        "model_cache_ttl_seconds", "model_cache_max_size"],
            "IP Management": ["blocklist_ips", "whitelist_ips", "trusted_proxies",
                            "country_blocklist", "asn_blocklist"]
        }
        
        for category, settings_list in categories.items():
            click.echo(f"\n{category}:")
            for setting in settings_list:
                if setting in settings_dict:
                    click.echo(f"  {setting}: {settings_dict[setting]}")
        
    except Exception as e:
        click.echo(f"Configuration validation failed: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--output', '-o', type=str, help='Output file path')
@click.option('--format', '-f', type=click.Choice(['env', 'json']), default='env',
              help='Output format (env or json)')
def export(output: Optional[str], format: str):
    """Export current configuration."""
    try:
        config_manager = ConfigurationManager()
        config = config_manager.export_config()
        
        if format == 'json':
            content = json.dumps(config, indent=2)
        else:
            # Convert to env format
            content = '\n'.join(f"{k.upper()}={v}" for k, v in config.items())
        
        if output:
            Path(output).write_text(content)
            click.echo(f"Configuration exported to: {output}")
        else:
            click.echo(content)
            
    except Exception as e:
        click.echo(f"Export failed: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('setting_name')
@click.argument('setting_value')
@click.option('--env-file', '-e', type=str, default='.env',
              help='Path to .env file to update')
def set(setting_name: str, setting_value: str, env_file: str):
    """Set a configuration value."""
    try:
        env_path = Path(env_file)
        
        # Read existing content
        content = env_path.read_text() if env_path.exists() else ""
        lines = content.splitlines()
        
        # Convert setting name to uppercase
        setting_name = setting_name.upper()
        
        # Find and replace or append setting
        found = False
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                if line.split('=')[0].strip() == setting_name:
                    lines[i] = f"{setting_name}={setting_value}"
                    found = True
                    break
        
        if not found:
            lines.append(f"{setting_name}={setting_value}")
        
        # Write back to file
        env_path.write_text('\n'.join(lines) + '\n')
        click.echo(f"Updated {setting_name} in {env_file}")
        
        # Validate new configuration
        click.echo("Validating new configuration...")
        validate.callback(env_file=env_file)
        
    except Exception as e:
        click.echo(f"Failed to set configuration: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()
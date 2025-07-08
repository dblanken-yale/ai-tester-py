"""Configuration settings for AI Tester."""
import os
from typing import Dict, Any

# Default configuration values
DEFAULT_CONFIG = {
    'request_timeout': 30,
    'max_retries': 3,
    'retry_delay': 2,
    'exponential_backoff': True,
    'backoff_multiplier': 1.5,
    'default_endpoint': '/conversation',
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'error_log_file': '.error_log.jsonl',
    'success_log_file': '.success_log.jsonl',
    'success_log_meta_file': '.success_log.meta.json',
    'run_dir_success_log_file': '.run_dir_success_log.jsonl',
    'run_dir_success_log_meta_file': '.run_dir_success_log.meta.json',
    'run_dir_error_log_file': '.run_dir_error_log.jsonl',
}

def get_config() -> Dict[str, Any]:
    """Get configuration with environment variable overrides."""
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if present
    config['request_timeout'] = int(os.getenv('AI_TESTER_TIMEOUT', config['request_timeout']))
    config['max_retries'] = int(os.getenv('AI_TESTER_MAX_RETRIES', config['max_retries']))
    config['retry_delay'] = float(os.getenv('AI_TESTER_RETRY_DELAY', config['retry_delay']))
    config['log_level'] = os.getenv('AI_TESTER_LOG_LEVEL', config['log_level'])
    config['default_endpoint'] = os.getenv('AI_TESTER_ENDPOINT', config['default_endpoint'])
    
    return config
"""
Example implementations for custom question sources and output destinations.

These examples show the minimal code needed to extend AI Tester with new functionality.
Copy and modify these templates for your own implementations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from src.core.question_sources import QuestionSource
from src.core.output_destinations import OutputDestination

logger = logging.getLogger(__name__)


# =============================================================================
# QUESTION SOURCE EXAMPLES
# =============================================================================

class APIQuestionSource(QuestionSource):
    """Example: Load questions from a REST API."""
    
    def __init__(self, api_url: str, api_key: str = None):
        """Initialize with API configuration."""
        self.api_url = api_url
        self.api_key = api_key
        
        # Add any validation here
        if not api_url:
            raise ValueError("API URL is required")
    
    def get_questions(self) -> List[str]:
        """Fetch questions from the API."""
        try:
            import requests
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.get(self.api_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Adapt to your API response format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'questions' in data:
                return data['questions']
            else:
                logger.warning(f"Unexpected API response format: {type(data)}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch questions from API: {e}")
            return []
    
    def get_source_info(self) -> Dict[str, Any]:
        """Return information about this source."""
        return {
            'type': 'api_rest',
            'api_url': self.api_url,
            'has_api_key': bool(self.api_key),
            'description': 'REST API question source'
        }


class CSVQuestionSource(QuestionSource):
    """Example: Load questions from a CSV file."""
    
    def __init__(self, file_path: str, question_column: str = 'question'):
        """Initialize with CSV file configuration."""
        self.file_path = file_path
        self.question_column = question_column
        
        # Validate file exists
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    def get_questions(self) -> List[str]:
        """Load questions from CSV file."""
        try:
            import pandas as pd
            
            df = pd.read_csv(self.file_path)
            
            if self.question_column not in df.columns:
                logger.error(f"Column '{self.question_column}' not found in CSV")
                return []
            
            questions = df[self.question_column].dropna().tolist()
            return [str(q) for q in questions]
            
        except Exception as e:
            logger.error(f"Failed to load questions from CSV: {e}")
            return []
    
    def get_source_info(self) -> Dict[str, Any]:
        """Return information about this source."""
        return {
            'type': 'csv_file',
            'file_path': self.file_path,
            'question_column': self.question_column,
            'description': 'CSV file question source'
        }


# =============================================================================
# OUTPUT DESTINATION EXAMPLES
# =============================================================================

class WebhookOutputDestination(OutputDestination):
    """Example: Send results to a webhook endpoint."""
    
    def __init__(self, webhook_url: str, api_key: str = None):
        """Initialize with webhook configuration."""
        self.webhook_url = webhook_url
        self.api_key = api_key
        
        if not webhook_url:
            raise ValueError("Webhook URL is required")
    
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send results to webhook."""
        try:
            import requests
            
            # Prepare payload
            payload = {
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results),
                'results': results,
                'metadata': metadata or {}
            }
            
            # Prepare headers
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Send webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Successfully sent {len(results)} results to webhook")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send results to webhook: {e}")
            return False
    
    def get_destination_info(self) -> Dict[str, Any]:
        """Return information about this destination."""
        return {
            'type': 'webhook',
            'webhook_url': self.webhook_url,
            'has_api_key': bool(self.api_key)
        }


class SlackOutputDestination(OutputDestination):
    """Example: Send results summary to Slack."""
    
    def __init__(self, webhook_url: str, channel: str = '#ai-testing'):
        """Initialize with Slack configuration."""
        self.webhook_url = webhook_url
        self.channel = channel
        
        if not webhook_url:
            raise ValueError("Slack webhook URL is required")
    
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send results summary to Slack."""
        try:
            import requests
            
            # Create summary
            total_results = len(results)
            successful_results = len([r for r in results if 'error' not in r])
            failed_results = total_results - successful_results
            
            # Create Slack message
            color = "good" if failed_results == 0 else "warning" if failed_results < total_results else "danger"
            
            message = {
                "channel": self.channel,
                "attachments": [
                    {
                        "color": color,
                        "title": "AI Tester Results",
                        "fields": [
                            {
                                "title": "Total Questions",
                                "value": str(total_results),
                                "short": True
                            },
                            {
                                "title": "Successful",
                                "value": str(successful_results),
                                "short": True
                            },
                            {
                                "title": "Failed",
                                "value": str(failed_results),
                                "short": True
                            }
                        ],
                        "footer": f"Tested endpoint: {metadata.get('base_url', 'Unknown') if metadata else 'Unknown'}",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(self.webhook_url, json=message, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully sent summary to Slack channel {self.channel}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send results to Slack: {e}")
            return False
    
    def get_destination_info(self) -> Dict[str, Any]:
        """Return information about this destination."""
        return {
            'type': 'slack',
            'channel': self.channel,
            'has_webhook': bool(self.webhook_url)
        }


# =============================================================================
# REGISTRATION EXAMPLES
# =============================================================================

"""
To register these custom implementations, add them to the respective factory classes:

# In src/core/question_sources.py
class QuestionSourceFactory:
    @staticmethod
    def create_source(source_type: str, **kwargs) -> QuestionSource:
        # ... existing code ...
        elif source_type.lower() == 'api_rest':
            api_url = kwargs.get('api_url')
            api_key = kwargs.get('api_key')
            return APIQuestionSource(api_url, api_key)
        elif source_type.lower() == 'csv_file':
            file_path = kwargs.get('file_path')
            question_column = kwargs.get('question_column', 'question')
            return CSVQuestionSource(file_path, question_column)
        # ... rest of method ...

# In src/core/output_destinations.py
class OutputDestinationFactory:
    @staticmethod
    def create_destination(destination_type: str, **kwargs) -> OutputDestination:
        # ... existing code ...
        elif destination_type.lower() == 'webhook':
            webhook_url = kwargs.get('webhook_url')
            api_key = kwargs.get('api_key')
            return WebhookOutputDestination(webhook_url, api_key)
        elif destination_type.lower() == 'slack':
            webhook_url = kwargs.get('webhook_url')
            channel = kwargs.get('channel', '#ai-testing')
            return SlackOutputDestination(webhook_url, channel)
        # ... rest of method ...
"""


# =============================================================================
# ENVIRONMENT VARIABLE EXAMPLES
# =============================================================================

"""
Example environment variables for these custom implementations:

# API Question Source
AI_TESTER_QUESTIONS_SOURCE_TYPE=api_rest
AI_TESTER_API_URL=https://api.mycompany.com/questions
AI_TESTER_API_KEY=your-secret-api-key

# CSV Question Source  
AI_TESTER_QUESTIONS_SOURCE_TYPE=csv_file
AI_TESTER_CSV_FILE_PATH=./questions.csv
AI_TESTER_CSV_QUESTION_COLUMN=question_text

# Webhook Output Destination
AI_TESTER_OUTPUT_DESTINATION_TYPE=webhook
AI_TESTER_WEBHOOK_URL=https://api.mycompany.com/ai-test-results
AI_TESTER_WEBHOOK_API_KEY=your-webhook-api-key

# Slack Output Destination
AI_TESTER_OUTPUT_DESTINATION_TYPE=slack
AI_TESTER_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
AI_TESTER_SLACK_CHANNEL=#ai-testing
"""
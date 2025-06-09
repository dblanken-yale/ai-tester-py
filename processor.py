"""Shared question processing logic for AI Tester."""
import uuid
import requests
import yaml
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import config

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class QuestionProcessor:
    """Handles processing of questions against AI endpoints."""
    
    def __init__(self, base_url: str, endpoint: str = None, debug: bool = False):
        self.config = config.get_config()
        self.base_url = self._validate_url(base_url)
        self.endpoint = endpoint or self.config['default_endpoint']
        self.debug = debug
        self.url = self.base_url + self.endpoint
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format=self.config['log_format']
        )

    def _validate_url(self, url: str) -> str:
        """Validate and sanitize URL input."""
        if not url:
            raise ValidationError("URL cannot be empty")
        
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(f"Invalid URL format: {url}")
        
        if parsed.scheme not in ('http', 'https'):
            raise ValidationError(f"URL must use http or https scheme: {url}")
        
        return url.rstrip('/')

    def get_questions_from_body(self, questions_data: Any) -> List[str]:
        """Parse questions from various input formats with validation."""
        if isinstance(questions_data, list):
            questions = questions_data
        elif isinstance(questions_data, str):
            try:
                questions = yaml.safe_load(questions_data)
            except yaml.YAMLError as e:
                raise ValidationError(f"Invalid YAML format: {e}")
        else:
            raise ValidationError("Questions must be a list or YAML string")
        
        if not isinstance(questions, list):
            raise ValidationError("Questions must be a list")
        
        if not questions:
            raise ValidationError("Questions list cannot be empty")
        
        # Validate each question
        for i, question in enumerate(questions):
            if not isinstance(question, str):
                raise ValidationError(f"Question {i+1} must be a string")
            if not question.strip():
                raise ValidationError(f"Question {i+1} cannot be empty")
        
        return questions

    def get_questions_from_file(self, filename: str) -> List[str]:
        """Read and validate questions from a file."""
        try:
            with open(filename, 'r') as file:
                data = yaml.safe_load(file)
                return self.get_questions_from_body(data)
        except FileNotFoundError:
            raise ValidationError(f"Questions file not found: {filename}")
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in {filename}: {e}")

    def create_payload(self, question: str) -> Dict[str, Any]:
        """Create request payload for a question."""
        if not question.strip():
            raise ValidationError("Question cannot be empty")
        
        payload_template = {"role": "user"}
        return {
            "messages": [
                {
                    "id": str(uuid.uuid4()),
                    "date": datetime.now(timezone.utc).isoformat(),
                    "content": question.strip(),
                    **payload_template,
                },
            ],
        }

    def _make_request(self, payload: Dict[str, Any]) -> bytes:
        """Make HTTP request with timeout and proper error handling."""
        try:
            response = requests.post(
                self.url, 
                json=payload,
                timeout=self.config['request_timeout']
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.Timeout:
            raise Exception(f"Request timed out after {self.config['request_timeout']} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Failed to connect to {self.url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def _parse_response(self, content: bytes, question: str) -> Dict[str, Any]:
        """Parse response content with improved validation."""
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise Exception("Response contains invalid UTF-8 encoding")
        
        try:
            # Parse each line as JSON
            json_content_array = []
            for line in text_content.split('\n'):
                line = line.strip()
                if line and line != '{}':
                    try:
                        json_content_array.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON line: {line[:100]}")
                        continue
            
            if not json_content_array:
                raise Exception("No valid JSON content found in response")
            
            # Extract messages with validation
            joined_choice_messages = []
            for json_line in json_content_array:
                if not isinstance(json_line, dict):
                    continue
                
                choices = json_line.get('choices', [])
                if not choices or not isinstance(choices, list):
                    continue
                
                choice = choices[0]
                if not isinstance(choice, dict):
                    continue
                
                messages = choice.get('messages', [])
                if not isinstance(messages, list):
                    continue
                
                content_parts = []
                for msg in messages:
                    if isinstance(msg, dict) and 'content' in msg:
                        content_parts.append(str(msg['content']))
                
                if content_parts:
                    joined_choice_messages.append(''.join(content_parts))
            
            if not joined_choice_messages:
                raise Exception("No valid choice messages found in response")
            
            # Parse citations from first message
            citations = []
            citations_contents = []
            
            try:
                first_message_data = json.loads(joined_choice_messages[0])
                if isinstance(first_message_data, dict) and 'citations' in first_message_data:
                    citation_list = first_message_data['citations']
                    if isinstance(citation_list, list):
                        for citation in citation_list:
                            if isinstance(citation, dict):
                                if 'url' in citation:
                                    citations.append(str(citation['url']))
                                if self.debug and 'content' in citation:
                                    citations_contents.append(str(citation['content']))
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse citations: {e}")
            
            # Join remaining messages as answer
            answer = ''.join(joined_choice_messages[1:])
            
            result = {
                "citations": citations,
                "answer": answer,
                "question": question
            }
            
            if self.debug and citations_contents:
                result["citationsContents"] = citations_contents
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to parse response: {str(e)}")

    def process_question_with_retry(self, question: str) -> Optional[Dict[str, Any]]:
        """Process a single question with retry logic and exponential backoff."""
        if not question.strip():
            logger.error("Empty question provided")
            return None
        
        delay = self.config['retry_delay']
        
        for attempt in range(1, self.config['max_retries'] + 1):
            try:
                logger.info(f"Processing question (attempt {attempt}/{self.config['max_retries']}): {question[:50]}...")
                
                payload = self.create_payload(question)
                content = self._make_request(payload)
                result = self._parse_response(content, question)
                
                logger.info(f"Successfully processed question: {question[:50]}...")
                return result
                
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for question '{question[:50]}...': {str(e)}")
                
                if attempt == self.config['max_retries']:
                    logger.error(f"All {self.config['max_retries']} attempts failed for question: {question[:50]}...")
                    return {"question": question, "error": str(e)}
                
                if self.config['exponential_backoff']:
                    delay *= self.config['backoff_multiplier']
                
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
        
        return None

    def process_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Process multiple questions and return results."""
        if not questions:
            logger.warning("No questions provided")
            return []
        
        results = []
        logger.info(f"Processing {len(questions)} questions...")
        
        for i, question in enumerate(questions, 1):
            logger.info(f"Processing question {i}/{len(questions)}")
            result = self.process_question_with_retry(question)
            if result is not None:
                results.append(result)
        
        logger.info(f"Completed processing. {len(results)} results generated.")
        return results
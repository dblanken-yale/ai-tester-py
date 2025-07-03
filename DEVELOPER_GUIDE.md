# Developer Guide: Extending AI Tester

This guide shows how to add new question sources and output destinations to AI Tester.

## Architecture Overview

AI Tester uses a modular architecture with abstract base classes and factory patterns:

- **Question Sources** (`src/core/question_sources.py`): Define how questions are loaded
- **Output Destinations** (`src/core/output_destinations.py`): Define how results are saved
- **Factory Classes**: Automatically register and create instances based on configuration

## Adding a New Question Source

### Step 1: Create the Question Source Class

All question sources must inherit from `QuestionSource` and implement two methods:

```python
# src/core/question_sources.py

class MyCustomQuestionSource(QuestionSource):
    """Custom question source example."""
    
    def __init__(self, config_param1: str, config_param2: int = 10):
        """Initialize with your custom parameters."""
        self.config_param1 = config_param1
        self.config_param2 = config_param2
        # Add any initialization logic here
    
    def get_questions(self) -> List[str]:
        """
        Retrieve questions from your custom source.
        
        Returns:
            List[str]: A list of question strings.
        """
        # Your custom logic here
        questions = []
        
        # Example: Load from API, database, file, etc.
        # questions = self._fetch_from_api()
        # questions = self._load_from_database()
        
        return questions
    
    def get_source_info(self) -> Dict[str, Any]:
        """
        Get metadata about your source.
        
        Returns:
            Dict[str, Any]: Information about the source
        """
        return {
            'type': 'my_custom_source',
            'config_param1': self.config_param1,
            'config_param2': self.config_param2,
            'description': 'My custom question source implementation'
        }
```

### Step 2: Register in Factory

Add your source to the `QuestionSourceFactory.create_source()` method:

```python
# src/core/question_sources.py

class QuestionSourceFactory:
    @staticmethod
    def create_source(source_type: str, **kwargs) -> QuestionSource:
        if source_type.lower() == 'yaml':
            # ... existing code ...
        elif source_type.lower() == 'my_custom_source':
            config_param1 = kwargs.get('config_param1')
            config_param2 = kwargs.get('config_param2', 10)
            return MyCustomQuestionSource(config_param1, config_param2)
        else:
            raise ValueError(f"Unsupported question source type: {source_type}")
    
    @staticmethod
    def get_available_sources() -> List[str]:
        return ['yaml', 'dummy', 'postgresql', 'my_custom_source']
```

### Step 3: Add Configuration Support

Update configuration classes to support your new source:

```python
# src/config/settings.py

@classmethod
def from_environment(cls) -> 'AITesterConfig':
    # ... existing code ...
    elif source_type == 'my_custom_source':
        question_source.custom_config = {
            'config_param1': os.getenv('AI_TESTER_CUSTOM_PARAM1'),
            'config_param2': int(os.getenv('AI_TESTER_CUSTOM_PARAM2', '10'))
        }
```

### Step 4: Update Service Layer

Add support in the question service:

```python
# src/services/question_service.py

def _create_question_source(self):
    config = self.config.question_source
    # ... existing code ...
    elif config.source_type.lower() == 'my_custom_source':
        return QuestionSourceFactory.create_source(
            'my_custom_source',
            config_param1=config.custom_config.get('config_param1'),
            config_param2=config.custom_config.get('config_param2', 10)
        )
```

## Adding a New Output Destination

### Step 1: Create the Output Destination Class

All output destinations must inherit from `OutputDestination`:

```python
# src/core/output_destinations.py

class MyCustomOutputDestination(OutputDestination):
    """Custom output destination example."""
    
    def __init__(self, endpoint_url: str, api_key: str, format_type: str = 'json'):
        """Initialize with your custom parameters."""
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.format_type = format_type
    
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Write results to your custom destination.
        
        Args:
            results: List of result dictionaries
            metadata: Optional run metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare data for your destination
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results),
                'results': results,
                'metadata': metadata
            }
            
            # Your custom logic here
            # Example: Send to API, write to database, etc.
            # success = self._send_to_api(output_data)
            # success = self._write_to_database(output_data)
            
            logger.info(f"Successfully wrote {len(results)} results to custom destination")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to custom destination: {e}")
            return False
    
    def get_destination_info(self) -> Dict[str, Any]:
        """Get information about the destination."""
        return {
            'type': 'my_custom_destination',
            'endpoint_url': self.endpoint_url,
            'format_type': self.format_type,
            'has_api_key': bool(self.api_key)
        }
```

### Step 2: Register in Factory

Add your destination to the `OutputDestinationFactory`:

```python
# src/core/output_destinations.py

class OutputDestinationFactory:
    @staticmethod
    def create_destination(destination_type: str, **kwargs) -> OutputDestination:
        destination_type = destination_type.lower()
        
        if destination_type == 'json':
            # ... existing code ...
        elif destination_type == 'my_custom_destination':
            endpoint_url = kwargs.get('endpoint_url')
            api_key = kwargs.get('api_key')
            format_type = kwargs.get('format_type', 'json')
            return MyCustomOutputDestination(endpoint_url, api_key, format_type)
        else:
            raise ValueError(f"Unsupported output destination type: {destination_type}")
    
    @staticmethod
    def get_available_destinations() -> List[str]:
        return ['json', 'excel', 'postgresql', 'console', 'my_custom_destination']
```

### Step 3: Add Configuration Support

Update configuration for your new destination:

```python
# src/config/settings.py

@classmethod
def from_environment(cls) -> 'AITesterConfig':
    # ... existing code ...
    elif dest_type == 'my_custom_destination':
        output_destination.custom_config = {
            'endpoint_url': os.getenv('AI_TESTER_CUSTOM_ENDPOINT_URL'),
            'api_key': os.getenv('AI_TESTER_CUSTOM_API_KEY'),
            'format_type': os.getenv('AI_TESTER_CUSTOM_FORMAT', 'json')
        }
```

### Step 4: Update Service Layer

Add support in the service layer:

```python
# src/services/question_service.py

def _create_output_destination(self):
    config = self.config.output_destination
    # ... existing code ...
    elif config.destination_type.lower() == 'my_custom_destination':
        return OutputDestinationFactory.create_destination(
            'my_custom_destination',
            endpoint_url=config.custom_config.get('endpoint_url'),
            api_key=config.custom_config.get('api_key'),
            format_type=config.custom_config.get('format_type', 'json')
        )
```

## Reference Examples

### DummyQuestionSource Implementation

The `DummyQuestionSource` is a perfect simple example:

```python
class DummyQuestionSource(QuestionSource):
    def __init__(self, questions: List[str] = None):
        self.questions = questions or [
            "What is the capital of France?",
            "How do you reverse a string in Python?",
            # ... more default questions
        ]
    
    def get_questions(self) -> List[str]:
        return self.questions.copy()
    
    def get_source_info(self) -> Dict[str, Any]:
        return {
            'type': 'dummy_static',
            'question_count': len(self.questions),
            'description': 'Static in-memory question source for testing'
        }
```

### ConsoleDestination Implementation

The `ConsoleDestination` shows a simple output implementation:

```python
class ConsoleDestination(OutputDestination):
    def __init__(self, format_type: str = 'json', detailed: bool = True):
        self.format_type = format_type
        self.detailed = detailed
    
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            if self.format_type == 'json':
                output_data = {
                    'timestamp': datetime.now().isoformat(),
                    'total_results': len(results),
                    'results': results
                }
                if metadata:
                    output_data['metadata'] = metadata
                
                print(json.dumps(output_data, indent=2, ensure_ascii=False))
            
            return True
        except Exception as e:
            logger.error(f"Failed to write results to console: {e}")
            return False
```

## Environment Variable Naming Convention

Follow these patterns for environment variables:

### Question Sources:
- `AI_TESTER_QUESTIONS_SOURCE_TYPE` - The source type name
- `AI_TESTER_<SOURCE>_<PARAM>` - Source-specific parameters

Examples:
- `AI_TESTER_POSTGRES_CONNECTION_STRING`
- `AI_TESTER_CUSTOM_PARAM1`

### Output Destinations:
- `AI_TESTER_OUTPUT_DESTINATION_TYPE` - The destination type name  
- `AI_TESTER_<DESTINATION>_<PARAM>` - Destination-specific parameters

Examples:
- `AI_TESTER_POSTGRES_TABLE`
- `AI_TESTER_CUSTOM_ENDPOINT_URL`

## Testing Your Extensions

### Unit Tests

Create tests for your new components:

```python
# tests/test_my_custom_source.py

import pytest
from src.core.question_sources import QuestionSourceFactory

def test_my_custom_source_creation():
    source = QuestionSourceFactory.create_source(
        'my_custom_source',
        config_param1='test_value',
        config_param2=20
    )
    
    assert source is not None
    assert source.config_param1 == 'test_value'
    assert source.config_param2 == 20

def test_my_custom_source_get_questions():
    source = QuestionSourceFactory.create_source(
        'my_custom_source',
        config_param1='test_value'
    )
    
    questions = source.get_questions()
    assert isinstance(questions, list)
    assert len(questions) > 0
```

### Integration Tests

Test with the full service:

```python
# tests/test_integration_custom.py

from src.config.settings import AITesterConfig, QuestionSourceConfig, OutputDestinationConfig
from src.services.question_service import QuestionProcessingService

def test_custom_source_integration():
    # Configure with your custom source
    config = AITesterConfig(
        base_url="https://test.example.com",
        question_source=QuestionSourceConfig(
            source_type='my_custom_source',
            custom_config={'config_param1': 'test'}
        ),
        output_destination=OutputDestinationConfig(
            destination_type='console'
        )
    )
    
    service = QuestionProcessingService(config)
    # Test the service can create your source
    source = service._create_question_source()
    assert source.get_source_info()['type'] == 'my_custom_source'
```

## Documentation Updates

When adding new extensions, update:

1. **AZURE_FUNCTION_CONFIG.md** - Add environment variable documentation
2. **README.md** - Add usage examples
3. **This file** - Add your extension as a reference example

## Best Practices

1. **Error Handling**: Always wrap operations in try/catch blocks
2. **Logging**: Use the logger for informational and error messages
3. **Validation**: Validate inputs in `__init__` methods
4. **Documentation**: Include clear docstrings with examples
5. **Testing**: Write both unit and integration tests
6. **Configuration**: Use environment variables for runtime configuration
7. **Fallbacks**: Provide reasonable defaults where possible

## Getting Help

- Check existing implementations in `src/core/` for patterns
- Look at the `DummyQuestionSource` and `ConsoleDestination` for simple examples
- Review `PostgreSQLQuestionSource` for more complex database patterns
- Examine the factory classes for registration patterns
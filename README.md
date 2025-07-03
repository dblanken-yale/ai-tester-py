# AI Tester

AI Tester automates the testing of AI endpoints using configurable question sets, exporting results to formats like Excel and JSON. It supports both command-line interface (CLI) and Azure Function execution modes.

## Architecture

The codebase is organized into modules for better maintainability:

```
src/
├── cli/           # Command-line interface
├── azure/         # Azure Function implementation  
├── services/      # Business logic and orchestration
├── core/          # Domain models (questions, outputs, processing)
├── config/        # Configuration management
└── utils/         # Shared utilities
```

## Quick Start

### Setup

```bash
./install.sh
```

### Running Tests (CLI Mode)

- **Single question file:**
  ```bash
  python test_questions.py <url> --questions questions.yml
  ```
- **Multiple question files in a directory:**
  ```bash
  ./run_dir.sh <directory> <url>
  ```
- **Custom output format:**
  ```bash
  python test_questions.py <url> --format excel --outfile results.xlsx
  ```
- **Debug mode (includes citation contents):**
  ```bash
  python test_questions.py <url> --debug
  ```

### Azure Function Mode

The AI Tester can run as an Azure Function with timer triggers for automated testing. Configuration is done through environment variables (see `AZURE_FUNCTION_CONFIG.md`).

## Configuration

Set these environment variables as needed:

- `AI_TESTER_TIMEOUT`: Request timeout in seconds (default: 30)
- `AI_TESTER_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `AI_TESTER_RETRY_DELAY`: Initial retry delay in seconds (default: 2)
- `AI_TESTER_LOG_LEVEL`: Logging level (default: INFO)
- `AI_TESTER_ENDPOINT`: Default API endpoint (default: /conversation)

## Output Formats

You can export results in different formats:

- **JSON (stdout):**
  ```bash
  python test_questions.py <url> > output.json
  ```
- **JSON (to file):**
  ```bash
  python test_questions.py <url> --outfile output.json
  ```
- **Excel:**
  ```bash
  python test_questions.py <url> --format excel --outfile output.xlsx
  ```

## Debugging

Enable debug mode for detailed output, including citation data (shown in raw JSON):

```bash
python test_questions.py <url> --debug
```

## Batch Testing

To test multiple question sets at once:

```bash
./run_dir.sh <folder_with_yaml_files> <url>
```

This creates a `<folder_with_yaml_files>_output` directory containing `.xlsx` files matching your YAML filenames.

## Custom Question Files

You can specify any questions file using the `--questions` flag:

```bash
python test_questions.py <url> --questions my_questions.yml
```

## How It Works

AI Tester sends questions from a YAML file to your endpoint, then outputs the question, citations, and response in a readable format.

## Code Conventions

- **Architecture:**
  - Shared core logic in `src/core/` for domain models and processing
  - Separate entry points for CLI (`src/cli/`) and Azure Functions (`src/azure/`)
  - Service layer (`src/services/`) for orchestration and business logic
  - Configuration management through typed classes in `src/config/`
  
- **Error Handling:**
  - Use `ValidationError` for input validation failures
  - Structured logging with configurable levels
  - Graceful fallbacks for missing configurations
  
- **Request Processing:**
  - All HTTP requests include timeouts and retries
  - Exponential backoff with configurable parameters
  - Comprehensive response validation
  
- **Backward Compatibility:**
  - Original file interfaces maintained through wrapper modules
  - Legacy output formats supported via compatibility layer
  - Existing scripts continue to work without modification

## Extending AI Tester

AI Tester is designed to be easily extensible with new question sources and output destinations:

- **Question Sources**: Load questions from YAML files, databases, APIs, or custom sources
- **Output Destinations**: Save results to JSON, Excel, databases, or custom destinations
- **Factory Pattern**: New extensions are automatically registered and available

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for detailed instructions on adding:
- Custom question sources (e.g., REST APIs, cloud storage, custom databases)
- Custom output destinations (e.g., monitoring systems, dashboards, notifications)

### Available Extensions:
- **Question Sources**: YAML, Dummy (testing), PostgreSQL
- **Output Destinations**: JSON, Excel, PostgreSQL, Console

## Testing Notes

AI Tester expects endpoint responses in a specific JSON streaming format:

- Multiple JSON objects per line
- First message contains citations
- Subsequent messages contain the main response text
- Always validate responses, as formats may vary between endpoints

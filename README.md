# AI Tester

AI Tester automates the testing of AI endpoints using configurable question sets, exporting results to formats like Excel and JSON.

## Quick Start

### Setup

```bash
./install.sh
```

### Running Tests

- **Single question file:**
  ```bash
  python test-questions.py <url> --questions questions.yml
  ```
- **Multiple question files in a directory:**
  ```bash
  ./run_dir.sh <directory> <url>
  ```
- **Custom output format:**
  ```bash
  python test-questions.py <url> --format excel --outfile results.xlsx
  ```
- **Debug mode (includes citation contents):**
  ```bash
  python test-questions.py <url> --debug
  ```

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
  python test-questions.py <url> > output.json
  ```
- **JSON (to file):**
  ```bash
  python test-questions.py <url> --outfile output.json
  ```
- **Excel:**
  ```bash
  python test-questions.py <url> --format excel --outfile output.xlsx
  ```

## Debugging

Enable debug mode for detailed output, including citation data (shown in raw JSON):

```bash
python test-questions.py <url> --debug
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
python test-questions.py <url> --questions my_questions.yml
```

## How It Works

AI Tester sends questions from a YAML file to your endpoint, then outputs the question, citations, and response in a readable format.

## Code Conventions

- **Error Handling:**
  - Use `ValidationError` for input validation failures.
  - Log errors appropriately with the structured logger.
  - Processing functions should return `None` or error dictionaries, not raise exceptions.
- **Request Processing:**
  - All HTTP requests must include timeouts.
  - Use exponential backoff for retries.
  - Validate response structure before parsing.
- **File Organization:**
  - Configuration: `config.py`
  - Shared logic: `processor.py`
  - Interface-specific code: respective modules
- **Output Formatting:**
  - Register new formats with `@register_output_format`.
  - Support both file and console output in formatters.
  - Maintain backward compatibility for output options.

## Testing Notes

AI Tester expects endpoint responses in a specific JSON streaming format:

- Multiple JSON objects per line
- First message contains citations
- Subsequent messages contain the main response text
- Always validate responses, as formats may vary between endpoints

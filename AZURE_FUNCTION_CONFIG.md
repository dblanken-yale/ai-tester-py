# Azure Function Configuration

This document describes the environment variables available for configuring the AI Tester Azure Function.

## New Modular Architecture

The Azure Function now uses a modular architecture with the following benefits:

- **Shared Core Logic**: Same processing engine used for both CLI and Azure Function modes
- **Typed Configuration**: Environment variables are parsed into typed configuration classes
- **Better Error Handling**: Structured error handling with fallback mechanisms
- **Extensible Design**: Easy to add new question sources and output destinations

The function entry point is now at `src/azure/function_app.py`, while maintaining backward compatibility through the root `function_app.py`.

## Required Configuration

### AI_TESTER_BASE_URL
- **Description**: Base URL of the AI endpoint to send questions to
- **Default**: `https://your-ai-endpoint.example.com`
- **Example**: `https://your-ai-endpoint.azurewebsites.net`

### AI_TESTER_SCHEDULE
- **Description**: CRON expression for timer trigger schedule (NCRONTAB format)
- **Default**: `0 */5 * * * *` (every 5 minutes)
- **Format**: `{second} {minute} {hour} {day} {month} {day-of-week}`
- **Examples**: 
  - `0 0 * * * *` - Every hour at the top of the hour
  - `0 */15 * * * *` - Every 15 minutes
  - `0 0 9 * * MON-FRI` - Every weekday at 9:00 AM
  - `0 30 2 * * *` - Every day at 2:30 AM

## Question Source Configuration

### AI_TESTER_QUESTIONS_SOURCE_TYPE
- **Description**: Type of question source to use
- **Default**: `yaml`
- **Options**: 
  - `yaml` - Read questions from YAML file
  - `dummy` - Use built-in test questions
  - `postgresql` - Read questions from PostgreSQL database

### AI_TESTER_QUESTIONS_FILE
- **Description**: Path to YAML questions file (when using yaml source)
- **Default**: `./questions.yml`
- **Example**: `./my-questions.yml`

## Output Configuration

### AI_TESTER_OUTPUT_FORMAT
- **Description**: Format for output data
- **Default**: `json`
- **Options**: `json`, `excel`

### AI_TESTER_OUTPUT_FILE
- **Description**: Output file path (optional, overrides smart naming)
- **Default**: None (uses smart file naming)
- **Example**: `./results.json` or `./results.xlsx`

### AI_TESTER_OUTPUT_TEMPLATE
- **Description**: Base template for smart file naming
- **Default**: `results`
- **Example**: `test_results`, `qa_output`

### AI_TESTER_OUTPUT_DIRECTORY
- **Description**: Directory for output files
- **Default**: Current directory
- **Example**: `./outputs`, `/app/results`

### AI_TESTER_INCLUDE_DOMAIN
- **Description**: Include domain name in filename
- **Default**: `true`
- **Options**: `true`, `false`

### AI_TESTER_INCLUDE_TIMESTAMP
- **Description**: Include timestamp in filename
- **Default**: `true`
- **Options**: `true`, `false`

### AI_TESTER_TIMESTAMP_FORMAT
- **Description**: Format for timestamp in filename
- **Default**: `datetime`
- **Options**: `datetime`, `date`, `time`, `unix`

## Debug and Logging

### AI_TESTER_DEBUG
- **Description**: Enable debug mode for detailed logging
- **Default**: `false`
- **Options**: `true`, `false`

## Advanced Question Source Options

### Dummy Source
For testing with built-in questions:

```bash
AI_TESTER_QUESTIONS_SOURCE_TYPE=dummy
```

To use custom dummy questions:
```bash
AI_TESTER_QUESTIONS_SOURCE_TYPE=dummy
AI_TESTER_DUMMY_QUESTIONS=["What is Azure?", "How does cloud computing work?"]
```

### PostgreSQL Source
For reading questions from a PostgreSQL database:

#### AI_TESTER_POSTGRES_CONNECTION_STRING
- **Description**: PostgreSQL connection string
- **Required**: Yes (when using postgresql source)
- **Example**: `postgresql://username:password@hostname:5432/database_name`

#### AI_TESTER_POSTGRES_TABLE
- **Description**: Database table containing questions
- **Default**: `questions`
- **Example**: `my_questions_table`

#### AI_TESTER_POSTGRES_COLUMN
- **Description**: Column name containing question text
- **Default**: `question_text`
- **Example**: `question_content`

**PostgreSQL Example Configuration:**
```bash
AI_TESTER_QUESTIONS_SOURCE_TYPE=postgresql
AI_TESTER_POSTGRES_CONNECTION_STRING=postgresql://user:pass@localhost:5432/mydb
AI_TESTER_POSTGRES_TABLE=questions
AI_TESTER_POSTGRES_COLUMN=question_text
```

## Local Development

For local development, set these variables in `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AI_TESTER_BASE_URL": "https://your-ai-endpoint.example.com",
    "AI_TESTER_SCHEDULE": "0 */5 * * * *",
    "AI_TESTER_QUESTIONS_SOURCE_TYPE": "yaml",
    "AI_TESTER_QUESTIONS_FILE": "./questions.yml",
    "AI_TESTER_OUTPUT_DESTINATION_TYPE": "json",
    "AI_TESTER_OUTPUT_FILE": "./results.json",
    "AI_TESTER_JSON_PRETTY_PRINT": "true",
    "AI_TESTER_DEBUG": "false"
  }
}
```

## Schedule Configuration Examples

The `AI_TESTER_SCHEDULE` supports NCRONTAB format with 6 fields:

### Common Schedule Patterns:
- **Development (every hour)**: `0 0 * * * *`
- **Testing (every 15 minutes)**: `0 */15 * * * *`
- **Production (every 5 minutes)**: `0 */5 * * * *`
- **Business hours only**: `0 */10 9-17 * * MON-FRI`
- **Daily at 2 AM**: `0 0 2 * * *`
- **Twice daily**: `0 0 2,14 * * *`

### Environment-Specific Examples:
```bash
# Development environment - every hour
AI_TESTER_SCHEDULE="0 0 * * * *"

# Staging environment - every 30 minutes during business hours
AI_TESTER_SCHEDULE="0 */30 9-17 * * MON-FRI"

# Production environment - every 5 minutes
AI_TESTER_SCHEDULE="0 */5 * * * *"
```

## Smart File Naming Examples

When using smart file naming, the system automatically generates unique filenames based on the endpoint and timestamp:

### Example Filename Patterns:
```bash
# Base URL: https://api.example.com
# Template: results
# Result: results_api_example_com_2024-01-15_143022.json

# Base URL: https://test.ai.mycompany.com  
# Template: qa_test
# Result: qa_test_test_ai_mycompany_com_2024-01-15_143022.xlsx
```

### Environment Variable Examples:
```bash
# Enable smart naming with domain and timestamp (default)
AI_TESTER_OUTPUT_TEMPLATE="results"
AI_TESTER_INCLUDE_DOMAIN="true"
AI_TESTER_INCLUDE_TIMESTAMP="true"
AI_TESTER_TIMESTAMP_FORMAT="datetime"

# Only domain, no timestamp (for endpoints that run once)
AI_TESTER_OUTPUT_TEMPLATE="endpoint_test"
AI_TESTER_INCLUDE_DOMAIN="true"
AI_TESTER_INCLUDE_TIMESTAMP="false"

# Timestamp only (for single endpoint, multiple runs)
AI_TESTER_OUTPUT_TEMPLATE="daily_check"
AI_TESTER_INCLUDE_DOMAIN="false"
AI_TESTER_INCLUDE_TIMESTAMP="true"
AI_TESTER_TIMESTAMP_FORMAT="date"

# Multiple endpoints to separate directory
AI_TESTER_OUTPUT_DIRECTORY="./test_results"
AI_TESTER_OUTPUT_TEMPLATE="ai_endpoint_test"
```

## Azure Portal Configuration

For production deployment, set these environment variables in the Azure Portal:

1. Go to your Function App in Azure Portal
2. Navigate to Configuration → Application settings
3. Add the required environment variables listed above

## Question Source Switching

The function can dynamically switch between question sources by changing the `AI_TESTER_QUESTIONS_SOURCE_TYPE` environment variable:

- **YAML File** (default): Uses existing questions.yml file
- **Dummy**: Uses built-in test questions for development/testing
- **PostgreSQL**: Connects to database for production question management

No code changes required - just update the environment variable and restart the function.

## Extending with Custom Sources and Destinations

AI Tester supports custom question sources and output destinations. See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for complete instructions.

### Quick Reference for Custom Extensions:

**Custom Question Source:**
```bash
AI_TESTER_QUESTIONS_SOURCE_TYPE="my_custom_source"
AI_TESTER_CUSTOM_PARAM1="value1"
AI_TESTER_CUSTOM_PARAM2="value2"
```

**Custom Output Destination:**
```bash
AI_TESTER_OUTPUT_DESTINATION_TYPE="my_custom_destination"
AI_TESTER_CUSTOM_ENDPOINT_URL="https://api.mycompany.com/results"
AI_TESTER_CUSTOM_API_KEY="your-api-key"
```

**Available Built-in Options:**
- Question Sources: `yaml`, `dummy`, `postgresql`
- Output Destinations: `json`, `excel`, `postgresql`, `console`
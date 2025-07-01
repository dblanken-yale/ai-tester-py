# Azure Function Configuration

This document describes the environment variables available for configuring the AI Tester Azure Function.

## Required Configuration

### AI_TESTER_BASE_URL
- **Description**: Base URL of the AI endpoint to send questions to
- **Default**: `https://your-ai-endpoint.example.com`
- **Example**: `https://your-ai-endpoint.azurewebsites.net`

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
- **Description**: Output file path (optional)
- **Default**: None (outputs to console/logs)
- **Example**: `./results.json` or `./results.xlsx`

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
    "AI_TESTER_QUESTIONS_SOURCE_TYPE": "yaml",
    "AI_TESTER_QUESTIONS_FILE": "./questions.yml",
    "AI_TESTER_OUTPUT_DESTINATION_TYPE": "json",
    "AI_TESTER_OUTPUT_FILE": "./results.json",
    "AI_TESTER_JSON_PRETTY_PRINT": "true",
    "AI_TESTER_DEBUG": "false"
  }
}
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
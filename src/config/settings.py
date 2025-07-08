"""Typed configuration classes for AI Tester."""
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    connection_string: Optional[str] = None
    table_name: str = 'questions'
    question_column: str = 'question_text'
    create_table: bool = True


@dataclass
class QuestionSourceConfig:
    """Configuration for question sources."""
    source_type: str = 'yaml'
    file_path: Optional[str] = None
    database: Optional[DatabaseConfig] = None
    custom_questions: Optional[list] = None

    def __post_init__(self):
        if self.source_type == 'yaml' and not self.file_path:
            self.file_path = './questions.yml'


@dataclass
class OutputDestinationConfig:
    """Configuration for output destinations."""
    destination_type: str = 'console'
    file_path: Optional[str] = None
    file_template: Optional[str] = None  # Template for dynamic file naming
    sheet_name: str = 'Results'
    format_type: str = 'json'
    pretty_print: bool = True
    detailed: bool = True
    database: Optional[DatabaseConfig] = None
    
    # Smart file naming options
    include_domain_in_filename: bool = True
    include_timestamp_in_filename: bool = True
    timestamp_format: str = 'datetime'  # 'datetime', 'date', 'time', 'unix'
    output_directory: Optional[str] = None


@dataclass
class ProcessingConfig:
    """Configuration for question processing."""
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 2.0
    exponential_backoff: bool = True
    backoff_multiplier: float = 1.5
    default_endpoint: str = '/conversation'


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    log_level: str = 'INFO'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    error_log_file: str = '.error_log.jsonl'
    success_log_file: str = '.success_log.jsonl'
    success_log_meta_file: str = '.success_log.meta.json'
    run_dir_success_log_file: str = '.run_dir_success_log.jsonl'
    run_dir_success_log_meta_file: str = '.run_dir_success_log.meta.json'
    run_dir_error_log_file: str = '.run_dir_error_log.jsonl'


@dataclass
class ScheduleConfig:
    """Configuration for Azure Function timer schedule."""
    schedule: str = "0 */5 * * * *"  # Default: every 5 minutes
    
    def validate_cron_expression(self) -> bool:
        """Validate CRON expression format (basic validation)."""
        parts = self.schedule.split()
        return len(parts) == 6  # NCRONTAB format: seconds minutes hours day month dayofweek


@dataclass
class AITesterConfig:
    """Main configuration class for AI Tester."""
    base_url: str
    debug: bool = False
    endpoint: Optional[str] = None
    
    question_source: QuestionSourceConfig = field(default_factory=QuestionSourceConfig)
    output_destination: OutputDestinationConfig = field(default_factory=OutputDestinationConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)

    @classmethod
    def from_environment(cls) -> 'AITesterConfig':
        """Create configuration from environment variables (Azure Function mode)."""
        # Question source configuration
        source_type = os.getenv('AI_TESTER_QUESTIONS_SOURCE_TYPE', 'yaml')
        question_source = QuestionSourceConfig(source_type=source_type)
        
        if source_type == 'yaml':
            question_source.file_path = os.getenv('AI_TESTER_QUESTIONS_FILE', './questions.yml')
        elif source_type == 'postgresql':
            question_source.database = DatabaseConfig(
                connection_string=os.getenv('AI_TESTER_POSTGRES_CONNECTION_STRING'),
                table_name=os.getenv('AI_TESTER_POSTGRES_TABLE', 'questions'),
                question_column=os.getenv('AI_TESTER_POSTGRES_COLUMN', 'question_text')
            )
        elif source_type == 'dummy':
            custom_questions_json = os.getenv('AI_TESTER_DUMMY_QUESTIONS')
            if custom_questions_json:
                try:
                    import json
                    question_source.custom_questions = json.loads(custom_questions_json)
                except json.JSONDecodeError:
                    pass  # Use default dummy questions

        # Output destination configuration
        dest_type = os.getenv('AI_TESTER_OUTPUT_DESTINATION_TYPE', 'console')
        output_destination = OutputDestinationConfig(destination_type=dest_type)
        
        if dest_type == 'json':
            output_destination.file_path = os.getenv('AI_TESTER_OUTPUT_FILE')
            output_destination.file_template = os.getenv('AI_TESTER_OUTPUT_TEMPLATE', 'results')
            output_destination.pretty_print = os.getenv('AI_TESTER_JSON_PRETTY_PRINT', 'true').lower() == 'true'
        elif dest_type == 'excel':
            output_destination.file_path = os.getenv('AI_TESTER_OUTPUT_FILE')
            output_destination.file_template = os.getenv('AI_TESTER_OUTPUT_TEMPLATE', 'results')
            output_destination.sheet_name = os.getenv('AI_TESTER_EXCEL_SHEET_NAME', 'Results')
        elif dest_type == 'postgresql':
            output_destination.database = DatabaseConfig(
                connection_string=os.getenv('AI_TESTER_OUTPUT_POSTGRES_CONNECTION_STRING'),
                table_name=os.getenv('AI_TESTER_OUTPUT_POSTGRES_TABLE', 'ai_results'),
                create_table=os.getenv('AI_TESTER_OUTPUT_POSTGRES_CREATE_TABLE', 'true').lower() == 'true'
            )
        elif dest_type == 'console':
            output_destination.format_type = os.getenv('AI_TESTER_CONSOLE_FORMAT', 'json')
            output_destination.detailed = os.getenv('AI_TESTER_CONSOLE_DETAILED', 'true').lower() == 'true'
        
        # Smart file naming options (apply to all destination types that use files)
        output_destination.include_domain_in_filename = os.getenv('AI_TESTER_INCLUDE_DOMAIN', 'true').lower() == 'true'
        output_destination.include_timestamp_in_filename = os.getenv('AI_TESTER_INCLUDE_TIMESTAMP', 'true').lower() == 'true'
        output_destination.timestamp_format = os.getenv('AI_TESTER_TIMESTAMP_FORMAT', 'datetime')
        output_destination.output_directory = os.getenv('AI_TESTER_OUTPUT_DIRECTORY')

        # Processing configuration
        processing = ProcessingConfig(
            request_timeout=int(os.getenv('AI_TESTER_TIMEOUT', '30')),
            max_retries=int(os.getenv('AI_TESTER_MAX_RETRIES', '3')),
            retry_delay=float(os.getenv('AI_TESTER_RETRY_DELAY', '2.0')),
            default_endpoint=os.getenv('AI_TESTER_ENDPOINT', '/conversation')
        )

        # Logging configuration (use defaults from dataclass)
        logging_config = LoggingConfig(
            log_level=os.getenv('AI_TESTER_LOG_LEVEL', 'INFO')
        )

        # Schedule configuration
        schedule_config = ScheduleConfig(
            schedule=os.getenv('AI_TESTER_SCHEDULE', '0 */5 * * * *')
        )

        return cls(
            base_url=os.getenv('AI_TESTER_BASE_URL', 'https://example.com'),
            debug=os.getenv('AI_TESTER_DEBUG', 'false').lower() == 'true',
            endpoint=os.getenv('AI_TESTER_ENDPOINT'),
            question_source=question_source,
            output_destination=output_destination,
            processing=processing,
            logging=logging_config,
            schedule=schedule_config
        )

    @classmethod
    def from_cli_args(cls, args) -> 'AITesterConfig':
        """Create configuration from command-line arguments (CLI mode)."""
        # Map CLI args to configuration
        source_type = getattr(args, 'source_type', 'yaml')
        question_source = QuestionSourceConfig(
            source_type=source_type,
            file_path=getattr(args, 'questions', None)
        )

        # Output configuration from CLI args
        output_format = getattr(args, 'format', 'json')
        output_file = getattr(args, 'outfile', None)
        
        if output_format == 'postgresql':
            dest_type = 'postgresql'
        elif output_format == 'excel':
            dest_type = 'excel'
        elif output_file and output_file.endswith('.json'):
            dest_type = 'json'
        else:
            dest_type = 'console'

        output_destination = OutputDestinationConfig(
            destination_type=dest_type,
            file_path=output_file,
            file_template=getattr(args, 'template', 'results'),
            format_type='json' if dest_type == 'console' else output_format,
            # CLI defaults for smart naming (can be overridden by env vars)
            include_domain_in_filename=getattr(args, 'include_domain', True),
            include_timestamp_in_filename=getattr(args, 'include_timestamp', False),  # CLI default: no timestamp
            output_directory=getattr(args, 'output_dir', None)
        )

        # Handle PostgreSQL-specific configuration
        if dest_type == 'postgresql':
            postgres_connection = getattr(args, 'postgres_connection', None)
            postgres_table = getattr(args, 'postgres_table', 'ai_results')
            
            if not postgres_connection:
                raise ValueError("PostgreSQL connection string is required when using postgresql format. Use --postgres-connection")
            
            output_destination.database = DatabaseConfig(
                connection_string=postgres_connection,
                table_name=postgres_table,
                create_table=True
            )

        # Processing configuration
        processing = ProcessingConfig(
            request_timeout=int(os.getenv('AI_TESTER_TIMEOUT', '30')),
            max_retries=int(os.getenv('AI_TESTER_MAX_RETRIES', '3')),
            retry_delay=float(os.getenv('AI_TESTER_RETRY_DELAY', '2.0')),
            default_endpoint=getattr(args, 'endpoint', '/conversation')
        )

        return cls(
            base_url=args.url,
            debug=getattr(args, 'debug', False),
            endpoint=getattr(args, 'endpoint', None),
            question_source=question_source,
            output_destination=output_destination,
            processing=processing,
            logging=LoggingConfig(),
            schedule=ScheduleConfig()  # CLI doesn't use schedule, but include for consistency
        )

    def get_legacy_config(self) -> Dict[str, Any]:
        """Convert to legacy config format for backward compatibility."""
        return {
            'request_timeout': self.processing.request_timeout,
            'max_retries': self.processing.max_retries,
            'retry_delay': self.processing.retry_delay,
            'exponential_backoff': self.processing.exponential_backoff,
            'backoff_multiplier': self.processing.backoff_multiplier,
            'default_endpoint': self.processing.default_endpoint,
            'log_level': self.logging.log_level,
            'log_format': self.logging.log_format,
            'error_log_file': self.logging.error_log_file,
            'success_log_file': self.logging.success_log_file,
            'success_log_meta_file': self.logging.success_log_meta_file,
            'run_dir_success_log_file': self.logging.run_dir_success_log_file,
            'run_dir_success_log_meta_file': self.logging.run_dir_success_log_meta_file,
            'run_dir_error_log_file': self.logging.run_dir_error_log_file,
        }
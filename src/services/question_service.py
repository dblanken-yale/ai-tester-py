"""Service layer for orchestrating question processing workflows."""
import logging
import json
import time
import os
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from src.config.settings import AITesterConfig
from src.core.processor import QuestionProcessor, ValidationError
from src.core.question_sources import QuestionSourceFactory
from src.core.output_destinations import OutputDestinationFactory
from src.utils.file_naming import SmartFileNamer

logger = logging.getLogger(__name__)


class QuestionProcessingService:
    """Service for orchestrating the complete question processing workflow."""
    
    def __init__(self, config: AITesterConfig):
        """Initialize the service with configuration."""
        self.config = config
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging based on configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.logging.log_level),
            format=self.config.logging.log_format
        )
    
    def process_questions(self) -> bool:
        """
        Main orchestration method for processing questions.
        
        Returns:
            bool: True if processing completed successfully, False otherwise
        """
        try:
            # Create question source and output destination
            question_source = self._create_question_source()
            output_destination = self._create_output_destination()
            
            # Create processor
            processor = QuestionProcessor(
                base_url=self.config.base_url,
                endpoint=self.config.endpoint or self.config.processing.default_endpoint,
                debug=self.config.debug,
                question_source=question_source
            )
            
            # Get questions
            questions = processor.get_questions_from_source()
            
            # Log configuration info
            source_info = question_source.get_source_info()
            destination_info = output_destination.get_destination_info()
            logger.info(f"Using question source: {source_info}")
            logger.info(f"Using output destination: {destination_info}")
            
            # Handle resumption logic
            current_meta = self._get_run_metadata(questions, source_info)
            previous_meta = self._load_run_metadata()
            successful_questions = self._handle_run_resumption(current_meta, previous_meta)
            
            # Process questions
            results = []
            all_success = True
            
            for question in questions:
                if question in successful_questions:
                    continue  # Skip already processed questions
                
                result = processor.process_question_with_retry(question)
                if result is not None and 'error' not in result:
                    results.append(result)
                    self._log_success(question)
                elif result is not None and 'error' in result:
                    self._log_error(question, result['error'])
                    all_success = False
                else:
                    all_success = False
            
            # Write results
            run_metadata = self._create_run_metadata(questions, results, successful_questions, source_info)
            success = output_destination.write_results(results, run_metadata)
            
            if not success:
                logger.error("Failed to write results to output destination")
                return False
            
            # Clean up success logs if all questions processed successfully
            if all_success and len(successful_questions) + len(results) == len(questions):
                self._cleanup_success_logs()
            
            return True
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to process questions: {e}")
            return False
    
    def _create_question_source(self):
        """Create question source based on configuration."""
        config = self.config.question_source
        
        if config.source_type.lower() == 'yaml':
            return QuestionSourceFactory.create_source('yaml', file_path=config.file_path)
        elif config.source_type.lower() == 'dummy':
            return QuestionSourceFactory.create_source('dummy', questions=config.custom_questions)
        elif config.source_type.lower() == 'postgresql':
            if not config.database or not config.database.connection_string:
                logger.warning("PostgreSQL connection string not provided, falling back to dummy source")
                return QuestionSourceFactory.create_source('dummy')
            
            return QuestionSourceFactory.create_source(
                'postgresql',
                connection_string=config.database.connection_string,
                table_name=config.database.table_name,
                question_column=config.database.question_column
            )
        else:
            logger.warning(f"Unknown source type '{config.source_type}', falling back to YAML")
            return QuestionSourceFactory.create_source('yaml', file_path=config.file_path or './questions.yml')
    
    def _create_output_destination(self):
        """Create output destination based on configuration."""
        config = self.config.output_destination
        
        if config.destination_type.lower() == 'json':
            file_path = self._get_smart_file_path(config, 'json')
            return OutputDestinationFactory.create_destination(
                'json',
                file_path=file_path,
                pretty_print=config.pretty_print
            )
        elif config.destination_type.lower() == 'excel':
            file_path = self._get_smart_file_path(config, 'xlsx')
            return OutputDestinationFactory.create_destination(
                'excel',
                file_path=file_path,
                sheet_name=config.sheet_name
            )
        elif config.destination_type.lower() == 'postgresql':
            if not config.database or not config.database.connection_string:
                logger.warning("PostgreSQL connection string not provided, falling back to console")
                return OutputDestinationFactory.create_destination('console')
            
            return OutputDestinationFactory.create_destination(
                'postgresql',
                connection_string=config.database.connection_string,
                table_name=config.database.table_name,
                create_table=config.database.create_table
            )
        elif config.destination_type.lower() == 'console':
            return OutputDestinationFactory.create_destination(
                'console',
                format_type=config.format_type,
                detailed=config.detailed
            )
        else:
            logger.warning(f"Unknown destination type '{config.destination_type}', defaulting to console")
            return OutputDestinationFactory.create_destination('console')
    
    def _get_smart_file_path(self, config, file_extension: str) -> str:
        """Generate smart file path with domain and timestamp if enabled."""
        # If user provided explicit file path, use it as-is
        if config.file_path:
            return config.file_path
        
        # Use smart file naming
        template = config.file_template or 'results'
        
        if config.include_domain_in_filename or config.include_timestamp_in_filename:
            return SmartFileNamer.generate_output_path(
                base_url=self.config.base_url,
                base_template=template,
                file_extension=file_extension,
                output_dir=config.output_directory,
                include_timestamp=config.include_timestamp_in_filename
            )
        else:
            # Use simple template-based naming
            filename = f"{template}.{file_extension}"
            if config.output_directory:
                from pathlib import Path
                path = Path(config.output_directory) / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                return str(path)
            return filename
    
    def _get_run_metadata(self, questions: List[str], source_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for the current run."""
        return {
            'base_url': self.config.base_url,
            'questions_source_type': self.config.question_source.source_type,
            'questions_source_config': source_info,
            'output_destination_type': self.config.output_destination.destination_type,
            'output_destination_config': {
                'file_path': self.config.output_destination.file_path,
                'format_type': self.config.output_destination.format_type
            },
            'debug': self.config.debug,
            'endpoint': self.config.endpoint or self.config.processing.default_endpoint,
            'total_questions': len(questions)
        }
    
    def _load_run_metadata(self) -> Optional[Dict[str, Any]]:
        """Load metadata from previous run."""
        meta_file = self.config.logging.success_log_meta_file
        if not os.path.exists(meta_file):
            return None
        
        try:
            with open(meta_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load run metadata: {e}")
            return None
    
    def _save_run_metadata(self, metadata: Dict[str, Any]):
        """Save metadata for the current run."""
        try:
            with open(self.config.logging.success_log_meta_file, 'w') as f:
                json.dump(metadata, f)
        except OSError as e:
            logger.warning(f"Failed to save run metadata: {e}")
    
    def _handle_run_resumption(self, current_meta: Dict[str, Any], previous_meta: Optional[Dict[str, Any]]) -> Set[str]:
        """Handle resumption logic for interrupted runs."""
        if previous_meta != current_meta:
            # New run parameters, clear logs
            self._clear_success_logs()
            self._save_run_metadata(current_meta)
            return set()
        else:
            # Same parameters, load successful questions for resumption
            return self._load_successful_questions()
    
    def _load_successful_questions(self) -> Set[str]:
        """Load set of successfully processed questions."""
        success_file = self.config.logging.success_log_file
        if not os.path.exists(success_file):
            return set()
        
        try:
            with open(success_file, 'r') as f:
                return set(json.loads(line)['question'] for line in f if line.strip())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load successful questions: {e}")
            return set()
    
    def _log_success(self, question: str):
        """Log successful question processing."""
        try:
            with open(self.config.logging.success_log_file, 'a') as f:
                f.write(json.dumps({'question': question}) + '\n')
        except OSError as e:
            logger.warning(f"Failed to log success: {e}")
    
    def _log_error(self, question: str, error_message: str):
        """Log error in question processing."""
        try:
            with open(self.config.logging.error_log_file, 'a') as f:
                f.write(json.dumps({
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    'question': question,
                    'error': error_message
                }) + '\n')
        except OSError as e:
            logger.warning(f"Failed to log error: {e}")
    
    def _create_run_metadata(self, questions: List[str], results: List[Dict[str, Any]], 
                           successful_questions: Set[str], source_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for the completed run."""
        return {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'total_questions': len(questions),
            'successful_results': len(results),
            'skipped_questions': len(successful_questions),
            'base_url': self.config.base_url,
            'questions_source': source_info,
            'debug_mode': self.config.debug
        }
    
    def _clear_success_logs(self):
        """Clear success logs for new run."""
        for log_file in [self.config.logging.success_log_file, self.config.logging.success_log_meta_file]:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except OSError as e:
                    logger.warning(f"Failed to remove log file {log_file}: {e}")
    
    def _cleanup_success_logs(self):
        """Clean up success logs after successful completion."""
        self._clear_success_logs()
        logger.info("All questions processed successfully, cleaned up success logs")
import logging
import json
import azure.functions as func
import os
import time
from processor import QuestionProcessor, ValidationError
import config
import outputOptions
from question_sources import QuestionSourceFactory
from output_destinations import OutputDestinationFactory

logging.basicConfig(level=logging.INFO)
app = func.FunctionApp()

def log_error(question, error_message):
    """Logs the error to a JSONL file with timestamp and question."""
    cfg = config.get_config()
    with open(cfg['error_log_file'], 'a') as f:
        f.write(json.dumps({
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'question': question,
            'error': error_message
        }) + '\n')

def log_success(question):
    """Logs the successful question to a JSONL file."""
    cfg = config.get_config()
    with open(cfg['success_log_file'], 'a') as f:
        f.write(json.dumps({'question': question}) + '\n')

def load_successful_questions():
    """Loads the set of successfully processed questions from the log file."""
    cfg = config.get_config()
    if not os.path.exists(cfg['success_log_file']):
        return set()
    with open(cfg['success_log_file'], 'r') as f:
        return set(json.loads(line)['question'] for line in f if line.strip())

def get_run_metadata(base_url, questions_source_type, questions_source_config, 
                     output_destination_type, output_destination_config, debug, endpoint):
    """Return a dict of the key parameters for this run."""
    return {
        'base_url': base_url,
        'questions_source_type': questions_source_type,
        'questions_source_config': questions_source_config,
        'output_destination_type': output_destination_type,
        'output_destination_config': output_destination_config,
        'debug': debug,
        'endpoint': endpoint
    }

def save_run_metadata(meta):
    cfg = config.get_config()
    with open(cfg['success_log_meta_file'], 'w') as f:
        json.dump(meta, f)

def load_run_metadata():
    cfg = config.get_config()
    if not os.path.exists(cfg['success_log_meta_file']):
        return None
    with open(cfg['success_log_meta_file'], 'r') as f:
        return json.load(f)

def create_output_destination(destination_type, destination_config):
    """Create an output destination based on configuration."""
    try:
        if destination_type.lower() == 'json':
            file_path = destination_config.get('file_path', './results.json')
            pretty_print = destination_config.get('pretty_print', True)
            return OutputDestinationFactory.create_destination(
                'json', 
                file_path=file_path, 
                pretty_print=pretty_print
            )
        
        elif destination_type.lower() == 'excel':
            file_path = destination_config.get('file_path', './results.xlsx')
            sheet_name = destination_config.get('sheet_name', 'Results')
            return OutputDestinationFactory.create_destination(
                'excel',
                file_path=file_path,
                sheet_name=sheet_name
            )
        
        elif destination_type.lower() == 'postgresql':
            connection_string = destination_config.get('connection_string')
            table_name = destination_config.get('table_name', 'ai_results')
            create_table = destination_config.get('create_table', True)
            return OutputDestinationFactory.create_destination(
                'postgresql',
                connection_string=connection_string,
                table_name=table_name,
                create_table=create_table
            )
        
        elif destination_type.lower() == 'console':
            format_type = destination_config.get('format_type', 'json')
            detailed = destination_config.get('detailed', True)
            return OutputDestinationFactory.create_destination(
                'console',
                format_type=format_type,
                detailed=detailed
            )
        
        else:
            # Default to console output
            logging.warning(f"Unknown output destination type '{destination_type}', defaulting to console")
            return OutputDestinationFactory.create_destination('console')
            
    except Exception as e:
        logging.error(f"Failed to create output destination '{destination_type}': {e}")
        # Fallback to console
        logging.info("Falling back to console output destination")
        return OutputDestinationFactory.create_destination('console')

def output_data(content, options):
    """Legacy function for backward compatibility with existing outputOptions."""
    output_func = outputOptions.get_output_function(options.get('format', 'raw'))
    output_func(content, options)

def create_question_source(source_type, source_config):
    """Create a question source based on configuration."""
    try:
        if source_type.lower() == 'yaml':
            file_path = source_config.get('file_path', './questions.yml')
            return QuestionSourceFactory.create_source('yaml', file_path=file_path)
        
        elif source_type.lower() == 'dummy':
            custom_questions = source_config.get('questions')
            return QuestionSourceFactory.create_source('dummy', questions=custom_questions)
        
        elif source_type.lower() == 'postgresql':
            connection_string = source_config.get('connection_string')
            table_name = source_config.get('table_name', 'questions')
            question_column = source_config.get('question_column', 'question_text')
            return QuestionSourceFactory.create_source(
                'postgresql',
                connection_string=connection_string,
                table_name=table_name,
                question_column=question_column
            )
        
        else:
            # Default to YAML with specified file path
            file_path = source_config.get('file_path', './questions.yml')
            logging.warning(f"Unknown source type '{source_type}', defaulting to YAML")
            return QuestionSourceFactory.create_source('yaml', file_path=file_path)
            
    except Exception as e:
        logging.error(f"Failed to create question source '{source_type}': {e}")
        # Fallback to dummy source
        logging.info("Falling back to dummy question source")
        return QuestionSourceFactory.create_source('dummy')

def process_questions(base_url, questions_source_type='yaml', questions_source_config=None, 
                     output_destination_type='console', output_destination_config=None, 
                     debug=False, endpoint=None):
    """Main logic for processing questions and outputting results using configurable sources and destinations."""
    cfg = config.get_config()
    if endpoint is None:
        endpoint = cfg['default_endpoint']
    
    if questions_source_config is None:
        questions_source_config = {'file_path': './questions.yml'}
    
    if output_destination_config is None:
        output_destination_config = {'format_type': 'json'}
    
    try:
        # Create question source
        question_source = create_question_source(questions_source_type, questions_source_config)
        
        # Create output destination
        output_destination = create_output_destination(output_destination_type, output_destination_config)
        
        # Create processor with question source
        processor = QuestionProcessor(base_url, endpoint, debug, question_source)
        questions = processor.get_questions_from_source()
        
        # Log source and destination information
        source_info = question_source.get_source_info()
        destination_info = output_destination.get_destination_info()
        logging.info(f"Using question source: {source_info}")
        logging.info(f"Using output destination: {destination_info}")
        
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        return
    except Exception as e:
        logging.error(f"Failed to initialize processor, question source, or output destination: {e}")
        return
    
    # Check run metadata
    current_meta = get_run_metadata(base_url, questions_source_type, questions_source_config, 
                                   output_destination_type, output_destination_config, debug, endpoint)
    previous_meta = load_run_metadata()
    if previous_meta != current_meta:
        # New run parameters, clear logs
        if os.path.exists(cfg['success_log_file']):
            os.remove(cfg['success_log_file'])
        if os.path.exists(cfg['success_log_meta_file']):
            os.remove(cfg['success_log_meta_file'])
        save_run_metadata(current_meta)
        successful_questions = set()
    else:
        successful_questions = load_successful_questions()
    
    results = []
    all_success = True
    
    for question in questions:
        if question in successful_questions:
            continue  # Skip already successful
        
        result = processor.process_question_with_retry(question)
        if result is not None and 'error' not in result:
            results.append(result)
            log_success(question)
        elif result is not None and 'error' in result:
            log_error(question, result['error'])
            all_success = False
        else:
            all_success = False
    
    # Write results using the new output destination interface
    run_metadata = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'total_questions': len(questions),
        'successful_results': len(results),
        'skipped_questions': len(successful_questions),
        'base_url': base_url,
        'questions_source': source_info,
        'debug_mode': debug
    }
    
    success = output_destination.write_results(results, run_metadata)
    if not success:
        logging.error("Failed to write results to output destination")
    
    # If all questions are successful, delete the success log file and meta file
    if all_success and len(successful_questions) + len(results) == len(questions):
        if os.path.exists(cfg['success_log_file']):
            os.remove(cfg['success_log_file'])
        if os.path.exists(cfg['success_log_meta_file']):
            os.remove(cfg['success_log_meta_file'])

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_process_batch_questions(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Azure Function timer trigger started processing questions')
    
    # Get configuration from environment variables
    base_url = os.getenv('AI_TESTER_BASE_URL', 'https://askyalemytest.azurewebsites.net')
    debug = os.getenv('AI_TESTER_DEBUG', 'false').lower() == 'true'
    
    # Question source configuration
    questions_source_type = os.getenv('AI_TESTER_QUESTIONS_SOURCE_TYPE', 'yaml')
    
    # Configure question source based on type
    questions_source_config = {}
    
    if questions_source_type.lower() == 'yaml':
        questions_source_config = {
            'file_path': os.getenv('AI_TESTER_QUESTIONS_FILE', './questions.yml')
        }
    elif questions_source_type.lower() == 'dummy':
        # For dummy source, you can optionally specify custom questions via JSON
        custom_questions_json = os.getenv('AI_TESTER_DUMMY_QUESTIONS')
        if custom_questions_json:
            try:
                questions_source_config = {
                    'questions': json.loads(custom_questions_json)
                }
            except json.JSONDecodeError:
                logging.warning('Invalid JSON in AI_TESTER_DUMMY_QUESTIONS, using default dummy questions')
                questions_source_config = {}
        else:
            questions_source_config = {}
    elif questions_source_type.lower() == 'postgresql':
        questions_source_config = {
            'connection_string': os.getenv('AI_TESTER_POSTGRES_CONNECTION_STRING'),
            'table_name': os.getenv('AI_TESTER_POSTGRES_TABLE', 'questions'),
            'question_column': os.getenv('AI_TESTER_POSTGRES_COLUMN', 'question_text')
        }
        if not questions_source_config['connection_string']:
            logging.error('PostgreSQL connection string not provided, falling back to dummy source')
            questions_source_type = 'dummy'
            questions_source_config = {}
    
    # Output destination configuration
    output_destination_type = os.getenv('AI_TESTER_OUTPUT_DESTINATION_TYPE', 'console')
    
    # Configure output destination based on type
    output_destination_config = {}
    
    if output_destination_type.lower() == 'json':
        output_destination_config = {
            'file_path': os.getenv('AI_TESTER_OUTPUT_FILE', './results.json'),
            'pretty_print': os.getenv('AI_TESTER_JSON_PRETTY_PRINT', 'true').lower() == 'true'
        }
    elif output_destination_type.lower() == 'excel':
        output_destination_config = {
            'file_path': os.getenv('AI_TESTER_OUTPUT_FILE', './results.xlsx'),
            'sheet_name': os.getenv('AI_TESTER_EXCEL_SHEET_NAME', 'Results')
        }
    elif output_destination_type.lower() == 'postgresql':
        output_destination_config = {
            'connection_string': os.getenv('AI_TESTER_OUTPUT_POSTGRES_CONNECTION_STRING'),
            'table_name': os.getenv('AI_TESTER_OUTPUT_POSTGRES_TABLE', 'ai_results'),
            'create_table': os.getenv('AI_TESTER_OUTPUT_POSTGRES_CREATE_TABLE', 'true').lower() == 'true'
        }
        if not output_destination_config['connection_string']:
            logging.error('PostgreSQL output connection string not provided, falling back to console output')
            output_destination_type = 'console'
            output_destination_config = {}
    elif output_destination_type.lower() == 'console':
        output_destination_config = {
            'format_type': os.getenv('AI_TESTER_CONSOLE_FORMAT', 'json'),
            'detailed': os.getenv('AI_TESTER_CONSOLE_DETAILED', 'true').lower() == 'true'
        }
    
    logging.info(f'Using question source: {questions_source_type}')
    logging.info(f'Using output destination: {output_destination_type}')
    
    try:
        process_questions(
            base_url=base_url,
            questions_source_type=questions_source_type,
            questions_source_config=questions_source_config,
            output_destination_type=output_destination_type,
            output_destination_config=output_destination_config,
            debug=debug
        )
        logging.info('Question processing completed successfully')
    except Exception as e:
        logging.error(f'Question processing failed: {e}')
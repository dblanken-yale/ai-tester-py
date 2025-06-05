import json
import argparse
import outputOptions
import time
import os
import logging
from processor import QuestionProcessor, ValidationError
import config



def get_questions(filename):
    """Reads the questions from a file."""
    processor = QuestionProcessor('dummy')
    return processor.get_questions_from_file(filename)






def output_data(content, options):
    """Outputs the data in the desired format using the output registry."""
    output_func = outputOptions.get_output_function(options.get('format', 'raw'))
    output_func(content, options)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Process some questions.')
    parser.add_argument('base_url', type=str, nargs='?', help='The base URL to send the questions to')
    parser.add_argument('--questions', type=str, help='Path to the questions file (default: ./questions.yml)', default='./questions.yml')
    parser.add_argument('--format', type=str, choices=['json', 'excel'], default='json', help='The format of the output')
    parser.add_argument('--outfile', type=str, help='The name of the output file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    if not args.base_url:
        parser.error("The base_url argument is required. Usage: python test-questions.py <base_url>")
    return args


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


def get_run_metadata(base_url, questions_file, output_format, filename, debug, endpoint):
    """Return a dict of the key parameters for this run."""
    return {
        'base_url': base_url,
        'questions_file': os.path.abspath(questions_file),
        'output_format': output_format,
        'filename': filename,
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




def run(base_url, questions_file, output_format, filename=None, debug=False, endpoint=None):
    """Main logic for processing questions and outputting results. Skips already successful questions.
    If all questions are successful, deletes the success log file and meta file.
    If run parameters change, deletes old log and meta file."""
    cfg = config.get_config()
    if endpoint is None:
        endpoint = cfg['default_endpoint']
    
    options = {
        'format': output_format,
        'filename': filename
    }
    
    try:
        processor = QuestionProcessor(base_url, endpoint, debug)
        questions = processor.get_questions_from_file(questions_file)
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        return
    except Exception as e:
        logging.error(f"Failed to initialize processor: {e}")
        return
    
    # Check run metadata
    current_meta = get_run_metadata(base_url, questions_file, output_format, filename, debug, endpoint)
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
    
    output_data(results, options)
    
    # If all questions are successful, delete the success log file and meta file
    if all_success and len(successful_questions) + len(results) == len(questions):
        if os.path.exists(cfg['success_log_file']):
            os.remove(cfg['success_log_file'])
        if os.path.exists(cfg['success_log_meta_file']):
            os.remove(cfg['success_log_meta_file'])


def main():
    """Entry point for CLI usage."""
    args = parse_args()
    run(
        base_url=args.base_url,
        questions_file=args.questions,
        output_format=args.format,
        filename=args.outfile,
        debug=args.debug
    )


if __name__ == '__main__':
    main()

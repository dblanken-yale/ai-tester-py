import uuid
import requests
import yaml
import json
import argparse
from datetime import datetime, timezone
import outputOptions
import time
import os

ERROR_LOG_FILE = '.error_log.jsonl'
SUCCESS_LOG_FILE = '.success_log.jsonl'
SUCCESS_LOG_META_FILE = '.success_log.meta.json'


def get_questions(filename):
    """Reads the questions from a file."""
    with open(filename, 'r') as file:
        return yaml.safe_load(file)


def fetch_data(url, payload):
    """Fetches the data from the URL."""
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.content


def fetch_data_with_retry(url, payload, question, max_retries=3, delay=2):
    """Fetches the data from the URL with retry logic. Logs errors if all retries fail."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.content
        except Exception as e:
            if attempt == max_retries:
                log_error(question, str(e))
                return None
            time.sleep(delay)


def create_payload(question):
    """Creates the payload for the question."""
    payload_template = {
        "role": "user",
    }
    return {
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "date": datetime.now(timezone.utc).isoformat(),
                "content": question,
                **payload_template,
            },
        ],
    }


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
    with open(ERROR_LOG_FILE, 'a') as f:
        f.write(json.dumps({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'question': question,
            'error': error_message
        }) + '\n')


def log_success(question):
    """Logs the successful question to a JSONL file."""
    with open(SUCCESS_LOG_FILE, 'a') as f:
        f.write(json.dumps({'question': question}) + '\n')


def load_successful_questions():
    """Loads the set of successfully processed questions from the log file."""
    if not os.path.exists(SUCCESS_LOG_FILE):
        return set()
    with open(SUCCESS_LOG_FILE, 'r') as f:
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
    with open(SUCCESS_LOG_META_FILE, 'w') as f:
        json.dump(meta, f)


def load_run_metadata():
    if not os.path.exists(SUCCESS_LOG_META_FILE):
        return None
    with open(SUCCESS_LOG_META_FILE, 'r') as f:
        return json.load(f)


def process_question(question, url, debug=False):
    """Process a single question and return the result dict, or None if failed."""
    payload = create_payload(question)
    buffer = fetch_data_with_retry(url, payload, question)
    if buffer is None:
        return None
    content = buffer.decode('utf-8')
    json_content_array = [
        json.loads(line) for line in content.split('\n')
        if line.strip() and line.strip() != '{}'
    ]
    joined_choice_messages = [
        ''.join(line_obj['content'] for line_obj in json_line['choices'][0]['messages'])
        for json_line in json_content_array if json_line['choices']
    ]
    citations = [citation['url'] for citation in json.loads(joined_choice_messages[0])['citations']]
    citations_contents = []
    if debug:
        citations_contents = [
            citation['content'] for citation in json.loads(joined_choice_messages[0])['citations']
        ]
    messages = ''.join(joined_choice_messages[1:])
    json_output = {
        "citations": citations,
        "answer": messages,
        "question": question
    }
    if debug:
        json_output["citationsContents"] = citations_contents
    return json_output


def run(base_url, questions_file, output_format, filename=None, debug=False, endpoint='/conversation'):
    """Main logic for processing questions and outputting results. Skips already successful questions.
    If all questions are successful, deletes the success log file and meta file.
    If run parameters change, deletes old log and meta file."""
    options = {
        'format': output_format,
        'filename': filename
    }
    url = base_url + endpoint
    results = []
    questions = get_questions(questions_file)
    # Check run metadata
    current_meta = get_run_metadata(base_url, questions_file, output_format, filename, debug, endpoint)
    previous_meta = load_run_metadata()
    if previous_meta != current_meta:
        # New run parameters, clear logs
        if os.path.exists(SUCCESS_LOG_FILE):
            os.remove(SUCCESS_LOG_FILE)
        if os.path.exists(SUCCESS_LOG_META_FILE):
            os.remove(SUCCESS_LOG_META_FILE)
        save_run_metadata(current_meta)
        successful_questions = set()
    else:
        successful_questions = load_successful_questions()
    all_success = True
    for question in questions:
        if question in successful_questions:
            continue  # Skip already successful
        result = process_question(question, url, debug=debug)
        if result is not None:
            results.append(result)
            log_success(question)
        else:
            all_success = False
    output_data(results, options)
    # If all questions are successful, delete the success log file and meta file
    if all_success and len(successful_questions) + len(results) == len(questions):
        if os.path.exists(SUCCESS_LOG_FILE):
            os.remove(SUCCESS_LOG_FILE)
        if os.path.exists(SUCCESS_LOG_META_FILE):
            os.remove(SUCCESS_LOG_META_FILE)


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

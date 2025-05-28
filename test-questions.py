import uuid
import requests
import yaml
import json
import argparse
from datetime import datetime, timezone
import outputOptions


def get_questions(filename):
    """Reads the questions from a file."""
    with open(filename, 'r') as file:
        return yaml.safe_load(file)


def fetch_data(url, payload):
    """Fetches the data from the URL."""
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.content


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


def process_question(question, url, debug=False):
    """Process a single question and return the result dict."""
    payload = create_payload(question)
    buffer = fetch_data(url, payload)
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
    """Main logic for processing questions and outputting results."""
    options = {
        'format': output_format,
        'filename': filename
    }
    url = base_url + endpoint
    results = []
    questions = get_questions(questions_file)
    for question in questions:
        result = process_question(question, url, debug=debug)
        results.append(result)
    output_data(results, options)


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

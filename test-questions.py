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

def outputData(content, options):
    """Outputs the data in the desired format."""

    outputFormat = outputOptions.toRaw
    match options['format']:
        case 'json':
            outputFormat = outputOptions.toJSON
        case 'excel':
            outputFormat = outputOptions.toExcel

    outputFormat(content, options)

def main():
    parser = argparse.ArgumentParser(description='Process some questions.')
    parser.add_argument('base_url', type=str, nargs='?', help='The base URL to send the questions to')
    parser.add_argument('--format', type=str, choices=['json', 'excel'], default='json', help='The format of the output')
    parser.add_argument('--outfile', type=str, help='The name of the output file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    if not args.base_url:
        parser.error("The base_url argument is required. Usage: python test-questions.py <base_url>")

    base_url = args.base_url
    format = args.format if args.format else 'json'
    filename = args.outfile if args.outfile else None
    debug = args.debug if args.debug else False
    options = {
        'format': format,
        'filename': filename
    }
    conversation_endpoint = '/conversation'
    url = base_url + conversation_endpoint
    results = []

    questions = get_questions('./questions.yml')

    for question in questions:
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
        citationsContents = []
        if debug:
            citationsContents = [
                citation['content'] for citation in json.loads(joined_choice_messages[0])['citations']
            ]

        messages = ''.join(joined_choice_messages[1:])

        json_output = {
            "citations": citations,
            "answer": messages,
            "question": question
        }

        if debug:
            json_output = {
                "citationsContents": citationsContents,
                "citations": citations,
                "answer": messages,
                "question": question
            }
        results.append(json_output)

    outputData(results, options)

if __name__ == '__main__':
    main()

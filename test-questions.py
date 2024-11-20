import uuid
import requests
import yaml
import json
import argparse
from datetime import datetime

def get_questions(filename):
    with open(filename, 'r') as file:
        return yaml.safe_load(file)

def fetch_data(url, payload):
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.content

def create_payload(question):
    payload_template = {
        "role": "user",
    }
    return {
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "date": datetime.utcnow().isoformat() + 'Z',
                "content": question,
                **payload_template,
            },
        ],
    }

def main():
    parser = argparse.ArgumentParser(description='Process some questions.')
    parser.add_argument('base_url', type=str, nargs='?', help='The base URL to send the questions to')
    args = parser.parse_args()

    if not args.base_url:
        parser.error("The base_url argument is required. Usage: python test-questions.py <base_url>")

    base_url = args.base_url
    conversation_endpoint = '/conversation'
    url = base_url + conversation_endpoint

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

        citations = [citation['content'] for citation in json.loads(joined_choice_messages[0])['citations']]
        messages = ''.join(joined_choice_messages[1:])

        json_output = {
            "citations": citations,
            "answer": messages,
            "question": question
        }
        print(json.dumps(json_output, indent=2))

if __name__ == '__main__':
    main()

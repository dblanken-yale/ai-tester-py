# AI Tester

## What is this?

This is a small python script to send multiple questions to an AI endpoint and attempt to retrieve the responses for review.

## How to install?

- Clone the repository locally
- Inside of the directory, run `./install.sh`
- Make any modifications to questions inside of the [questions.yml](https://github.com/dblanken-yale/ai-tester-py/blob/main/questions.yml) file
- Run the script: `python test-questions.py <url>`
- To capture the output, run `python test-questions.py <url> > output.json`
  - Where `<url>` is the endpoint to test against
- Usage can be seen by running `python test-questions.py -h`

## Can I output to different formats?

Yes, here is how:

### JSON

```bash
python test-questions.py <url> > output.json
```

### JSON to file

```bash
python test-questions.py <url> --outfile output.json
```

### Excel to file

```bash
python test-questions.py <url> --format excel --outfile output.xlsx
```

## I found an issue or want to know more

You can enable debug mode to see more information; currently you'll be able to see this only in raw JSON output, and it currently supports showing all citation data.

```bash
python test-questions.py <url> --debug
```

## How does it work?

This will attempt to hit an endpoint with a multitude of questions stored inside of the questions.yml file, and output the question, citations, and response into a readable output.

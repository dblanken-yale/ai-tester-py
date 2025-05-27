# AI Tester

AI Tester is a tool for automating the testing of AI endpoints using configurable question sets and exporting results to various formats, including Excel.

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

## I'd like to run a lot of different sets of questions

You can do this by running an included bash script:

```bash
./run_dir.sh <name_of_folder_with_yaml_files> <url>
```

This will create a new directory named `<name_of_folder_with_yaml_files>_output`.  For instance, if you passed in a directory of `iyy`, it'd create `iyy_output`.

It would then create new files matching the yaml filenames but with an `.xlsx` extension in that directory.

## I'd like to specify my own questions

You don't have to use questions.yml, you can specify your own questions file by using the `--questions` flag:

```bash
python test-questions.py <url> --questions my_questions.yml
```

The above will use your own questions file instead of the default `questions.yml`.

## How does it work?

This will attempt to hit an endpoint with a multitude of questions stored inside of the questions.yml file, and output the question, citations, and response into a readable output.

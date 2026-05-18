# AI Tester

## What is this?

This is a small Python tool that sends a list of questions to an AI service and collects the responses — including any source citations — for review.

## Prerequisites

Before you begin, you need the following installed on your computer:

- **Python 3.8 or higher** — [Download Python](https://www.python.org/downloads/)
- **Git** — [Download Git](https://git-scm.com/downloads/)

If you are unsure whether these are installed, open a terminal and run:

```
python --version
git --version
```

Both commands should print a version number. If you see an error, install the missing tool first.

## How to install?

1. **Download the project.** In your terminal, run:

   ```bash
   git clone https://github.com/dblanken-yale/ai-tester-py.git
   cd ai-tester-py
   ```

2. **Install dependencies.** This installs the Python libraries the tool needs:

   ```bash
   ./install.sh
   ```

3. **Add your questions.** Open `questions.yml` in any text editor (Notepad on Windows, TextEdit on Mac, or VS Code) and replace the example questions with your own. Each question goes on its own line starting with a dash and a space (`- `).

4. **Run the tool.** Replace `<url>` with the address of the AI service you are testing:

   ```bash
   python test-questions.py <url>
   ```

   The tool will print results to your screen. See the sections below to save them to a file.

> **What is the URL?** This is the web address of the AI service you want to test. It is typically provided by your team or the service documentation and should start with `https://`.

All available options can be seen by running:

```bash
python test-questions.py -h
```

## Saving your results

By default the tool prints results to your screen. To save them to a file, use one of the options below.

### JSON (printed to screen, redirected to a file)

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

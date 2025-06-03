#!/usr/bin/env bash
# install.sh - Script to set up the environment for ai-tester-py
# Exits on any error
set -e

print_green() {
  local GREEN='\033[0;32m'
  local NC='\033[0m' # No Color
  echo -e "${GREEN}$1${NC}"
}

# Check for pip
if ! command -v pip &> /dev/null; then
  echo "pip could not be found. Please install Python and pip first."
  exit 1
fi

# Check for requirements.txt
if [ ! -f requirements.txt ]; then
  echo "requirements.txt not found in the current directory."
  exit 1
fi

print_green "Installing dependencies via pip"
echo ""
pip install -r requirements.txt || { echo 'pip install failed'; exit 1; }

echo ""
print_green "Modify the \`questions.yml\` with questions you'd like to ask."
print_green "These should be of the following format:"
print_green "- Question 1"
print_green "- Question 2"
echo ""
print_green "If you need multiline questions, you can use the following way:"
print_green "- |"
print_green "  A very long question with newlines and the like."
print_green "  Keep going."
print_green "- Question 2"
echo ""
print_green "Then run \`python test-questions.py <url>\`"
echo ""
print_green "If you ever have issues remembering what to do, you can run this installer again or \`python test-questions.py -h\`"

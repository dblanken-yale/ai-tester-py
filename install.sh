#!/usr/bin/env bash

print_green() {
  local GREEN='\033[0;32m'
  local NC='\033[0m' # No Color
  echo -e "${GREEN}$1${NC}"
}

print_green "Installing dependencies via pip"
echo ""
pip install -r requirements.txt

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

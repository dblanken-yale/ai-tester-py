#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage: $0 <directory> <url> [other_python_args]"
  exit 1
}

check_directories() {
  local dir="$1"
  local dir_output="$2"
  if [ ! -d "$dir" ]; then
    echo "Directory $dir does not exist."
    exit 1
  fi
  if [ ! -d "$dir_output" ]; then
    echo "Creating $dir_output"
    mkdir "$dir_output"
  fi
}

process_file() {
  local yml_file="$1"
  local dir_output="$2"
  shift 2
  local base_name
  base_name="$(basename "${yml_file%.yml}.xlsx")"
  local xlsx_file="$dir_output/$base_name"

  echo "Processing $yml_file"
  python ./test-questions.py --question "$yml_file" "$@" --format excel --outfile "$xlsx_file"
}

main() {
  if [ $# -lt 2 ]; then
    usage
  fi
  local dir="$1"
  shift
  local dir_output="${dir}_output"
  local args=("$@")

  check_directories "$dir" "$dir_output"

  find "$dir" -type f -name '*.yml' -print0 | while IFS= read -r -d '' yml_file; do
    process_file "$yml_file" "$dir_output" "${args[@]}"
  done
}

main "$@"

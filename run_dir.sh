#!/bin/bash
set -euo pipefail

# Get log file paths from config
get_config_value() {
  python3 -c "import config; cfg = config.get_config(); print(cfg['$1'])"
}

SUCCESS_LOG_FILE=$(get_config_value "run_dir_success_log_file")
SUCCESS_LOG_META_FILE=$(get_config_value "run_dir_success_log_meta_file")
ERROR_LOG_FILE=$(get_config_value "run_dir_error_log_file")

usage() {
  echo "Usage: $0 <directory> <url> [other_python_args]"
  exit 1
}

get_run_metadata() {
  local dir="$1"
  local url="$2"
  shift 2
  local args=("$@")
  local args_str="${args[*]:-}"
  jq -n --arg dir "$(cd "$dir" && pwd)" --arg url "$url" --arg args "$args_str" '{dir: $dir, url: $url, args: $args}'
}

save_run_metadata() {
  local meta_json="$1"
  echo "$meta_json" > "$SUCCESS_LOG_META_FILE"
}

load_run_metadata() {
  [ -f "$SUCCESS_LOG_META_FILE" ] && cat "$SUCCESS_LOG_META_FILE" || echo ""
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

log_success() {
  local yml_file="$1"
  printf '{"yml_file": "%s"}\n' "$yml_file" >> "$SUCCESS_LOG_FILE"
}

log_error() {
  local yml_file="$1"
  local error_msg="$2"
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  printf '{"timestamp": "%s", "yml_file": "%s", "error": "%s"}\n' "$timestamp" "$yml_file" "$error_msg" >> "$ERROR_LOG_FILE"
}

load_successful_files() {
  [ ! -f "$SUCCESS_LOG_FILE" ] && return
  jq -r '.yml_file' "$SUCCESS_LOG_FILE"
}

process_file() {
  local yml_file="$1"
  local dir_output="$2"
  shift 2
  local base_name
  base_name="$(basename "${yml_file%.yml}.xlsx")"
  local xlsx_file="$dir_output/$base_name"
  local retries=0
  local max_retries=3
  local success=0
  while [ $retries -lt $max_retries ]; do
    echo "Processing $yml_file (attempt $((retries+1))/$max_retries)"
    if python ./test-questions.py --questions "$yml_file" "$@" --format excel --outfile "$xlsx_file"; then
      log_success "$yml_file"
      success=1
      break
    else
      log_error "$yml_file" "Python script failed on attempt $((retries+1))"
      retries=$((retries+1))
      sleep 2
    fi
  done
  [ $success -eq 0 ] && echo "Failed to process $yml_file after $max_retries attempts."
}

main() {
  if [ $# -lt 2 ]; then
    usage
  fi
  local dir="$1"
  shift
  local url="$1"
  shift
  local dir_output="${dir}_output"
  local args=("$url" "$@")

  check_directories "$dir" "$dir_output"

  # Compute and check run metadata
  local current_meta previous_meta
  current_meta=$(get_run_metadata "$dir" "$url" "$@")
  previous_meta=$(load_run_metadata)
  if [ "$current_meta" != "$previous_meta" ]; then
    rm -f "$SUCCESS_LOG_FILE" "$SUCCESS_LOG_META_FILE"
    save_run_metadata "$current_meta"
  fi

  # Load successful files into an array (portable, no mapfile)
  local successful_files=()
  while IFS= read -r sfile || [ -n "$sfile" ]; do
    [ -n "$sfile" ] && successful_files+=("$sfile")
  done < <(load_successful_files)

  find "$dir" -type f -name '*.yml' -print0 | while IFS= read -r -d '' yml_file; do
    local skip=0
    if [ ${#successful_files[@]:-0} -gt 0 ]; then
      for sfile in "${successful_files[@]}"; do
        if [ "$yml_file" = "$sfile" ]; then
          skip=1
          break
        fi
      done
    fi
    [ $skip -eq 1 ] && { echo "Skipping already successful: $yml_file"; continue; }
    process_file "$yml_file" "$dir_output" "${args[@]}"
  done

  # If all files were successful, delete the logs
  local total_files success_count
  total_files=$(find "$dir" -type f -name '*.yml' | wc -l)
  success_count=$(wc -l < "$SUCCESS_LOG_FILE" 2>/dev/null || echo 0)
  if [ "$total_files" -eq "$success_count" ]; then
    rm -f "$SUCCESS_LOG_FILE" "$SUCCESS_LOG_META_FILE"
  fi
}

main "$@"

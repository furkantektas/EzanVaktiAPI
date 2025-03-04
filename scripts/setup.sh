#!/usr/bin/env bash

# Script to download, validate, and transform data with retries
# Usage: ./download-data.sh [--attempts N] [--delay S] [--verbose]

set -eo pipefail

# Configure default variables
MAX_ATTEMPTS=5
RETRY_DELAY=60  # in seconds
VERBOSE=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/download-data.log"

# Terminal colors (only if terminal supports it)
if [[ -t 1 ]] && [[ "$(tput colors 2>/dev/null || echo 0)" -gt 0 ]]; then
  GREEN=$(tput setaf 2)
  RED=$(tput setaf 1)
  YELLOW=$(tput setaf 3)
  RESET=$(tput sgr0)
else
  GREEN=""
  RED=""
  YELLOW=""
  RESET=""
fi

# Process command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --attempts) MAX_ATTEMPTS="$2"; shift 2 ;;
    --delay) RETRY_DELAY="$2"; shift 2 ;;
    --verbose) VERBOSE=1; shift ;;
    --help) echo "Usage: $0 [--attempts N] [--delay S] [--verbose]"; exit 0 ;;
    *) echo "Unknown parameter: $1"; exit 1 ;;
  esac
done

# Logging functions
log() {
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  echo "${timestamp} - $1"
  echo "${timestamp} - $1" >> "${LOG_FILE}"
}

log_success() {
  log "${GREEN}✅ $1${RESET}"
}

log_error() {
  log "${RED}❌ $1${RESET}"
}

log_warning() {
  log "${YELLOW}⚠️  $1${RESET}"
}

# Check for required commands
check_requirements() {
  if ! command -v uv &> /dev/null; then
    log_error "uv is not installed or not in PATH"
    exit 1
  fi
}

# Function to run download and validation with retries
run_with_retries() {
  local attempt=1
  local success=false

  while [ $attempt -le $MAX_ATTEMPTS ]; do
    log "Attempt $attempt of $MAX_ATTEMPTS"

    log "Running download script..."
    if ! uv run "${SCRIPT_DIR}/download.py"; then
      log_error "Download script failed"

      if [ $attempt -lt $MAX_ATTEMPTS ]; then
        log_warning "Waiting $RETRY_DELAY seconds before retrying..."
        sleep $RETRY_DELAY
        attempt=$((attempt+1))
        continue
      else
        return 1
      fi
    fi

    log "Running validation script..."
    if uv run "${SCRIPT_DIR}/validate.py"; then
      log_success "Validation successful!"
      success=true
      break
    else
      log_error "Validation failed"

      if [ $attempt -lt $MAX_ATTEMPTS ]; then
        log_warning "Waiting $RETRY_DELAY seconds before retrying..."
        sleep $RETRY_DELAY
      fi
    fi

    attempt=$((attempt+1))
  done

  if [ "$success" = true ]; then
    return 0
  else
    log_error "Maximum attempts reached. Failed to validate data after $MAX_ATTEMPTS attempts."
    return 1
  fi
}

# Cleanup function
cleanup() {
  EXIT_CODE=$?
  if [ $EXIT_CODE -ne 0 ]; then
    log_error "Script execution interrupted or failed with exit code $EXIT_CODE"
  fi
  exit $EXIT_CODE
}

# Set trap for clean exit
trap cleanup EXIT INT TERM

# Main execution
main() {
  log "Starting data update process..."

  # Ensure we're in the correct directory
  cd "${SCRIPT_DIR}" || { log_error "Failed to change directory to ${SCRIPT_DIR}"; exit 1; }

  # Check requirements
  check_requirements

  if run_with_retries; then
    log "Running transformation script..."
    if uv run "${SCRIPT_DIR}/transform.py"; then
      log_success "Data transformation completed successfully!"
      return 0
    else
      log_error "Transformation script failed"
      return 1
    fi
  else
    log_error "Data update process failed"
    return 1
  fi
}

# Execute main function
main
exit $?

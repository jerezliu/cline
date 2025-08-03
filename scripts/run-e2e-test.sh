#!/bin/bash

# Default values
WORKSPACE=""
TASK=""
API_KEY=""
PLAN_ACT_SCRIPT_PATH="$HOME/GitHub/cline/evals/cli/dist/run-plan-act-test.js"
WAIT_SECONDS=15
BLIND_APPROVAL_WAIT_SECONDS=""
TIMEOUT_MINUTES=""

# Function to display usage
usage() {
    echo "Usage: $0 --workspace <path> --task <description> --api-key <key> [--script-path <path>] [--wait-seconds <seconds>] [--blind-approval-wait-seconds <seconds>] [--timeout-minutes <minutes>]"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -w|--workspace) WORKSPACE="$2"; shift ;;
        -t|--task) TASK="$2"; shift ;;
        -k|--api-key) API_KEY="$2"; shift ;;
        -p|--script-path) PLAN_ACT_SCRIPT_PATH="$2"; shift ;;
        -s|--wait-seconds) WAIT_SECONDS="$2"; shift ;;
        --blind-approval-wait-seconds) BLIND_APPROVAL_WAIT_SECONDS="$2"; shift ;;
        --timeout-minutes) TIMEOUT_MINUTES="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Validate required arguments
if [ -z "$WORKSPACE" ] || [ -z "$TASK" ] || [ -z "$API_KEY" ]; then
    echo "Error: Missing required arguments."
    usage
fi

# Absolute path for the workspace
if [[ "$WORKSPACE" != /* ]]; then
    WORKSPACE="$(pwd)/$WORKSPACE"
fi

echo "Starting VS Code for workspace: $WORKSPACE"
# Launch VS Code in the background
code "$WORKSPACE" &
CODE_PID=$!

# Wait for VS Code and the server to initialize
echo "Waiting for $WAIT_SECONDS seconds for server to initialize..."
sleep "$WAIT_SECONDS"

echo "Running the Plan/Act test script..."
# Build the command with optional arguments
CMD_ARGS=("--task" "$TASK" "--api-key" "$API_KEY" "--workspace" "$WORKSPACE")
if [ -n "$BLIND_APPROVAL_WAIT_SECONDS" ]; then
    CMD_ARGS+=("--blind-approval-wait-seconds" "$BLIND_APPROVAL_WAIT_SECONDS")
fi
if [ -n "$TIMEOUT_MINUTES" ]; then
    CMD_ARGS+=("--timeout-minutes" "$TIMEOUT_MINUTES")
fi

# Run the client script
"$PLAN_ACT_SCRIPT_PATH" "${CMD_ARGS[@]}"
SCRIPT_EXIT_CODE=$?

echo "Shutting down VS Code..."
# Kill the VS Code process
kill $CODE_PID

# Wait for the process to be killed
wait $CODE_PID 2>/dev/null

echo "Test finished with exit code: $SCRIPT_EXIT_CODE"
exit $SCRIPT_EXIT_CODE

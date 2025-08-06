#!/bin/bash

# Default values
WORKSPACE=""
TASK=""
API_KEY=""
PLAN_ACT_SCRIPT_PATH="$HOME/GitHub/cline/evals/cli/dist/run-plan-act-test.js"
START_HEADLESS_SESSION_SCRIPT_PATH="$HOME/GitHub/cline/scripts/start-headless-session.py"
WAIT_SECONDS="10"
BLIND_APPROVAL_WAIT_SECONDS="15"
TIMEOUT_MINUTES="15"
CODE_SERVER_PORT=8080
RECORD=false

# Function to display usage
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Runs an end-to-end test in a headless environment."
    echo ""
    echo "Options:"
    echo "  -w, --workspace <path>          Required. Path to the workspace to be tested."
    echo "  -t, --task <description>        Required. The task description for the AI."
    echo "  -k, --api-key <key>             Required. The API key for the AI service."
    echo "  -p, --script-path <path>        Optional. Path to the Plan/Act test script. Defaults to '$PLAN_ACT_SCRIPT_PATH'."
    echo "  -s, --wait-seconds <seconds>    Optional. Seconds to wait for servers to initialize. Defaults to $WAIT_SECONDS."
    echo "  --blind-approval-wait-seconds <seconds> Optional. Time to wait before automatically approving tool usage."
    echo "  --timeout-minutes <minutes>     Optional. Hard timeout for the entire test run. Defaults to $TIMEOUT_MINUTES minutes."
    echo "  --record                        Optional. Enable video recording of the session."
    echo "  -h, --help                      Display this help message."
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
        --record) RECORD=true ;;
        -h|--help) usage ;;
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

# Cleanup function to be called on exit
cleanup() {
    echo "Cleaning up..."
    # Kill code-server and record-session.py
    if [ -n "$CODE_SERVER_PID" ]; then
        kill $CODE_SERVER_PID
        wait $CODE_SERVER_PID 2>/dev/null
    fi
    if [ -n "$RECORDER_PID" ]; then
        kill $RECORDER_PID
        wait $RECORDER_PID 2>/dev/null
    fi
    # Deactivate virtual environment if it's active
    if type deactivate &>/dev/null; then
        deactivate
    fi
    # Optional: remove venv
    # rm -rf venv
    echo "Cleanup finished."
}

# Set trap to call cleanup function on script exit
trap cleanup EXIT

# ----------------------------
# Step 1. Start vscode server.
# ----------------------------
echo "Starting code-server for workspace: $WORKSPACE"
# Launch code-server in the background
code-server --disable-workspace-trust --auth none --port $CODE_SERVER_PORT "$WORKSPACE" &
CODE_SERVER_PID=$!

# Wait for code-server to initialize
echo "Waiting for $WAIT_SECONDS seconds for server to initialize..."
sleep "$WAIT_SECONDS"

# -------------------------------------------------------------------------------------
# Step 2. Run START_HEADLESS_SESSION_SCRIPT to start cline client session via headless browser.
# -------------------------------------------------------------------------------------

# Setup and run start-headless-session.py
echo "Setting up Python virtual environment..."
virtualenv venv
source venv/bin/activate
pip install playwright
playwright install chromium

echo "Starting session recorder..."
RECORDER_CMD="python $START_HEADLESS_SESSION_SCRIPT_PATH --url http://127.0.0.1:$CODE_SERVER_PORT --dir $WORKSPACE"
if [ "$RECORD" = true ]; then
    RECORDER_CMD="$RECORDER_CMD --record"
fi
$RECORDER_CMD &
RECORDER_PID=$!

# Wait for vscode & cline to initialize
echo "Waiting for $WAIT_SECONDS seconds for vscode cline to initialize..."
sleep "$WAIT_SECONDS"

# ---------------------------------------------------
# Step 3. Run script to invoke cline to execute task.
# ---------------------------------------------------
echo "Running the Plan/Act test script..."
# Build the command with optional arguments
CMD_ARGS=("--task" "$TASK" "--api-key" "$API_KEY" "--workspace" "$WORKSPACE")
if [ -n "$BLIND_APPROVAL_WAIT_SECONDS" ]; then
    echo "Setting blind yes-botton click time interval to $BLIND_APPROVAL_WAIT_SECONDS seconds..."
    CMD_ARGS+=("--blind-approval-wait-seconds" "$BLIND_APPROVAL_WAIT_SECONDS")
fi
if [ -n "$TIMEOUT_MINUTES" ]; then
    echo "Setting hard timeout to $TIMEOUT_MINUTES minutes..."
    CMD_ARGS+=("--timeout-minutes" "$TIMEOUT_MINUTES")
fi

# Run the client script
START_TIME=$(date +%s)
"$PLAN_ACT_SCRIPT_PATH" "${CMD_ARGS[@]}"
SCRIPT_EXIT_CODE=$?
END_TIME=$(date +%s)

RUNTIME=$((END_TIME - START_TIME))
echo "Test script finished in $RUNTIME seconds."

# Final cleanup.
echo "Test finished with exit code: $SCRIPT_EXIT_CODE"
exit $SCRIPT_EXIT_CODE

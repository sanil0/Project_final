#!/bin/bash
set -e

# Function to wait for dependencies
wait_for_dependencies() {
    # Add dependency checks here if needed
    # Example: Wait for database
    echo "Checking dependencies..."
}

# Function to initialize configuration
init_config() {
    if [ ! -f "/app/config/config.yaml" ]; then
        echo "Initializing default configuration..."
        cp /app/config/config.yaml.template /app/config/config.yaml
    fi
}

# Function to validate ML models
validate_models() {
    echo "Validating ML models..."
    if [ ! -f "/app/models/ddos_model.joblib" ]; then
        echo "Error: Required ML model not found!"
        exit 1
    fi
}

# Function to setup logging
setup_logging() {
    # Ensure log directory exists and is writable
    mkdir -p /app/logs
    
    # Configure log rotation
    if [ ! -f "/etc/logrotate.d/ddos-protection" ]; then
        cat > /etc/logrotate.d/ddos-protection << EOF
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 appuser appuser
}
EOF
    fi
}

# Function to adjust workers based on CPU
adjust_workers() {
    CPU_CORES=$(nproc)
    if [ "$WORKERS" = "auto" ]; then
        WORKERS=$((CPU_CORES * 2))
        if [ "$WORKERS" -gt "$MAX_WORKERS" ]; then
            WORKERS=$MAX_WORKERS
        fi
    fi
    export WORKERS
}

# Main initialization
echo "Initializing DDoS Protection Service..."

# Perform initialization steps
wait_for_dependencies
init_config
validate_models
setup_logging
adjust_workers

# Print service information
echo "Service Configuration:"
echo "- Workers: $WORKERS"
echo "- Worker Class: $WORKER_CLASS"
echo "- Timeout: $TIMEOUT"
echo "- Max Requests: $MAX_REQUESTS"
echo "- Log Level: $LOG_LEVEL"

# Execute command
echo "Starting service..."
exec "$@"
#!/bin/bash

#
# Load Generator for Chaos Engineering Experiments (Port-Forward Version)
#
# This script continuously sends requests to the client service
# to observe system behavior during chaos experiments.
#
# Prerequisites:
#   In a separate terminal, run:
#   kubectl port-forward service/client-service 8080:8080
#
# Usage:
#   ./load_generator.sh [interval] [duration]
#
# Arguments:
#   interval - Time between requests in seconds (default: 1)
#   duration - Total duration in seconds (default: infinite)
#

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
INTERVAL=${1:-1}          # Default: 1 second between requests
DURATION=${2:-0}          # Default: 0 (infinite)
REQUEST_COUNT=0
SUCCESS_COUNT=0
FAILURE_COUNT=0
FAST_FAIL_COUNT=0
START_TIME=$(date +%s)

# Use localhost via port-forward
CLIENT_URL="http://localhost:8080"

# Print header
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}           CHAOS ENGINEERING LOAD GENERATOR            ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check if port-forward is running
echo -e "${YELLOW}Checking connection to client service...${NC}"
if curl -s -f -m 2 "$CLIENT_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Client service is accessible at: ${CLIENT_URL}${NC}"
else
    echo -e "${RED}✗ Cannot connect to client service at ${CLIENT_URL}${NC}"
    echo -e "${YELLOW}⚠  Please make sure port-forward is running in another terminal:${NC}"
    echo -e "${CYAN}   kubectl port-forward service/client-service 8080:8080${NC}"
    echo ""
    echo -e "${YELLOW}Press Enter to continue anyway, or Ctrl+C to exit...${NC}"
    read
fi

echo ""
echo -e "${CYAN}Configuration:${NC}"
echo -e "  Target URL: ${CLIENT_URL}"
echo -e "  Interval: ${INTERVAL}s"
if [ "$DURATION" -eq 0 ]; then
    echo -e "  Duration: Infinite (Ctrl+C to stop)"
else
    echo -e "  Duration: ${DURATION}s"
fi
echo ""

# Function to make a test request
make_request() {
    local req_num=$1
    
    # Make request with timeout
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "$CLIENT_URL/client/users/1" 2>/dev/null)
    
    # Get current timestamp
    local timestamp=$(date '+%H:%M:%S')
    
    # Determine result
    if [ "$STATUS" == "200" ]; then
        # Success
        echo -e "${GREEN}✓${NC} [${timestamp}] Request ${req_num}: SUCCESS"
        ((SUCCESS_COUNT++))
        
    elif [ "$STATUS" == "503" ]; then
        # Service unavailable - likely circuit breaker open
        echo -e "${MAGENTA}⚡${NC} [${timestamp}] Request ${req_num}: FAST FAIL (Circuit Breaker OPEN)"
        ((FAST_FAIL_COUNT++))
        ((FAILURE_COUNT++))
        
    elif [ -z "$STATUS" ]; then
        # Timeout or connection error
        echo -e "${RED}✗${NC} [${timestamp}] Request ${req_num}: CONNECTION ERROR / TIMEOUT"
        ((FAILURE_COUNT++))
        
    else
        # Other error
        echo -e "${RED}✗${NC} [${timestamp}] Request ${req_num}: ERROR ${STATUS}"
        ((FAILURE_COUNT++))
    fi
}

# Function to print statistics
print_stats() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - START_TIME))
    local success_rate=0
    
    if [ $REQUEST_COUNT -gt 0 ]; then
        success_rate=$(awk "BEGIN {printf \"%.1f\", $SUCCESS_COUNT * 100 / $REQUEST_COUNT}")
    fi
    
    echo ""
    echo -e "${BLUE}─────────────────────────────────────────────────────${NC}"
    echo -e "${CYAN}STATISTICS${NC}"
    echo -e "${BLUE}─────────────────────────────────────────────────────${NC}"
    printf "%-20s %s\n" "Total Requests:" "$REQUEST_COUNT"
    printf "%-20s ${GREEN}%s${NC}\n" "Successful:" "$SUCCESS_COUNT"
    printf "%-20s ${RED}%s${NC}\n" "Failed:" "$FAILURE_COUNT"
    printf "%-20s ${MAGENTA}%s${NC}\n" "Fast Fails:" "$FAST_FAIL_COUNT"
    printf "%-20s %.1f%%\n" "Success Rate:" "$success_rate"
    printf "%-20s %ds\n" "Elapsed Time:" "$elapsed"
    echo -e "${BLUE}─────────────────────────────────────────────────────${NC}"
    echo ""
}

# Trap Ctrl+C to print final statistics
trap 'echo ""; echo ""; print_stats; echo -e "${YELLOW}Load generator stopped by user${NC}"; exit 0' INT TERM

# Main loop
echo -e "${YELLOW}Starting load generation... (Press Ctrl+C to stop)${NC}"
echo ""

while true; do
    ((REQUEST_COUNT++))
    
    make_request $REQUEST_COUNT
    
    # Check if duration limit reached
    if [ "$DURATION" -gt 0 ]; then
        current_time=$(date +%s)
        elapsed=$((current_time - START_TIME))
        
        if [ $elapsed -ge $DURATION ]; then
            echo ""
            echo -e "${GREEN}Duration limit reached${NC}"
            break
        fi
    fi
    
    # Print statistics every 20 requests
    if [ $((REQUEST_COUNT % 20)) -eq 0 ]; then
        print_stats
    fi
    
    # Wait before next request
    sleep $INTERVAL
done

# Print final statistics
print_stats

echo -e "${GREEN}Load generator finished${NC}"
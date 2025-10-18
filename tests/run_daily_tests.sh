#!/bin/bash
# Main Test Orchestrator - Runs all automated tests

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR="/app/tests/results"
MAIN_LOG="$LOG_DIR/daily_test_$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "==========================================" | tee "$MAIN_LOG"
echo "DAILY AUTOMATED TEST SUITE" | tee -a "$MAIN_LOG"
echo "Start Time: $(date)" | tee -a "$MAIN_LOG"
echo "==========================================" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

# Run Backend Tests
echo ">>> Running Backend Tests..." | tee -a "$MAIN_LOG"
/bin/bash /app/tests/automated_backend_test.sh
BACKEND_EXIT=$?
echo "" | tee -a "$MAIN_LOG"

# Run Frontend Tests
echo ">>> Running Frontend Tests..." | tee -a "$MAIN_LOG"
/bin/bash /app/tests/automated_frontend_test.sh
FRONTEND_EXIT=$?
echo "" | tee -a "$MAIN_LOG"

# System Health Check
echo ">>> System Health Check..." | tee -a "$MAIN_LOG"
echo "Services Status:" | tee -a "$MAIN_LOG"
sudo supervisorctl status | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

echo "Disk Usage:" | tee -a "$MAIN_LOG"
df -h / | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

echo "Memory Usage:" | tee -a "$MAIN_LOG"
free -h | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

# Database Stats
echo ">>> Database Statistics..." | tee -a "$MAIN_LOG"
USER_COUNT=$(mongosh test_database --quiet --eval "db.users.countDocuments()")
NODE_COUNT=$(mongosh test_database --quiet --eval "db.nodes.countDocuments()")
echo "Total Users: $USER_COUNT" | tee -a "$MAIN_LOG"
echo "Total Nodes: $NODE_COUNT" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

# Final Summary
echo "==========================================" | tee -a "$MAIN_LOG"
echo "TEST SUITE COMPLETED" | tee -a "$MAIN_LOG"
echo "End Time: $(date)" | tee -a "$MAIN_LOG"
echo "Backend Tests: $([ $BACKEND_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')" | tee -a "$MAIN_LOG"
echo "Frontend Tests: $([ $FRONTEND_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')" | tee -a "$MAIN_LOG"
echo "==========================================" | tee -a "$MAIN_LOG"

# Keep only last 30 days of logs
find "$LOG_DIR" -name "*.log" -type f -mtime +30 -delete

exit 0

#!/bin/bash
# View Test Results - Shows summary of all automated tests

LOG_DIR="/app/tests/results"

echo "=========================================="
echo "AUTOMATED TEST RESULTS DASHBOARD"
echo "=========================================="
echo ""

# Check if cron job is active
echo "📅 Cron Job Status:"
crontab -l | grep "run_daily_tests"
echo ""

# Show summary
echo "📊 Test Summary (All Time):"
if [ -f "$LOG_DIR/test_summary.csv" ]; then
    echo "Date                | Total | Passed | Failed"
    echo "--------------------+-------+--------+-------"
    tail -n 10 "$LOG_DIR/test_summary.csv" | grep -v "timestamp" || echo "No tests run yet"
fi
echo ""

# Show latest test results
echo "📝 Latest Test Logs:"
LATEST_DAILY=$(ls -t $LOG_DIR/daily_test_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_DAILY" ]; then
    echo "Latest Daily Test: $(basename $LATEST_DAILY)"
    tail -n 30 "$LATEST_DAILY"
else
    echo "No daily tests run yet"
fi
echo ""

# Show test files
echo "📁 Test Files Available:"
ls -lh /app/tests/*.sh
echo ""

echo "💡 Commands:"
echo "  Run tests now:       /app/tests/run_daily_tests.sh"
echo "  View all logs:       ls -lh $LOG_DIR/"
echo "  View latest log:     tail -f $LOG_DIR/cron_output.log"
echo "  Backend test only:   /app/tests/automated_backend_test.sh"
echo "  Frontend test only:  /app/tests/automated_frontend_test.sh"
echo "=========================================="

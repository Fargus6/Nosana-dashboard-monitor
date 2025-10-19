# 📊 Earnings Statistics System

## Overview
Comprehensive earnings tracking system that records job completion earnings and provides daily, monthly, and yearly statistics for each node.

## Features Implemented

### Backend (✅ Complete)

**1. Earnings Tracking**
- Automatic saving of job earnings when jobs complete
- Stores: duration, NOS earned, USD value, timestamps
- Linked to user and node for privacy

**2. Rolling Year Cycle**
- Tracks earnings from first job date
- 12-month cycle per node
- Automatic archiving after 1 year
- Keeps last 3 archived years

**3. Calendar Month Breakdown**
- First month: Partial (from tracking start to month end)
- Subsequent months: Full calendar months (1st to last day)
- Continues until year cycle completes

**4. API Endpoints**

```
GET /api/earnings/node/{address}/yesterday
- Returns yesterday's complete earnings
- Shows: NOS, USD, job count, duration

GET /api/earnings/node/{address}/today
- Returns today's earnings (in progress)
- Shows: NOS, USD, job count, duration

GET /api/earnings/node/{address}/monthly
- Returns all calendar months since tracking started
- Shows: each month's earnings, dates, job counts
- Marks current month and partial first month

GET /api/earnings/node/{address}/yearly
- Returns current year cycle total
- Shows: months completed/remaining
- Returns archived years (last 3)
```

**5. Database Collections**

**job_earnings:**
```javascript
{
  id: "uuid",
  user_id: "user-uuid",
  node_id: "node-address",
  node_name: "Node Alpha",
  completed_at: "2025-10-19T12:00:00Z",
  duration_seconds: 3600,
  nos_earned: 1.95,
  usd_value: 0.90,
  date: "2025-10-19",  // For daily queries
  month: "2025-10",     // For monthly queries
  year: "2025"          // For yearly queries
}
```

**node_tracking_metadata:**
```javascript
{
  node_id: "node-address",
  user_id: "user-uuid",
  tracking_started: "2025-10-18T10:30:00Z",
  current_year_start: "2025-10-18T10:30:00Z",
  archived_years: [
    {
      year_number: 1,
      start_date: "2025-10-18",
      end_date: "2026-10-17",
      total_nos: 1847.5,
      total_usd: 852.05,
      total_jobs: 1653
    }
  ]
}
```

**6. Automatic Year Rollover**
- Checks on each job completion
- When 365 days elapsed from current_year_start:
  - Calculates year total
  - Archives the year
  - Resets counters for new year
  - Maintains only last 3 archived years

## Frontend Implementation Needed

### 1. Node Card Update
Add yesterday's earnings display:

```jsx
<div className="node-card">
  <h3>{node.name}</h3>
  <div className="status">Online</div>
  
  {/* NEW: Yesterday earnings */}
  <div className="yesterday-earnings">
    💰 Yesterday: {yesterdayEarnings.nos} NOS (${yesterdayEarnings.usd})
  </div>
  
  {/* NEW: Stats button */}
  <button onClick={() => openStats(node.address)}>
    📊 Stats
  </button>
</div>
```

### 2. Statistics Page/Modal
Create detailed statistics view:

```jsx
<StatisticsPage nodeAddress={address}>
  <h2>📊 Earnings Statistics - {nodeName}</h2>
  <p>Tracking started: {trackingStarted}</p>
  
  {/* Daily Section */}
  <section>
    <h3>YESTERDAY</h3>
    <p>{yesterdayData.date}</p>
    <p>{yesterdayData.nos} NOS (${yesterdayData.usd})</p>
    <p>{yesterdayData.jobCount} jobs | {formatDuration(yesterdayData.duration)}</p>
  </section>
  
  <section>
    <h3>TODAY (In Progress)</h3>
    <p>{todayData.date}</p>
    <p>{todayData.nos} NOS (${todayData.usd}) so far</p>
    <p>{todayData.jobCount} jobs | {formatDuration(todayData.duration)}</p>
  </section>
  
  {/* Monthly Section */}
  <section>
    <h3>MONTHLY BREAKDOWN</h3>
    {monthlyData.months.map(month => (
      <div key={month.month}>
        <h4>{month.month} {month.isPartial && '(partial)'} {month.isCurrent && '(current)'}</h4>
        <p>{month.startDate} to {month.endDate}</p>
        <p>{month.nos} NOS (${month.usd}) | {month.jobCount} jobs</p>
      </div>
    ))}
  </section>
  
  {/* Yearly Section */}
  <section>
    <h3>YEAR {yearlyData.currentYear.yearNumber} TOTAL</h3>
    <p>{yearlyData.currentYear.startDate} - {yearlyData.currentYear.endDate}</p>
    <p>{yearlyData.currentYear.nos} NOS (${yearlyData.currentYear.usd})</p>
    <p>{yearlyData.currentYear.jobCount} jobs</p>
    <p>[{yearlyData.currentYear.monthsCompleted} months completed, {yearlyData.currentYear.monthsRemaining} remaining]</p>
  </section>
  
  {/* Archived Years */}
  {yearlyData.archivedYears.length > 0 && (
    <section>
      <h3>ARCHIVED YEARS</h3>
      {yearlyData.archivedYears.map(year => (
        <div key={year.yearNumber}>
          <h4>Year {year.yearNumber}</h4>
          <p>{year.startDate} - {year.endDate}</p>
          <p>{year.totalNos} NOS (${year.totalUsd})</p>
          <p>{year.totalJobs} jobs</p>
        </div>
      ))}
    </section>
  )}
</StatisticsPage>
```

### 3. API Integration Functions

```javascript
// Fetch yesterday's earnings for node card
async function fetchYesterdayEarnings(nodeAddress) {
  const response = await fetch(
    `${BACKEND_URL}/api/earnings/node/${nodeAddress}/yesterday`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return await response.json();
}

// Fetch all statistics for details page
async function fetchNodeStatistics(nodeAddress) {
  const [yesterday, today, monthly, yearly] = await Promise.all([
    fetch(`${BACKEND_URL}/api/earnings/node/${nodeAddress}/yesterday`),
    fetch(`${BACKEND_URL}/api/earnings/node/${nodeAddress}/today`),
    fetch(`${BACKEND_URL}/api/earnings/node/${nodeAddress}/monthly`),
    fetch(`${BACKEND_URL}/api/earnings/node/${nodeAddress}/yearly`)
  ]);
  
  return {
    yesterday: await yesterday.json(),
    today: await today.json(),
    monthly: await monthly.json(),
    yearly: await yearly.json()
  };
}
```

## How It Works

### 1. First Job Completion
- User adds node on Oct 18, 2025
- First job completes → Creates tracking metadata
- `tracking_started`: Oct 18, 2025
- `current_year_start`: Oct 18, 2025
- Saves earnings record

### 2. Ongoing Tracking
- Each job completion saves earnings
- Earnings tagged with date, month, year
- Aggregated on-demand for statistics

### 3. Monthly Display
- **Oct 2025:** Oct 18-31 (partial first month)
- **Nov 2025:** Nov 1-30 (full month)
- **Dec 2025:** Dec 1-31 (full month)
- ... continues for 12 calendar months

### 4. Year Rollover (After 365 days)
- On Oct 18, 2026 (365 days later)
- Archives Year 1: Oct 18, 2025 - Oct 17, 2026
- Resets: `current_year_start` = Oct 18, 2026
- Year 2 begins

### 5. Archive Management
- Keeps last 3 archived years
- Older years automatically removed
- Users can view archived year totals

## Testing

### Test Earnings Tracking
```bash
# Login and trigger job completion
# Earnings should be automatically saved

# Check if earnings saved
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8001/api/earnings/node/NODE_ADDRESS/yesterday

# Expected: Returns earnings data or zeros if no jobs yesterday
```

### Test Statistics Endpoints
```bash
# Get today's earnings
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8001/api/earnings/node/NODE_ADDRESS/today

# Get monthly breakdown
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8001/api/earnings/node/NODE_ADDRESS/monthly

# Get yearly totals
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8001/api/earnings/node/NODE_ADDRESS/yearly
```

## Next Steps

1. ✅ Backend earnings tracking - COMPLETE
2. ✅ API endpoints - COMPLETE
3. ⏳ Frontend node card update - NEEDED
4. ⏳ Frontend statistics page - NEEDED
5. ⏳ Testing with real job completions - NEEDED

## Benefits

### For Users
- Track daily earnings progress
- See monthly income patterns
- View yearly totals
- Access historical data
- No manual recording needed

### For App
- Data-driven insights
- Better user engagement
- Historical records preserved
- Automatic archiving
- Efficient queries with indexes

## Database Indexes (Recommended)

```javascript
// For fast queries
db.job_earnings.createIndex({ "node_id": 1, "user_id": 1, "date": -1 })
db.job_earnings.createIndex({ "node_id": 1, "user_id": 1, "month": -1 })
db.job_earnings.createIndex({ "node_id": 1, "user_id": 1, "completed_at": -1 })
db.node_tracking_metadata.createIndex({ "node_id": 1, "user_id": 1 }, { unique: true })
```

## Notes

- All timestamps use UTC timezone
- Earnings calculated at job completion time
- NOS price fetched live from CoinGecko
- USD values stored at time of completion (not recalculated)
- Year cycle is 365 days (not calendar year)
- First month is always partial (start date to month end)

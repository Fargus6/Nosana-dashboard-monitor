# Step-by-Step: Testing Full History Scraping for One Node

## Test Node
**Address**: `9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV`
**Total Jobs**: 341 jobs
**Owner**: Your account

## Step 1: Login and Open Modal
1. Login to the app
2. Find the test node: `9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV`
3. Click "View Earnings & Statistics" button

## Step 2: Scrape Full History
1. In the modal, you'll see a **purple "Scrape Full History"** button
2. Click it
3. Wait 2-3 minutes (scraping 341 jobs across ~35 pages)
4. You'll see a success toast: "✅ Scraped 341 jobs! X new jobs stored."

## Step 3: Verify Statistics
After scraping completes, the modal will automatically refresh and show:

### ✅ Yesterday's Earnings
- Should show actual earnings from 24-48 hours ago
- Example: "$3.24 USD | 21.60 NOS | 20 jobs"

### ✅ Monthly Breakdown
- Should list all months with data
- Example:
  - October 2025: $45.80 | 305 NOS | 283 jobs
  - September 2025: $120.50 | 803 NOS | 745 jobs

### ✅ Yearly Totals
- Should show 2025 total
- Example: 2025: $1,250.00 | 8,333 NOS | 7,730 jobs

## Step 4: Verify in Database
```bash
# Check total jobs stored
mongosh --quiet "$MONGO_URL" --eval "
  db = db.getSiblingDB('test_database'); 
  db.scraped_jobs.countDocuments({node_address: '9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV'})
"
# Should return: 341

# Check oldest job
mongosh --quiet "$MONGO_URL" --eval "
  db = db.getSiblingDB('test_database'); 
  printjson(db.scraped_jobs.find({node_address: '9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV'}).sort({started: 1}).limit(1).toArray())
"

# Check newest job
mongosh --quiet "$MONGO_URL" --eval "
  db = db.getSiblingDB('test_database'); 
  printjson(db.scraped_jobs.find({node_address: '9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV'}).sort({started: -1}).limit(1).toArray())
"
```

## What to Check
- [ ] Full history scraping completes without errors
- [ ] All 341 jobs are stored in MongoDB
- [ ] Yesterday's earnings show correct data (not 0)
- [ ] Monthly breakdown shows multiple months
- [ ] Yearly totals show accurate numbers
- [ ] Earnings match Nosana dashboard calculations

## Expected Results

### Yesterday's Data
If the node ran jobs yesterday (24-48h ago), you should see:
- Non-zero USD and NOS amounts
- Correct job count
- Duration in hours

### Monthly Data
Should show months like:
- Current month (October 2025)
- Previous months with data
- Each month showing total earnings

### Yearly Data
- 2025 total earnings
- Total job count
- Total duration

## After Testing This One Node

Once verified working correctly, we can:
1. **Apply to other nodes**: Click "Scrape Full History" for each
2. **Automate**: Create a button to "Scrape All Nodes"
3. **Schedule**: Set up periodic scraping (every hour)

## Troubleshooting

### If scraping fails:
- Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
- Look for Playwright errors
- Check if dashboard is accessible

### If statistics show 0:
- Verify jobs are in MongoDB
- Check `completed` field is not null for SUCCESS jobs
- Verify date ranges match

### If pagination doesn't work:
- Dashboard might have changed UI
- Check browser console for errors
- May need to adjust selectors

---

**Ready to test!** Login and click "Scrape Full History" for node `9hsWPkJU...`

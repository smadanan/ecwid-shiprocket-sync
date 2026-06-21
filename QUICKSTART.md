# Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Get Your API Credentials

### Ecwid
1. Log in to your Ecwid dashboard
2. Go to **Settings** → **API Tokens**
3. Click **Create Token**
4. Name it: "Shiprocket Integration"
5. Grant permission: **Read Orders**
6. Copy the token (you'll need it in a moment)
7. Your Store ID is in the URL: `app.ecwid.com/cp/123456` → Use `123456`

### Shiprocket
1. Log in to Shiprocket dashboard
2. Note your **email** and **password**
3. Go to **Settings** → **Pickup Locations**
4. Note your default location's **ID** (e.g., 1, 2, 3...)
5. Go to **Settings** → **Sales Channels**
6. Note a **Channel ID** (e.g., 1, 2, 3...)

## Step 2: Install & Configure

### Option A: Automatic Setup (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Run setup wizard
python setup.py
```

Answer the prompts with your credentials. The wizard will test your connection!

### Option B: Manual Setup

1. Copy example config:
```bash
cp config.example.json config.json
```

2. Edit `config.json`:
```bash
nano config.json  # or use your editor
```

3. Fill in your credentials:
```json
{
  "ecwid_store_id": "YOUR_STORE_ID",
  "ecwid_api_token": "YOUR_API_TOKEN",
  "shiprocket_email": "your@email.com",
  "shiprocket_password": "your_password",
  "shiprocket_pickup_location_id": 1,
  "shiprocket_channel_id": 1,
  "default_package_length": 10,
  "default_package_breadth": 10,
  "default_package_height": 10,
  "default_package_weight": 0.5
}
```

## Step 3: Start Using

### Option 1: Web Dashboard (Easiest)

```bash
python main.py webui
```

Then open: **http://localhost:5000**

You'll see:
- 📊 Order statistics
- 🚀 Sync button with custom hours
- 🔁 Retry failed orders button
- 🧪 Test connection button
- 📊 Status dashboard

### Option 2: Command Line

```bash
# Sync last 24 hours
python main.py sync

# Check status
python main.py status

# Retry failed orders
python main.py retry
```

## Step 4: Schedule Automatic Syncing (Optional)

### Linux/Mac Cron

```bash
# Open crontab editor
crontab -e

# Add this line to sync every 6 hours:
0 */6 * * * cd /path/to/ecwid_shiprocket_tool && python main.py sync >> sync.log 2>&1
```

### Windows Task Scheduler

1. Create `sync.bat`:
```batch
@echo off
cd C:\path\to\ecwid_shiprocket_tool
python main.py sync >> sync.log 2>&1
```

2. Open Task Scheduler
3. Create Basic Task
4. Run: `C:\path\to\sync.bat`
5. Trigger: Daily or at your desired interval

## Troubleshooting

### "Authentication failed"
- Double-check email/password
- Ensure Shiprocket account is active
- Check API token validity

### "No orders found"
- Check Ecwid store has orders
- Use `--hours` flag to increase time range:
  ```bash
  python main.py sync --hours 168  # Last 7 days
  ```

### "Connection test fails"
- Check internet connection
- Verify credentials are correct
- Check firewall isn't blocking APIs

### View logs
```bash
tail -f integration.log
```

## Common Commands

```bash
# First sync
python main.py sync

# Check how many orders synced
python main.py status

# Sync with custom time range (last 48 hours)
python main.py sync --hours 48

# Force re-sync already processed orders
python main.py sync --force

# Retry failed orders
python main.py retry

# Start web dashboard
python main.py webui --port 5000
```

## What's Happening?

When you run `sync`:

1. **Fetches** orders from Ecwid (created in last 24 hours)
2. **Transforms** them to Shiprocket format
3. **Skips** already processed orders
4. **Uploads** to Shiprocket
5. **Tracks** what succeeded/failed
6. **Logs** everything for your reference

## Next Steps

- Check `README.md` for advanced features
- Configure cron/scheduler for automatic syncing
- Set up webhooks for notifications
- Customize order field mapping if needed

## Need Help?

1. Check `integration.log` for detailed error messages
2. Use web UI test button to verify connections
3. Review README.md for troubleshooting guide
4. Check API documentation:
   - [Ecwid API](https://developers.ecwid.com/api-documentation)
   - [Shiprocket API](https://shiprocket.in/api-docs)

---

**That's it!** You're ready to start syncing orders. 🎉

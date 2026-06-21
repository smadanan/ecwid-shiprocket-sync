# Deploy to Render (Cloud Hosting)

Complete guide to deploy your Ecwid-Shiprocket integration to Render for **free** with automatic syncing 24/7.

---

## **Why Render? (vs Local Task Scheduler)**

✅ **Runs 24/7** - No laptop needed  
✅ **Free tier** available  
✅ **Auto-restart** if crashes  
✅ **Easy monitoring** via web dashboard  
✅ **Automatic syncing** - Runs on schedule  
✅ **Professional setup**  

---

## **Step 1: Create GitHub Account & Repository**

### 1.1 Create GitHub Account
- Go to: https://github.com/signup
- Sign up (free)
- Verify email

### 1.2 Create New Repository
1. Click **"New"** (top left)
2. Repository name: `ecwid-shiprocket-sync`
3. Description: `Ecwid to Shiprocket Order Integration`
4. **Private** (recommended - keeps your credentials safe)
5. Click **"Create repository"**

### 1.3 Upload Your Files
You have two options:

**Option A: Using GitHub Web (Easiest)**
1. On your new repository page, click **"Add file"** → **"Upload files"**
2. Drag & drop all your files (except `config.json`!)
3. Include:
   - `main.py`
   - `ecwid_client.py`
   - `shiprocket_client.py`
   - `config.py`
   - `database.py`
   - `webui.py`
   - `scheduler.py`
   - `setup.py`
   - `requirements.txt`
   - `.gitignore`
   - `Procfile`
   - `runtime.txt`
   - `templates/dashboard.html`
4. Commit & push

**Option B: Using Git Command Line (If comfortable)**
```bash
git clone https://github.com/YOUR_USERNAME/ecwid-shiprocket-sync.git
cd ecwid-shiprocket-sync
# Copy all files here
git add .
git commit -m "Initial commit"
git push origin main
```

---

## **Step 2: Create Render Account**

1. Go to: https://render.com
2. Click **"Sign up"** (you can use GitHub account!)
3. Verify email

---

## **Step 3: Deploy to Render**

### 3.1 Create New Web Service
1. On Render dashboard, click **"New"** → **"Web Service"**
2. Click **"Connect account"** if GitHub not connected
3. Find your repository: `ecwid-shiprocket-sync`
4. Click **"Connect"**

### 3.2 Configure Service
Fill in these details:

- **Name:** `ecwid-shiprocket-sync`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py webui --port $PORT`
- **Plan:** `Free` (blue option)

### 3.3 Add Environment Variables
This is **CRITICAL** - your credentials go here (NOT in code):

Click **"Advanced"** → **"Add Environment Variable"** and add:

```
ECWID_STORE_ID = 13339036
ECWID_API_TOKEN = your_secret_token_here
SHIPROCKET_EMAIL = your_email@gmail.com
SHIPROCKET_PASSWORD = your_password_here
SHIPROCKET_PICKUP_LOCATION_ID = 123456
SHIPROCKET_CHANNEL_ID = 1
```

Replace with YOUR actual values!

### 3.4 Deploy
Click **"Create Web Service"**

**Wait 3-5 minutes** while Render builds and deploys your app.

You'll see:
```
Build successful ✓
App running at: https://ecwid-shiprocket-sync.onrender.com
```

---

## **Step 4: Access Your Dashboard**

Once deployed, you can access your app at:
```
https://ecwid-shiprocket-sync.onrender.com
```

Open in browser → You should see the purple dashboard!

---

## **Step 5: Set Up Automatic Syncing**

Your app is now running 24/7! But you need to schedule the syncs.

### Option A: Manual Dashboard (No Setup)
- Just visit https://ecwid-shiprocket-sync.onrender.com
- Click "Start Sync" whenever you want
- **Works even if your laptop is off!**

### Option B: Automatic Syncing Every 6 Hours (Recommended)

We need to modify `main.py` to include a scheduler. Here's what to do:

1. Edit `main.py` on GitHub
2. Add this at the top of the `main()` function:

```python
# Add scheduler for automatic syncing
if args.command == 'webui':
    from scheduler import SyncScheduler
    scheduler = SyncScheduler(integrator)
    scheduler.schedule_interval_sync(hours=6)  # Sync every 6 hours
    logger.info("Scheduler started - syncing every 6 hours")
```

3. Commit & push to GitHub
4. Render will auto-redeploy (takes 2-3 minutes)
5. Now syncs run automatically every 6 hours! ✅

---

## **Step 6: Monitor Your App**

### View Logs
1. Go to Render dashboard
2. Click your service name
3. Click **"Logs"** tab
4. See all sync operations in real-time!

### View Dashboard
- Visit: https://ecwid-shiprocket-sync.onrender.com
- Click "Test Connection" to verify APIs
- Click "Start Sync" for manual sync
- See status anytime!

---

## **Important Notes**

### Environment Variables
- **NEVER** put credentials in code
- Always use Environment Variables in Render
- Keep your GitHub repository private
- `.gitignore` prevents `config.json` from uploading

### Free Tier Limitations (Render)
- App spins down after 15 mins of inactivity
- But wakes up when accessed
- So keep dashboard bookmarked to keep it alive
- Or use paid plan ($7/month) for always-on

### Keep App Alive (Free Tier)
To prevent spindown, use a monitoring service:
- Better Uptime (free tier)
- Kuma (self-hosted)
- Or just visit the dashboard daily

---

## **Troubleshooting**

### App won't start
- Check Render logs for errors
- Verify all environment variables set
- Check requirements.txt has all packages

### Sync not running
- Check logs to see if scheduler started
- Verify credentials are correct
- Try manual sync first

### Can't access dashboard
- Check if Render URL is correct
- Wait 5 minutes for app to wake up
- Check Render dashboard for errors

---

## **Next Steps**

1. ✅ Create GitHub account
2. ✅ Upload files to GitHub
3. ✅ Create Render account
4. ✅ Deploy to Render
5. ✅ Add environment variables
6. ✅ Test dashboard
7. ✅ Set up automatic syncing (optional)
8. ✅ Monitor logs

---

## **You're All Set!**

Your app is now running in the cloud 24/7!

**Access it anytime:**
```
https://ecwid-shiprocket-sync.onrender.com
```

**Syncs run automatically** (if you set up the scheduler)

**No laptop needed!** ✅

---

## **Costs**

- **GitHub:** Free
- **Render:** Free (with limitations) or $7/month
- **Total:** $0-7/month

Much cheaper than keeping a laptop on 24/7!


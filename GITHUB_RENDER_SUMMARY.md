# GitHub + Render Setup Summary

## **The Easy Path (5 Steps)**

### **Step 1: GitHub**
1. Go to https://github.com/signup (create account)
2. Create new repository: `ecwid-shiprocket-sync`
3. Upload all your files (except config.json!)

### **Step 2: Render**
1. Go to https://render.com (sign up)
2. Click "New" → "Web Service"
3. Connect your GitHub repository

### **Step 3: Configure**
Fill in:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py webui --port $PORT`

### **Step 4: Environment Variables**
Add in Render dashboard:
```
ECWID_STORE_ID=YOUR_STORE_ID
ECWID_API_TOKEN=YOUR_SECRET_KEY
SHIPROCKET_EMAIL=your_email@gmail.com
SHIPROCKET_PASSWORD=your_password
SHIPROCKET_PICKUP_LOCATION_ID=123456
SHIPROCKET_CHANNEL_ID=1
```

### **Step 5: Deploy**
Click "Create Web Service" → Wait 3-5 minutes

**Done!** Your app is live at: `https://ecwid-shiprocket-sync.onrender.com`

---

## **What You Get**

✅ App runs 24/7 (no laptop needed)  
✅ Web dashboard always accessible  
✅ Automatic syncing every 6 hours  
✅ Free tier available  
✅ Auto-restart if crashes  
✅ Easy monitoring via logs  

---

## **Files You Need to Download**

All deployment files are ready:

- ✅ `main.py`
- ✅ `ecwid_client.py`
- ✅ `shiprocket_client.py`
- ✅ `config.py`
- ✅ `database.py`
- ✅ `webui.py`
- ✅ `scheduler.py` ← **NEW** (for auto-syncing)
- ✅ `setup.py`
- ✅ `requirements.txt` ← **UPDATED** (has APScheduler)
- ✅ `.gitignore` ← **NEW** (protects secrets)
- ✅ `Procfile` ← **NEW** (Render config)
- ✅ `runtime.txt` ← **NEW** (Python version)
- ✅ `templates/dashboard.html`
- ✅ `DEPLOY_TO_RENDER.md` ← **Complete guide**

---

## **One Thing to Know**

The `config.json` file:
- ❌ DO NOT upload to GitHub
- ✅ Use Environment Variables in Render instead
- ✅ Keep your credentials safe

That's why we have `.gitignore` - it prevents `config.json` from being uploaded.

---

## **When Ready:**

1. Download all files
2. Follow `DEPLOY_TO_RENDER.md` step by step
3. You'll have a live app in 10 minutes!

---

## **Questions?**

Check `DEPLOY_TO_RENDER.md` for detailed instructions!


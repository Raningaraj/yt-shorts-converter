# 🚀 Deployment Guide: Railway or Render

This guide will help you deploy the YouTube to Shorts Converter with Streamlit frontend and Flask backend on **Railway** or **Render**.

## Quick Comparison

| Feature | Railway | Render |
|---------|---------|--------|
| **Free Tier** | $5/month credit | Decent free tier |
| **Startup Time** | Fast | Can be slow (free tier) |
| **Video Processing** | ✅ Good RAM allocation | ⚠️ Limited on free tier |
| **Setup Difficulty** | Very easy | Easy |
| **Recommended** | ✅ Best for this project | Alternative |

---

## 🚂 Option 1: Deploy on Railway (Recommended)

Railway makes deployment extremely simple. Follow these steps:

### Step 1: Prepare Your Repository
Your repository already has everything needed:
- ✅ `Procfile` - tells Railway how to run your app
- ✅ `start.py` - manages Flask + Streamlit
- ✅ `streamlit_app.py` - Streamlit frontend
- ✅ `requirements.txt` - all dependencies

### Step 2: Create Railway Account & Deploy
1. Go to https://railway.app
2. Click **"Start Project"**
3. Select **"Deploy from GitHub"**
4. Choose your `yt-shorts-converter` repository
5. Railway will automatically:
   - Detect the Procfile
   - Install dependencies
   - Start your app

### Step 3: Configure Environment (Important!)
In Railway dashboard, go to **Variables** and add:

```
GROQ_API_KEY=your_groq_key_here
FLASK_ENV=production
BACKEND_URL=https://your-railway-app.railway.app
```

**Get your Groq API Key** (FREE):
1. Visit https://console.groq.com
2. Sign up/login
3. Create an API key
4. Copy and paste it in Railway Variables

### Step 4: Monitor Deployment
- Railway shows logs in real-time
- Both Flask (port 5000) and Streamlit (port 8501) will start automatically
- The public URL will be shown once deployment is complete

---

## 🎨 Option 2: Deploy on Render

Render also works well. Follow these steps:

### Step 1: Connect Repository
1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Select **"Connect a GitHub repository"**
4. Choose `yt-shorts-converter`

### Step 2: Configure Service
Fill in the form:
- **Name**: `yt-shorts-converter`
- **Environment**: `Python 3.11`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python start.py`
- **Instance Type**: Standard (for video processing)

### Step 3: Set Environment Variables
Click **"Advanced"** and add:

```
GROQ_API_KEY=your_groq_key_here
FLASK_ENV=production
BACKEND_URL=https://your-render-app.onrender.com
PORT=8501
FLASK_PORT=5000
```

### Step 4: Deploy
- Click **"Create Web Service"**
- Render will build and deploy automatically
- Logs are shown during deployment

---

## 🔐 Getting Your Groq API Key (FREE)

The app uses **Groq** for AI transcription (completely free):

1. Visit https://console.groq.com
2. Sign up with email
3. Go to **API Keys**
4. Create a new key
5. Copy the key and add to your platform's environment variables

⚠️ **Important**: The Groq API key is REQUIRED for the app to work!

---

## 📊 What Gets Deployed

When you deploy, the platform runs:

```
┌─────────────────────────────┐
│    Your Railway/Render App  │
├─────────────────────────────┤
│                             │
│  ┌──────────────────────┐  │
│  │  Streamlit Frontend  │  │ Port 8501
│  │  (User Interface)    │  │
│  └──────────────────────┘  │
│           ↓                │
│  ┌──────────────────────┐  │
│  │  Flask Backend       │  │ Port 5000
│  │  • Video download    │  │
│  │  • AI transcription  │  │
│  │  • Video processing  │  │
│  └──────────────────────┘  │
│                             │
└─────────────────────────────┘
```

The Streamlit app is accessible from the public URL. Flask runs internally.

---

## 🧪 Testing Locally Before Deploying

To test locally with the Streamlit + Flask setup:

```bash
# Terminal 1: Start Flask backend
cd backend
python -m flask run --port=5000

# Terminal 2: Start Streamlit
streamlit run streamlit_app.py
```

Then visit `http://localhost:8501` in your browser.

---

## ⚠️ Common Issues & Solutions

### Issue: "Backend connection failed"
**Solution**: Make sure `BACKEND_URL` is set correctly in environment variables.

### Issue: "Out of memory" during video processing
**Solution**: 
- Railway Standard: Should be fine for most videos
- Render: Upgrade to Premium instance for large videos

### Issue: "Groq API key error"
**Solution**: 
- Check your API key in environment variables
- Make sure the key hasn't expired
- Get a new key from https://console.groq.com

### Issue: App takes too long to start
**Solution**: 
- This is normal for first deployment (Building dependencies)
- Subsequent restarts are faster
- Be patient (can take 2-3 minutes)

---

## 📈 Monitoring & Logs

### Railway
- Logs are shown in dashboard
- Click "Logs" tab to see real-time output
- Click service name for more details

### Render
- Logs show in "Logs" section
- Full deployment logs available
- Error messages clearly displayed

---

## 💰 Cost Estimates

### Railway
- **Free tier**: $5/month credit
- **Video processing**: Uses compute (usually ~$0.02-0.10 per conversion)
- **Total**: Usually free with monthly credit

### Render
- **Free tier**: Very limited (can't handle video processing)
- **Standard instance**: $7/month minimum
- **Recommended**: Pay-as-you-go plan

---

## 🎉 After Deployment

Your app will be live at:
- **Railway**: `https://your-app.railway.app`
- **Render**: `https://your-app.onrender.com`

Share the URL with others and they can use your YouTube to Shorts converter!

---

## 🔄 Updating Your App

After deploying, to update your app:

1. Make changes to your code locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update message"
   git push origin master
   ```
3. Railway/Render will automatically redeploy! ✨

---

## 📚 More Help

- **Railway Docs**: https://docs.railway.app
- **Render Docs**: https://render.com/docs
- **Streamlit Docs**: https://docs.streamlit.io
- **Groq Docs**: https://console.groq.com/docs

---

**You're ready to deploy! Choose Railway for the easiest experience.** 🚀

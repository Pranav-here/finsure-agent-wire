# 🔑 API CREDENTIALS QUICK REFERENCE

## What You Need

This bot requires **2 sets of API credentials**:

1. **X (Twitter) API** - REQUIRED ⚡
2. **YouTube Data API** - OPTIONAL but recommended 🎥

---

## 1️⃣ X (Twitter) API Credentials

### What You Need (4 credentials)

```
✅ X_API_KEY           (also called "Consumer Key")
✅ X_API_SECRET        (also called "Consumer Secret")
✅ X_ACCESS_TOKEN      (user access token)
✅ X_ACCESS_SECRET     (user access token secret)
```

### Where to Get Them

**URL**: https://developer.twitter.com/en/portal/dashboard

### Step-by-Step

1. **Sign in** with your Twitter account

2. **Create a Project**
   - Click "Create Project"
   - Name: "AI Finance News Bot"
   - Use case: "Making a bot"
   - Description: "Automated news aggregator"

3. **Create an App**
   - Name: "finsure-agent-wire" (must be unique)
   - Complete setup

4. **Save API Keys** ⚠️ IMPORTANT
   - You'll see **API Key** and **API Key Secret**
   - **COPY THESE NOW** - you won't see them again!
   - Save to a text file temporarily

5. **Set Permissions** ⚠️ CRITICAL
   - Go to app Settings
   - "User authentication settings" → "Set up"
   - **App permissions**: Select "Read and Write"
   - Type: "Web App, Automated App or Bot"
   - Callback URI: `http://localhost`
   - Website: `https://github.com/yourusername/finsure-agent-wire`
   - **Save**

6. **Generate Access Tokens**
   - Go to "Keys and tokens" tab
   - Under "Access Token and Secret" → **"Generate"**
   - **COPY BOTH** - Access Token and Access Token Secret
   - Save to your text file

### ⚠️ Common Mistakes

❌ **Forgetting to set "Read and Write" permissions**
   → Bot will get 403 Forbidden errors
   
❌ **Using old Access Tokens after changing permissions**
   → Must regenerate tokens after permission change

❌ **Copying keys with extra spaces**
   → Trim whitespace when pasting to `.env`

### Cost

**FREE** 🎉
- Free tier: 50 tweets per 24 hours
- Plenty for this bot (default: 5 tweets every 6h = 20/day)

---

## 2️⃣ YouTube Data API v3 Key

### What You Need (1 credential)

```
✅ YOUTUBE_API_KEY     (API key for YouTube Data API v3)
```

### Where to Get It

**URL**: https://console.cloud.google.com

### Step-by-Step

1. **Create a Project**
   - Click project dropdown (top left)
   - "New Project"
   - Name: "finsure-agent-wire"
   - Click "Create"
   - Wait ~30 seconds for project to be created

2. **Enable YouTube Data API v3**
   - Use search bar at top: "YouTube Data API v3"
   - Click on the API → Click **"Enable"**
   - Wait for it to enable

3. **Create API Key**
   - Left sidebar → "Credentials"
   - Click "Create Credentials" → **"API key"**
   - Copy the API key that appears
   - Save to your text file

4. **Restrict Key (Optional but Recommended)**
   - Click on your API key name
   - Under "API restrictions" → Select "Restrict key"
   - Choose only **"YouTube Data API v3"**
   - Save

### Cost

**FREE** 🎉
- Free tier: 10,000 units per day
- Each search = 100 units
- Bot runs every 6h = 4 runs × ~100 units = 400 units/day
- **You're using only 4% of your quota!**

### If You Skip This

- Bot still works! ✅
- Just won't include YouTube videos
- Only GDELT and RSS sources

---

## 3️⃣ RSS Feeds (Optional)

### What You Need

**Nothing!** Just URLs 🎉

### Common RSS Feeds

```bash
# Medium tags
https://medium.com/feed/tag/fintech
https://medium.com/feed/tag/insurtech
https://medium.com/feed/tag/ai

# Tech publications
https://techcrunch.com/category/fintech/feed/
https://venturebeat.com/category/ai/feed/

# Finance publications
https://www.pymnts.com/feed/
https://www.bankingtech.com/feed/
```

### How to Find RSS Feeds

Most sites have RSS! Look for:
- `/feed/` or `/rss/` URLs
- Orange RSS icon
- "Subscribe" links
- Google: "site:example.com rss"

### Cost

**FREE** - No API key needed 🎉

---

## 🔐 Storing Your Credentials

### For Local Testing

Create `.env` file:

```bash
# X API (REQUIRED)
X_API_KEY=AaBbCcDd123456xyz
X_API_SECRET=XxYyZz789secret
X_ACCESS_TOKEN=1234567890-AbCdEfGh
X_ACCESS_SECRET=SecretTokenHere123

# YouTube API (OPTIONAL)
YOUTUBE_API_KEY=AIzaSyABC123XYZ

# YouTube searches (customize!)
YOUTUBE_QUERIES=AI agents finance,autonomous agents banking,LLM fintech

# RSS feeds (customize!)
RSS_FEEDS=https://medium.com/feed/tag/fintech,https://techcrunch.com/feed/

# Safety (keep true for testing!)
DRY_RUN=true
REVIEW_MODE=false

# Settings
LOOKBACK_HOURS=24
MAX_POSTS_PER_RUN=5
MAX_POSTS_PER_DOMAIN=1
MIN_SCORE_THRESHOLD=5.0
```

### For GitHub Actions

**Never commit `.env` to GitHub!**

Instead:
1. Go to your repo on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret:

```
Name: X_API_KEY
Value: [paste your API key]

Name: X_API_SECRET
Value: [paste your API secret]

Name: X_ACCESS_TOKEN
Value: [paste your access token]

Name: X_ACCESS_SECRET
Value: [paste your access token secret]

Name: YOUTUBE_API_KEY
Value: [paste your YouTube key]
```

---

## ✅ Validation Checklist

Before running the bot:

- [ ] X API Key copied (starts with uppercase letters)
- [ ] X API Secret copied (longer, mixed case)
- [ ] X Access Token copied (format: `1234567890-AbCdEf...`)
- [ ] X Access Token Secret copied (mixed case string)
- [ ] X app has "Read and Write" permissions ⚠️
- [ ] YouTube API key copied (starts with `AIza...`) (optional)
- [ ] All credentials pasted into `.env`
- [ ] No extra spaces or quotes in `.env`
- [ ] `DRY_RUN=true` for initial testing

---

## 🆘 Troubleshooting Credentials

### X API Returns 401 Unauthorized

**Cause**: Wrong credentials

**Fix**:
1. Double-check all 4 credentials in `.env`
2. Make sure no extra spaces
3. Regenerate Access Token if needed

### X API Returns 403 Forbidden

**Cause**: App doesn't have write permissions

**Fix**:
1. Go to app settings on Twitter Developer Portal
2. User authentication settings → Edit
3. Set to "Read and Write"
4. **Save**
5. **Regenerate Access Token** (old ones won't work!)
6. Update `.env` with new tokens

### YouTube API Returns 403

**Cause**: API not enabled OR quota exceeded

**Fix**:
1. Make sure "YouTube Data API v3" is enabled in Google Cloud
2. Check quota: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
3. If over quota, wait 24h or remove `YOUTUBE_API_KEY` from `.env`

### YouTube API Returns 400 Bad Request

**Cause**: Invalid query format

**Fix**:
- Check `YOUTUBE_QUERIES` is comma-separated
- Remove any quotes around queries
- Example: `YOUTUBE_QUERIES=AI agents,fintech news`

---

## 🎯 Quick Start Command

After setting up credentials:

```bash
# Copy template
cp .env.example .env

# Edit .env with your favorite editor
# nano .env    (Linux/Mac)
# notepad .env (Windows)

# Or just:
code .env  # VS Code
```

Then paste your credentials!

---

## 📞 Need Help?

- **X API Issues**: https://developer.twitter.com/en/support
- **YouTube API Issues**: https://console.cloud.google.com/support
- **This Repo**: Open a GitHub issue

---

**Once you have these credentials, setup takes 5 minutes! 🚀**

See `NEXT_STEPS.md` for what to do next.

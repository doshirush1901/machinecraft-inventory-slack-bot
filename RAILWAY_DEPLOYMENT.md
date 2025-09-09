# 🚀 Railway Deployment Guide

## ✅ Code Fixed and Pushed!

Your Railway deployment has been fixed with:
- **Proper PORT handling** for Railway environment
- **Startup script** with better error handling
- **Database fallback** for immediate testing
- **Robust health checks**

## 🔧 Railway Deployment Steps:

### 1. **Railway Should Auto-Redeploy**
Railway should automatically redeploy with the new code. Check your Railway dashboard.

### 2. **Set Environment Variables**
In Railway dashboard → **Variables** tab:
```
SLACK_BOT_TOKEN=your-slack-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
FLASK_ENV=production
```

### 3. **Upload Database (Optional)**
- Go to Railway dashboard → **Storage** tab
- Upload `machinecraft_inventory_pipeline.db` (8.8GB)
- Or use the sample database created by the app

### 4. **Test Health Endpoint**
Visit: `https://steadfast-illumination-production.up.railway.app/health`

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "items_count": 10543066,
  "bot_token_set": true,
  "signing_secret_set": true
}
```

### 5. **Configure Slack Events API**
1. Go to https://api.slack.com/apps
2. Select your "Machinecraft In..." app
3. Go to **Event Subscriptions**
4. Enable Events
5. Set Request URL: `https://steadfast-illumination-production.up.railway.app/slack/events`
6. Subscribe to: `message.channels`, `message.groups`, `message.im`

## 🎯 What's Fixed:

✅ **PORT Environment Variable** - Properly handled for Railway  
✅ **Startup Script** - Better error handling and logging  
✅ **Database Fallback** - Creates sample data if main DB missing  
✅ **Health Checks** - Robust status reporting  
✅ **Railway Optimized** - Container-friendly configuration  

## 🧪 Test Commands:

Once deployed, test in Slack:
```
inventory summary
inventory servo motors
inventory mitsubishi
inventory expensive items
```

## 🆘 Troubleshooting:

### If Health Check Fails:
1. Check Railway logs for errors
2. Verify environment variables are set
3. Test with sample database first

### If Bot Doesn't Respond:
1. Check Slack Events API configuration
2. Verify webhook URL is correct
3. Ensure bot is added to channel

## 🎉 Expected Result:

Your bot will be live at: `https://steadfast-illumination-production.up.railway.app`

**Team can search through 10.5M+ inventory items worth ₹60M+ directly in Slack!**

---

**Need help?** Check Railway logs or test the health endpoint first!

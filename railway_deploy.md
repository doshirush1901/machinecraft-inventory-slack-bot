# 🚀 Deploy to Railway (No Server Needed!)

## What is Railway?
Railway is a cloud platform that automatically deploys your code - **no server setup needed!** It's like Heroku but better and cheaper.

## 🚀 Quick Deploy Steps:

### 1. Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. Connect your GitHub account

### 2. Deploy Your Bot
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository (or create one with these files)
4. Railway will automatically detect it's a Python app

### 3. Set Environment Variables
In Railway dashboard, go to "Variables" tab and add:
```
SLACK_BOT_TOKEN=your-slack-bot-token-here
SLACK_SIGNING_SECRET=6455ad30866671dad55a6eda3666d87c
FLASK_ENV=production
```

### 4. Upload Database
1. Go to "Storage" tab in Railway
2. Upload your `machinecraft_inventory_pipeline.db` file
3. Railway will give you a URL to access it

### 5. Get Your Bot URL
Railway will give you a URL like: `https://your-app-name.railway.app`
This is your bot's webhook URL!

## 🔧 Configure Slack Events API

### 1. Go to Slack App Settings
1. Go to https://api.slack.com/apps
2. Select your "Machinecraft In..." app
3. Go to "Event Subscriptions"

### 2. Set Request URL
1. Enable Events
2. Set Request URL to: `https://your-app-name.railway.app/slack/events`
3. Slack will verify the URL automatically

### 3. Subscribe to Events
Add these events:
- `message.channels`
- `message.groups` 
- `message.im`

### 4. Save Changes
Click "Save Changes" - your bot is now live!

## ✅ Test Your Bot

### 1. Add Bot to Channel
In Slack, type: `/invite @Machinecraft Inventory Bot`

### 2. Test Commands
```
inventory summary
inventory servo motors
inventory mitsubishi
inventory expensive items
```

## 💰 Railway Pricing
- **Free tier**: 500 hours/month (enough for 24/7 operation)
- **Pro tier**: $5/month for unlimited usage
- **No credit card required** for free tier

## 🔄 Updates
When you push code to GitHub, Railway automatically redeploys your bot!

## 🆘 Troubleshooting

### Bot Not Responding
1. Check Railway logs: Go to "Deployments" → "View Logs"
2. Verify environment variables are set
3. Check Slack Event Subscriptions are enabled

### Database Issues
1. Ensure database file is uploaded to Railway Storage
2. Check file permissions
3. Verify database path in environment variables

### Slack API Errors
1. Verify bot token is correct
2. Check bot permissions in Slack App settings
3. Ensure Event Subscriptions are properly configured

## 🎯 Benefits of Railway
✅ **No server setup** - Just push code and deploy  
✅ **Automatic scaling** - Handles traffic spikes  
✅ **Built-in monitoring** - View logs and metrics  
✅ **Free tier** - Perfect for testing and small teams  
✅ **Easy updates** - Git push = automatic deploy  
✅ **Custom domains** - Add your own domain later  

## 🚀 Alternative: Railway CLI (Advanced)

If you prefer command line:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy from current directory
railway up

# Set environment variables
railway variables set SLACK_BOT_TOKEN=your-slack-bot-token-here
railway variables set SLACK_SIGNING_SECRET=6455ad30866671dad55a6eda3666d87c

# View logs
railway logs
```

---

## 🎉 That's It!

Your Machinecraft Inventory Slack Bot will be running 24/7 on Railway with:
- **10.5M+ inventory items** searchable
- **Real-time Slack integration**
- **Automatic scaling**
- **Zero server maintenance**

**No server needed - Railway handles everything!** 🚀

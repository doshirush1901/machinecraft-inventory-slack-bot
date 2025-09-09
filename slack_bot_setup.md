# Machinecraft Inventory Slack Bot Setup

## 🚀 Quick Start

### 1. Create a Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Machinecraft Inventory Bot"
4. Select your workspace

### 2. Configure Bot Permissions
1. Go to "OAuth & Permissions"
2. Add these Bot Token Scopes:
   - `chat:write` - Send messages
   - `channels:read` - Read channel info
   - `groups:read` - Read private channels
   - `im:read` - Read direct messages
   - `mpim:read` - Read group messages

### 3. Install App to Workspace
1. Click "Install to Workspace"
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 4. Set Environment Variable
```bash
export SLACK_BOT_TOKEN="xoxb-your-token-here"
```

### 5. Run the Bot
```bash
python3 slack_inventory_bot.py
```

## 💬 Usage Examples

### Basic Commands
- `inventory servo motors` - Find servo motors
- `inventory expensive items` - High-value items (₹10K+)
- `inventory mitsubishi` - All Mitsubishi products
- `inventory out of stock` - Items needing reorder
- `inventory pneumatic components` - FESTO/SMC items
- `inventory electrical components` - Eaton/Siemens parts
- `inventory cables` - LAPP/Phoenix cables
- `inventory summary` - Overall inventory stats

### Natural Language Search
- "Show me servo motors"
- "What expensive items do we have?"
- "Find Mitsubishi products"
- "What's out of stock?"
- "Search for pneumatic components"

## 🎯 Features

### ✅ What Works Now
- **Natural language search** through 10.5M+ items
- **Real-time inventory data** from your Silver database
- **Visual results** with icons and status indicators
- **Price and stock information** in INR
- **Brand and category filtering**

### 🔧 Bot Responses Include
- **Part numbers** and descriptions
- **Pricing** in Indian Rupees
- **Stock levels** with status indicators
- **Brand information**
- **Total inventory values**
- **Visual icons** for easy identification

## 📊 Sample Output

```
⚙️ Servo Motors
Found 10 items • Total Value: ₹6,751,400.00

🏭 HG-SR7024B
Contactor 9A, with 1NO+1NC, 230V AC Coil Voltage
Price: ₹245,400.00 | Stock: ✅ 5 units | Brand: Mitsubishi | Total Value: ₹1,227,000.00

🔧 MR-J4-200B4
Servo Amplifier 200W
Price: ₹143,400.00 | Stock: ✅ 11 units | Brand: Mitsubishi | Total Value: ₹1,577,400.00
```

## 🛠️ Advanced Setup (Optional)

### Enable Events API
1. Go to "Event Subscriptions"
2. Enable Events
3. Subscribe to `message.channels` and `message.groups`
4. Set Request URL to your server endpoint

### Add Interactive Components
1. Go to "Interactive Components"
2. Enable Interactivity
3. Set Request URL to your server endpoint

## 🔒 Security Notes

- Keep your bot token secure
- Use environment variables for tokens
- Consider IP whitelisting for production
- Monitor bot usage and permissions

## 📈 Next Steps

1. **Deploy to server** for 24/7 availability
2. **Add web scraping** for real-time supplier data
3. **Integrate with procurement** systems
4. **Add approval workflows** for high-value items
5. **Create automated alerts** for low stock

## 🆘 Troubleshooting

### Bot Not Responding
- Check if bot token is set correctly
- Verify bot is added to the channel
- Check bot permissions

### No Search Results
- Verify database file exists
- Check database connection
- Ensure data is properly loaded

### Permission Errors
- Reinstall app to workspace
- Check OAuth scopes
- Verify bot is in the channel

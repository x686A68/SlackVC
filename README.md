# SlackVC

Vibe code from Slack. Send a message in a Slack channel and Claude Code runs it on your server — no IDE required.

## How it works

```
You (Slack) → Slack Bot → Claude Code CLI → results back to Slack
```

Each Slack channel maps to a local project directory. Claude Code runs in headless mode, maintains conversation history per channel, and sends results back to the channel.

## Requirements

- Python 3.11+
- [Claude Code](https://claude.ai/code) installed and authenticated
- A Slack App with Socket Mode enabled

## Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. **Socket Mode** → Enable Socket Mode → generate an **App-Level Token** (`xapp-...`)
3. **OAuth & Permissions** → Bot Token Scopes → add:
   - `app_mentions:read`
   - `chat:write`
4. **Event Subscriptions** → Subscribe to Bot Events → add:
   - `app_mention`
5. **App Home** → Show Tabs → enable **Messages Tab** and **Allow users to send Slash commands and messages from the messages tab**
6. **Install to Workspace** → copy the **Bot User OAuth Token** (`xoxb-...`)
7. **Basic Information** → App Credentials → copy the **Signing Secret**

### 2. Configure the bot

```bash
git clone https://github.com/YOUR_USERNAME/SlackVC.git
cd SlackVC
pip install slack-bolt python-dotenv certifi
```

Copy and fill in the env file:
```bash
cp .env.example .env
```

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
```

Copy and fill in the channel config:
```bash
cp channels.example.json channels.json
```

```json
{
  "C0XXXXXXXXX": "/path/to/your/project"
}
```

The channel ID can be found by right-clicking a channel in Slack → **Copy link** — it's the last segment of the URL (starts with `C`).

### 3. Run

```bash
python3 bot.py
```

## Usage

In any configured channel, **@ mention** the bot with your request:

```
@ClaudeCode write a sorting algorithm in test.py
@ClaudeCode add unit tests for the sort function
@ClaudeCode run the tests and show me the results
```

Claude Code will execute in the mapped project directory and reply in the channel. Conversation history is maintained per channel — Claude remembers context across messages.

To start a fresh conversation:
```
@ClaudeCode new session
```

## Deploying to a server

Since the bot uses Socket Mode (outbound WebSocket), no open ports or domain name are needed. Just run `bot.py` on any machine with Claude Code installed.

```bash
# Run in the background with nohup
nohup python3 bot.py > bot.log 2>&1 &
```

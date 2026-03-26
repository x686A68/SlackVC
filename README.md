# SlackVC

Vibe code from Slack. Send a message in a Slack channel and Claude Code runs it on your machine — no IDE required.

## How it works

```
You (Slack) → Slack Bot → Claude Code CLI → results back to Slack
```

Each Slack channel maps to a local project directory. Claude Code runs in headless mode, maintains conversation history per channel, and sends results back to the channel.

## Requirements

- Python 3.11+
- [Claude Code](https://claude.ai/code) installed and authenticated
- A Slack workspace where you have permission to install apps

## Environment setup

### Python

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip tmux

# macOS
brew install python tmux
```

### Dependencies

```bash
pip install slack-bolt python-dotenv certifi
```

## Setup

### 1. Create a Slack App (one click)

[![Create Slack App](https://img.shields.io/badge/Create%20Slack%20App-4A154B?style=for-the-badge&logo=slack&logoColor=white)](https://api.slack.com/apps?new_app=1&manifest_json=%7B%22display_information%22%3A%7B%22name%22%3A%22SlackVC%22%2C%22description%22%3A%22Vibe%20code%20from%20Slack%20using%20Claude%20Code%22%2C%22background_color%22%3A%22%231a1a2e%22%7D%2C%22features%22%3A%7B%22app_home%22%3A%7B%22home_tab_enabled%22%3Afalse%2C%22messages_tab_enabled%22%3Atrue%2C%22messages_tab_read_only_enabled%22%3Afalse%7D%2C%22bot_user%22%3A%7B%22display_name%22%3A%22SlackVC%22%2C%22always_online%22%3Atrue%7D%7D%2C%22oauth_config%22%3A%7B%22scopes%22%3A%7B%22bot%22%3A%5B%22app_mentions%3Aread%22%2C%22chat%3Awrite%22%2C%22channels%3Ahistory%22%2C%22im%3Ahistory%22%2C%22im%3Awrite%22%5D%7D%7D%2C%22settings%22%3A%7B%22event_subscriptions%22%3A%7B%22bot_events%22%3A%5B%22app_mention%22%2C%22message.im%22%5D%7D%2C%22interactivity%22%3A%7B%22is_enabled%22%3Afalse%7D%2C%22org_deploy_enabled%22%3Afalse%2C%22socket_mode_enabled%22%3Atrue%2C%22token_rotation_enabled%22%3Afalse%7D%7D)

Or manually:
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From a manifest**
2. Paste the contents of `manifest.json` from this repo

Then collect your three tokens:
- **Basic Information** → App Credentials → **Signing Secret**
- **OAuth & Permissions** → Install to Workspace → **Bot User OAuth Token** (`xoxb-...`)
- **Socket Mode** → Enable Socket Mode → generate an **App-Level Token** (`xapp-...`)

### 2. Configure the bot

```bash
git clone https://github.com/x686A68/SlackVC.git
cd SlackVC
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
tmux new -s slackvc
python3 bot.py
# Detach: Ctrl+B, then D
```

## Usage

In any configured channel, **@ mention** the bot with your request:

```
@SlackVC write a sorting algorithm in test.py
@SlackVC add unit tests for the sort function
@SlackVC run the tests and show me the results
```

Claude Code executes in the mapped project directory and replies in the channel. Conversation history is maintained per channel — Claude remembers context across messages.

To start a fresh conversation:
```
@SlackVC new session
```

## Deploying to a server

Since the bot uses Socket Mode (outbound WebSocket), no open ports or domain name are needed. Just run `bot.py` on any machine with Claude Code installed.

### Keep the bot running with tmux

`tmux` lets you run the bot in the background — it keeps running even after you close your terminal or IDE.

```bash
# Install tmux if not already installed
sudo apt install tmux   # Ubuntu/Debian
brew install tmux       # macOS

# Create a named session and start the bot
tmux new -s slackvc
python3 bot.py

# Detach from the session (bot keeps running): Ctrl+B, then D

# Later, reconnect to see logs
tmux attach -t slackvc

# Stop the bot
tmux kill-session -t slackvc
```

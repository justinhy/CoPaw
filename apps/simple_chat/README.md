# Simple Chat - CoPaw DesktopChannel POC

A minimal chat application to demonstrate and verify CoPaw's DesktopChannel functionality.

## Features

- Simple PyQt6 chat window
- WebSocket connection to CoPaw server
- Send/receive text messages
- Connection status indicator

## Installation

```bash
pip install -e .
```

## Usage

### 1. Start CoPaw Server

First, you need to start the CoPaw server. You can do this in two ways:

#### Option A: Install CoPaw (recommended)
```bash
# Install CoPaw
pip install copaw

# Initialize with defaults
copaw init --defaults

# Start CoPaw server
copaw app
```

#### Option B: Use Docker
```bash
# Pull and run CoPaw in Docker
docker run -p 127.0.0.1:8088:8088 -v copaw-data:/app/working agentscope/copaw:latest copaw app
```

The server will start at **http://127.0.0.1:8088/**

### 2. Configure API Key

Before using Simple Chat, you need to configure an API key for the AI model:

1. Open **http://127.0.0.1:8088/** in your browser
2. Click on "Providers" in the left sidebar
3. Add a provider (e.g., OpenAI, Alibaba Cloud, Ollama)
4. Enter your API key and base URL
5. Click "Save"

**Example configurations:**

- **OpenAI**: 
  - API Key: `sk-...`
  - Base URL: `https://api.openai.com/v1`
  
- **Alibaba Cloud (DashScope)**:
  - API Key: `sk-...` (from https://dashscope.console.aliyun.com/)
  - Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`

- **Ollama (local)**:
  - API Key: `ollama`
  - Base URL: `http://localhost:11434/v1`

### 3. Run Simple Chat

```bash
simple-chat
```

### 4. Connect and Chat

1. Click **"Connect"** button
   - Status should change to **"Connected"**
   - Color should turn green

2. Type a message in the input box

3. Click **"Send"** button or press **Enter**

4. Wait for CoPaw's response
   - Response will appear in the chat display

## Connection Details

**WebSocket URL**: `ws://127.0.0.1:8088/desktop/ws`

**Protocol**:
- Client → Server: `{"type": "text", "content": "..."}`
- Server → Client: `{"type": "text_chunk", "content": "...", "is_final": bool}`

## Development

This is a proof-of-concept application for testing:
- DesktopChannel WebSocket endpoint
- Message serialization/deserialization
- Basic PyQt6 widgets

## Architecture

```
simple_chat/
├── __init__.py
├── main.py            # Entry point
├── chat_window.py    # PyQt6 window
└── channel_client.py  # WebSocket client
```

## Testing Checklist

- [ ] CoPaw server is running at http://127.0.0.1:8088/
- [ ] API key is configured in CoPaw Console
- [ ] Simple Chat connects successfully
- [ ] Can send text messages
- [ ] Can receive text responses
- [ ] Connection status updates correctly

## Troubleshooting

### Connection Failed
- Check if CoPaw server is running: `copaw app`
- Verify server is accessible: Open http://127.0.0.1:8088/ in browser
- Check logs for errors

### No Response from CoPaw
- Verify API key is configured in CoPaw Console
- Check if provider/model is selected
- Look at CoPaw server logs for errors

### Docker Issues
If running CoPaw in Docker:
- Ensure port 8088 is mapped correctly
- For local models (Ollama), use `http://host.docker.internal:11434/v1`

## Requirements

- Python 3.10+
- PyQt6
- websockets
- CoPaw server running (with configured API key)

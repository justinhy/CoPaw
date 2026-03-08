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

1. Start CoPaw server:
```bash
copaw app
```

2. Run Simple Chat:
```bash
simple-chat
```

3. Connect to server:
   - Click "Connect" button
   - Status should change to "Connected"

4. Send messages:
   - Type message in input box
   - Click "Send" button
   - Message appears in chat display

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

## Testing

1. Start CoPaw server
2. Launch Simple Chat
3. Verify connection
4. Send test messages
5. Check message display

## Requirements

- Python 3.10+
- PyQt6
- websockets
- CoPaw server running

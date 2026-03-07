# CoPaw Desktop

> Cross-platform AI Voice Companion Desktop Application for CoPaw

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

CoPaw Desktop is a full-featured desktop client for [CoPaw](https://github.com/agentscope-ai/CoPaw), providing voice interaction, chat interface, and dynamic content rendering capabilities.

### Key Features

- 🎤 **Always-on Microphone** with VAD (Voice Activity Detection)
- 🗣️ **Voice-to-Text** using cloud ASR services
- 🤖 **CoPaw Integration** via custom WebSocket channel
- 💬 **Chat Interface** with message bubbles and streaming responses
- 📊 **Dynamic Content** rendering (images, charts, markdown)
- 💾 **Session Management** with SQLite storage
- 🌐 **Cross-platform** support (Ubuntu & Windows)

## Screenshots

_Coming soon after feat-006 implementation_

## Quick Start

### Prerequisites

- Python 3.10 or higher
- CoPaw server running (see [CoPaw documentation](https://copaw.agentscope.io))

### Installation

#### Linux / macOS

```bash
# Clone the repository
git clone https://github.com/agentscope-ai/CoPaw.git
cd CoPaw/apps/copaw_desktop

# Initialize environment
./init.sh

# Activate virtual environment
source venv/bin/activate

# Run the application
python src/copaw_desktop/main.py
```

#### Windows

```powershell
# Clone the repository
git clone https://github.com/agentscope-ai/CoPaw.git
cd CoPaw\apps\copaw_desktop

# Initialize environment
.\init.ps1

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the application
python src\copaw_desktop\main.py
```

### Configuration

Create a `.env` file in the project root:

```bash
# CoPaw server endpoint
COPAW_WS_URL=ws://127.0.0.1:8088/ws/desktop

# Cloud ASR credentials (choose one)
DASHSCOPE_API_KEY=your-api-key-here
# or
OPENAI_API_KEY=your-api-key-here

# Database path (optional)
COPAW_DB_PATH=~/.copaw_desktop/sessions.db
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/copaw_desktop --cov-report=html

# Run specific test category
pytest tests/ -m unit
pytest tests/ -m "not slow"
```

### Code Quality

```bash
# Format code
black src/ tests/

# Check code style
flake8 src/ tests/

# Type checking
mypy src/
```

### Development Methodology

This project follows **Test-Driven Development (TDD)** with discrete session workflow:

1. Each feature has a corresponding test file
2. Tests are written before implementation
3. Features are marked as `passes: true` only after tests pass
4. Progress is tracked in `feature_list.json` and `claude-progress.txt`

See [app_spec.txt](app_spec.txt) for detailed architecture and [feature_list.json](feature_list.json) for development roadmap.

## Project Structure

```
copaw_desktop/
├── src/copaw_desktop/
│   ├── core/           # Core engine (audio, network, database)
│   ├── gui/            # PyQt6 GUI components
│   ├── utils/          # Helper functions
│   └── main.py         # Application entry point
├── tests/              # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── gui/            # GUI tests
├── scripts/            # Build and deployment scripts
├── feature_list.json   # Development roadmap (single source of truth)
├── claude-progress.txt # Session logs
├── app_spec.txt        # Architecture specification
├── init.sh             # Linux/macOS setup script
├── init.ps1            # Windows setup script
└── README.md           # This file
```

## Architecture

CoPaw Desktop follows **MVVM (Model-View-ViewModel)** pattern with clean architecture:

```
┌─────────────────────────────────────┐
│     PyQt6 GUI Layer (View)          │
└────────────┬────────────────────────┘
             │ Signals/Slots
┌────────────┴────────────────────────┐
│  Application Core (ViewModel)       │
│  - State Manager                    │
│  - Message Bus                      │
└────────────┬────────────────────────┘
             │
┌────────────┴────────────────────────┐
│     Core Engine (Model)             │
│  - Audio Pipeline (VAD)             │
│  - Cloud Services (ASR/TTS)         │
│  - Network Layer (WebSocket)        │
│  - Data Layer (SQLite)              │
└────────────┬────────────────────────┘
             │ WebSocket Protocol
┌────────────┴────────────────────────┐
│   CoPaw Server (DesktopChannel)     │
└─────────────────────────────────────┘
```

For detailed architecture documentation, see [app_spec.txt](app_spec.txt).

## Roadmap

### Phase 1: Foundation (feat-001 to feat-003)
- [ ] DesktopChannel implementation in CoPaw core
- [ ] WebSocket client with auto-reconnect
- [ ] SQLite session storage

### Phase 2: Cloud Services (feat-004 to feat-005)
- [ ] Cloud ASR integration
- [ ] Cloud TTS integration

### Phase 3: GUI Framework (feat-006 to feat-010)
- [ ] Main window with 3-column layout
- [ ] Session list panel
- [ ] Chat panel with message bubbles
- [ ] Dynamic content panel (images, charts)

### Phase 4: Integration (feat-011 to feat-012)
- [ ] Audio recorder with VAD
- [ ] Full pipeline integration

See [feature_list.json](feature_list.json) for detailed feature specifications.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat-XXX-feature-name`)
3. Write tests first (TDD approach)
4. Implement the feature
5. Ensure all tests pass (`pytest tests/`)
6. Run code quality checks (`black`, `flake8`, `mypy`)
7. Commit with descriptive message
8. Push to your branch
9. Open a Pull Request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.

## Acknowledgments

- [CoPaw](https://github.com/agentscope-ai/CoPaw) - The AI assistant framework
- [AgentScope Team](https://github.com/agentscope-ai) - For creating and maintaining CoPaw
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [edge-tts](https://github.com/rany2/edge-tts) - Free TTS service

## Support

- 📖 [Documentation](https://copaw.agentscope.io)
- 🐛 [Issue Tracker](https://github.com/agentscope-ai/CoPaw/issues)
- 💬 [Discord](https://discord.gg/eYMpfnkG8h)
- 📧 [Email](mailto:agentscope@alibaba-inc.com)

---

**Built with ❤️ by the AgentScope Team**

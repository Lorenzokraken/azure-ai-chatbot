# 🐙 KrakenGPT - Multi-Provider AI Chatbot

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0%2B-green)
![React](https://img.shields.io/badge/React-18.2.0-blue)

**KrakenGPT** is a sophisticated multi-provider chatbot application that supports Azure OpenAI, OpenRouter, and Local AI servers, providing an intelligent conversational experience with advanced project management and enhanced markdown rendering.

## 🌟 Features

### 🤖 **Multi-Provider AI Support**
- **Azure OpenAI** - Enterprise-grade models (GPT-4, GPT-3.5-turbo)
- **OpenRouter** - Access to free AI models with dynamic loading
- **Local AI** - Connect to your local AI server (LM Studio, Ollama, etc.)
- **Automatic Provider Switching** - Seamless failover between providers

### 💬 **Enhanced Chat Experience**
- **Modern ChatGPT-like UI** with responsive dark theme
- **Advanced Markdown Rendering** with syntax highlighting
- **Code Block Features** - Copy buttons, language detection, line numbers
- **Real-time Streaming** responses with typing indicators
- **Stop Generation** button to interrupt long responses
- **Response Timer** to track generation speed

### 📁 **Project Management**
- **Organize Conversations** into projects with custom names
- **Custom System Prompts** per project for specialized behavior
- **RAG Context Support** - Enhance responses with document context
- **Chat History** - Persistent conversation storage

### ⚙️ **Advanced Configuration**
- **Dynamic Model Loading** from OpenRouter API
- **Settings Persistence** - Remember your preferred provider/model
- **Temperature & Token Control** - Fine-tune AI responses
- **Multiple Model Selection** per provider

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- At least one AI provider configured (Azure OpenAI, OpenRouter, or Local)

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/Lorenzokraken/azure-ai-chatbot.git
cd azure-ai-chatbot
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:

#### Azure OpenAI Configuration
```env
# Azure OpenAI (Enterprise)
AZURE_DEPLOYMENT_NAME=gpt-4
AZURE_ENDPOINT=https://your-azure-endpoint.openai.azure.com/
AZURE_API_KEY=your-azure-api-key
```

#### OpenRouter Configuration  
```env
# OpenRouter (Free Models)
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
OPENROUTER_MODELS=https://openrouter.ai/api/v1/models
```

#### Local AI Server Configuration
```env
# Local AI Server (LM Studio, Ollama, etc.)
LOCAL_ENDPOINT=http://localhost:1234/v1/chat/completions
LOCAL_MODEL=qwen/qwen3-4b-thinking-2507
```

4. Run the backend:

```bash
py main.py
```

### Frontend Setup

1. Navigate to the React frontend:

```bash
cd react-frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm start
```

The application will be available at `http://localhost:3000`.

## 🛠️ Architecture

### Backend (FastAPI)

- **API Layer**: FastAPI server with CORS support and request logging
- **Database**: SQLite for project and chat persistence  
- **AI Providers**: Multi-provider support (Azure, OpenRouter, Local)
- **Dynamic Model Loading**: Real-time model discovery from OpenRouter API
- **Streaming Support**: Server-sent events for real-time responses

### Frontend (React)

- **UI Framework**: React 18 with hooks and modern patterns
- **State Management**: Local state with localStorage persistence
- **Markdown Rendering**: Enhanced with syntax highlighting and code copy
- **Responsive Design**: Mobile-friendly dark theme interface

## 📚 API Documentation

### Core Endpoints

- `GET /` - Application home page
- `GET /models` - Get available models for all providers
- `GET /providers` - Get provider status and configuration
- `POST /v1/chat/completions` - Send chat completion request

### Project Management

- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get specific project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Chat Management

- `GET /api/projects/{id}/chats` - Get chats for project
- `POST /api/chats` - Create new chat
- `GET /api/chats/{id}` - Get specific chat
- `PUT /api/chats/{id}` - Update chat
- `DELETE /api/chats/{id}` - Delete chat

## 🔧 Configuration Guide

### Environment Variables Reference

#### Required for Azure OpenAI
```env
AZURE_DEPLOYMENT_NAME=gpt-4          # Your deployment name
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_API_KEY=your-api-key           # Your Azure API key
```

#### Required for OpenRouter
```env
OPENROUTER_API_KEY=your-key          # Get from openrouter.ai
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
OPENROUTER_MODELS=https://openrouter.ai/api/v1/models
```

#### Required for Local AI
```env
LOCAL_ENDPOINT=http://localhost:1234/v1/chat/completions
LOCAL_MODEL=your-model-name          # e.g., llama-3.2-3b-instruct
```

#### Optional Configuration
```env
DEFAULT_PROVIDER=azure               # Default: azure
MAX_TOKENS=4096                      # Default: 4096  
TEMPERATURE=0.7                      # Default: 0.7
```

### Provider Setup Instructions

#### Azure OpenAI Setup
1. Create an Azure OpenAI resource in the Azure portal
2. Deploy a model (GPT-4 or GPT-3.5-turbo recommended)
3. Get your endpoint and API key from the Azure portal
4. Update the `.env` file with your credentials

#### OpenRouter Setup  
1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Get your API key from the dashboard
3. Update the `.env` file with your OpenRouter API key
4. The app will automatically discover free models

#### Local AI Setup (LM Studio)
1. Download [LM Studio](https://lmstudio.ai/)
2. Download and load a model (Qwen, Llama, etc.)
3. Start the local server (usually on port 1234)
4. Update `.env` with your local endpoint and model name

#### Local AI Setup (Ollama)
1. Install [Ollama](https://ollama.com/)
2. Pull a model: `ollama pull llama3.2:3b`
3. Serve with OpenAI-compatible API: `ollama serve`
4. Update `.env` with endpoint `http://localhost:11434/v1/chat/completions`
## 🎯 Key Features Deep Dive

### 🤖 Multi-Provider Support

**Azure OpenAI Integration**
- Enterprise-grade security and reliability
- Support for GPT-4, GPT-3.5-turbo models
- Advanced configuration options

**OpenRouter Integration**  
- Dynamic model discovery via API
- Automatic filtering for free models
- 59+ free models available (auto-updated)

**Local AI Server Support**
- Connect to LM Studio, Ollama, or custom servers
- Full control over your data and models
- Offline capability

### 💎 Enhanced User Experience

**Advanced Markdown Rendering**
- Syntax highlighting for 100+ programming languages
- Code copy buttons with visual feedback
- Professional dark theme styling
- Enhanced headers, tables, lists, and blockquotes

**Smart Chat Features**
- Stop generation button for long responses
- Response time tracking
- Streaming with typing indicators
- Settings persistence across sessions

**Project Management**
- Organize conversations by topic/project
- Custom system prompts per project
- RAG context integration
- Persistent chat history

## 🔧 Supported Models & Providers

### Azure OpenAI Models
```
gpt-4 (recommended)
gpt-35-turbo  
gpt-4-turbo
Your custom deployments
```

### OpenRouter Free Models (Auto-Updated)
```
mistralai/mistral-7b-instruct:free
google/gemma-2-9b-it:free
meta-llama/llama-3.1-8b-instruct:free
microsoft/phi-3-mini-128k-instruct:free
qwen/qwen-2-7b-instruct:free
+ 50+ more models (automatically discovered)
```

### Local AI Models
```
Any model compatible with OpenAI Chat Completions API
Popular choices: Llama, Qwen, Mistral, CodeLlama, etc.
```

## � Advanced Usage

### Custom System Prompts
```javascript
// Example project system prompt
"You are a senior Python developer. Provide detailed, 
production-ready code with error handling and best practices."
```

### RAG Context Integration
```javascript
// Add context to enhance responses
"Context: This project uses FastAPI with SQLite database..."
```

### API Usage Examples

**Get Available Models**
```bash
curl http://localhost:8000/models
```

**Get Provider Status**  
```bash
curl http://localhost:8000/providers
```

**Send Chat Message**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "provider": "azure",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 🛠️ Troubleshooting

### Common Issues

**Backend won't start on port 8000**
```bash
# Check what's using the port
netstat -ano | findstr :8000
# Kill the process if needed
taskkill /F /PID <process_id>
```

**OpenRouter models not loading**
- Verify your API key is correct
- Check internet connection
- API key should start with "sk-or-"

**Local AI connection fails**
- Ensure your local server is running
- Check the endpoint URL and port
- Verify the model name matches exactly

### Environment Variables Validation
```bash
# Test your configuration
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Azure Key:', '✓' if os.getenv('AZURE_API_KEY') else '✗')
print('OpenRouter Key:', '✓' if os.getenv('OPENROUTER_API_KEY') else '✗')
print('Local Endpoint:', os.getenv('LOCAL_ENDPOINT', 'Not set'))
"
```

## 🏆 Performance & Features

- **Fast Response Times** - Optimized API calls and streaming
- **Memory Efficient** - SQLite database with minimal overhead  
- **Scalable Architecture** - Easy to add new providers/models
- **Production Ready** - Error handling, logging, CORS support
- **Mobile Responsive** - Works on all devices
- **Offline Capable** - With local AI providers

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- New AI provider integrations
- UI/UX enhancements  
- Performance optimizations
- Additional markdown features
- Mobile app development
- Docker containerization

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Azure OpenAI** - Enterprise AI services
- **OpenRouter** - Free AI model access
- **FastAPI** - Modern Python web framework
- **React** - Frontend framework
- **Prism.js** - Syntax highlighting
- **React Markdown** - Markdown rendering

---

<div align="center">

**🐙 KrakenGPT - Unleash the Power of Multi-Provider AI**

Made with ❤️ by [Lorenzo Kraken](https://github.com/Lorenzokraken)

[⭐ Star this repo](https://github.com/Lorenzokraken/azure-ai-chatbot) • [🐛 Report Bug](https://github.com/Lorenzokraken/azure-ai-chatbot/issues) • [💡 Request Feature](https://github.com/Lorenzokraken/azure-ai-chatbot/issues)

</div>
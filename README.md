# 🐙 KrakenGPT - Azure AI Chatbot

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0%2B-green)
![React](https://img.shields.io/badge/React-18.2.0-blue)

**KrakenGPT** is a sophisticated chatbot application that leverages Azure OpenAI and OpenRouter APIs to provide an intelligent conversational experience with project management capabilities and Retrieval-Augmented Generation (RAG) context support.

## 🌟 Features

- 💬 **Intelligent Chat Interface** - Beautiful ChatGPT-like UI with markdown rendering
- ☁️ **Dual Provider Support** - Seamlessly switch between Azure OpenAI and OpenRouter
- 📁 **Project Management** - Organize conversations into projects with custom prompts
- 📚 **RAG Context** - Enhance AI responses with custom context documents
- 🔄 **Streaming Responses** - Real-time response generation with typing indicators
- 🎨 **Modern UI/UX** - Responsive design with dark theme and smooth animations
- 🔧 **Advanced Settings** - Control temperature, max tokens, and model selection

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Azure OpenAI API key (or OpenRouter API key as fallback)

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
```env
AZURE_DEPLOYMENT_NAME=gpt-4.1
AZURE_ENDPOINT=https://your-azure-endpoint.openai.azure.com/
AZURE_API_KEY=your-azure-api-key

OPENROUTER_API_KEY=your-openrouter-api-key
```

4. Run the backend:
```bash
python main.py
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
- **API Layer**: FastAPI server with CORS support
- **Database**: SQLite for project and chat persistence
- **AI Providers**: Azure OpenAI and OpenRouter integration
- **Fallback System**: Automatic switching between providers

### Frontend (React)
- **UI Framework**: React 18 with hooks
- **State Management**: Built-in React state
- **Styling**: Custom CSS with ChatGPT-like dark theme
- **Markdown**: React Markdown with GFM support

## 🎯 Key Components

### Project Management
Organize your conversations into projects with:
- Custom project names and descriptions
- Project-specific system prompts
- Dedicated chat history

### RAG Context
Enhance AI responses by providing context:
- Add documents or information as context
- Context is automatically included in system prompts
- Perfect for domain-specific queries

### Provider Selection
Switch between AI providers:
- **Azure OpenAI** - Primary provider with GPT models
- **OpenRouter** - Fallback provider with free models
- Automatic fallback when one provider fails

## 🎨 UI/UX Highlights

- **Dark Theme** - Easy on the eyes with professional styling
- **Responsive Design** - Works on desktop and mobile devices
- **Smooth Animations** - Polished interactions and transitions
- **Floating Modals** - Non-intrusive dialog boxes
- **Emoji Integration** - Visual enhancements throughout the interface

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_DEPLOYMENT_NAME` | Azure model deployment name | Yes |
| `AZURE_ENDPOINT` | Azure OpenAI endpoint URL | Yes |
| `AZURE_API_KEY` | Azure OpenAI API key | Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key | Optional (fallback) |

### Supported Models

**Azure OpenAI:**
- `gpt-35-turbo`
- `gpt-4`
- `gpt-4.1`

**OpenRouter (Free Models):**
- `mistralai/mistral-7b-instruct:free`
- `google/gemma-7b-it:free`
- `meta-llama/llama-3.1-8b-instruct:free`
- `microsoft/phi-3-mini-128k-instruct:free`
- `openchat/openchat-7b:free`
- `neversleep/llama-3-lumimaid-8b:free`
- `sao10k/fimbulvetr-11b-v2:free`

## 📱 Mobile Support

The application features a fully responsive design:
- Collapsible sidebar on mobile devices
- Touch-friendly interface elements
- Optimized input areas for mobile typing
- Adaptive layouts for all screen sizes

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Azure OpenAI](https://azure.microsoft.com/en-us/services/cognitive-services/openai-service/)
- [OpenRouter](https://openrouter.ai/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [SQLite](https://www.sqlite.org/)

## 📞 Support

If you encounter any issues or have questions, please file an issue on GitHub.

---

<p align="center">
  Made with 🐙 by Lorenzo Kraken
</p>
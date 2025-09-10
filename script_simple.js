// Configurazione
const API_CONFIG = {
    endpoint: "http://127.0.0.1:8000",
    model_name: "gpt-4.1",
    temperature: 0.7,
    max_tokens: 13107,
    provider: "azure"  // Default provider
};

// Elementi DOM
let chatMessages;
let userInput;
let sendButton;
let modelSelect;
let settingsBtn;
let settingsModal;
let closeModalBtn;

// Stato streaming
let currentBotMessageElement = null;
let currentBotMessageContent = "";

// Inizializzazione
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    loadSupportedModels();
    addEventListeners();
    addWelcomeMessage();
});

function initializeElements() {
    chatMessages = document.getElementById('chat-messages');
    userInput = document.getElementById('user-input');
    sendButton = document.getElementById('send-button');
    modelSelect = document.getElementById('model-select');
    settingsBtn = document.querySelector('.settings-btn');
    settingsModal = document.getElementById('settings-modal');
    closeModalBtn = settingsModal.querySelector('.close-btn');
}

// Carica modelli dal backend
async function loadSupportedModels() {
    try {
        const response = await fetch(`${API_CONFIG.endpoint}/models`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        const models = data.models;
        const providers = data.providers;
        const defaultProvider = data.default_provider;
        
        // Update provider selection
        const providerSelect = document.getElementById('provider-select');
        if (providerSelect) {
            providerSelect.innerHTML = '';
            providers.forEach(provider => {
                const opt = document.createElement('option');
                opt.value = provider;
                opt.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
                providerSelect.appendChild(opt);
            });
            providerSelect.value = defaultProvider;
        }
        
        // Update model selection based on default provider
        updateModelSelection(models, defaultProvider);
    } catch (err) {
        console.error("Errore caricamento modelli:", err);
        // Fallback to default model
        modelSelect.innerHTML = '';
        const opt = document.createElement('option');
        opt.value = "gpt-4.1";
        opt.textContent = "GPT-4.1";
        modelSelect.appendChild(opt);
        modelSelect.value = "gpt-4.1";
    }
}

function updateModelSelection(models, provider) {
    modelSelect.innerHTML = '';
    
    let providerModels = [];
    if (provider === 'azure') {
        providerModels = ["gpt-35-turbo", "gpt-4", "gpt-4.1"];
    } else if (provider === 'openrouter') {
        providerModels = [
            "mistralai/mistral-7b-instruct:free",
            "google/gemma-7b-it:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "openchat/openchat-7b:free",
            "neversleep/llama-3-lumimaid-8b:free",
            "sao10k/fimbulvetr-11b-v2:free"
        ];
    }
    
    providerModels.forEach(model => {
        const opt = document.createElement('option');
        opt.value = model;
        opt.textContent = formatModelName(model);
        modelSelect.appendChild(opt);
    });
    
    // Set default model based on provider
    if (provider === 'azure') {
        modelSelect.value = "gpt-4.1";
    } else if (provider === 'openrouter') {
        modelSelect.value = "meta-llama/llama-3.1-8b-instruct:free";
    }
    
    // Update API config
    API_CONFIG.provider = provider;
    API_CONFIG.model_name = modelSelect.value;
}

function formatModelName(model) {
    const names = {
        "gpt-4.1": "GPT-4.1"
    };
    return names[model] || model;
}

// Event Listeners
function addEventListeners() {
    sendButton?.addEventListener('click', sendMessage);
    userInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    modelSelect?.addEventListener('change', (e) => {
        API_CONFIG.model_name = e.target.value;
    });

    settingsBtn?.addEventListener('click', () => {
        settingsModal.style.display = 'block';
        document.getElementById('temperature').value = API_CONFIG.temperature;
        document.getElementById('max-tokens').value = API_CONFIG.max_tokens;
        document.getElementById('temperature-value').textContent = API_CONFIG.temperature;
        document.getElementById('max-tokens-value').textContent = API_CONFIG.max_tokens;
        document.getElementById('provider-select').value = API_CONFIG.provider;
    });

    closeModalBtn?.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) settingsModal.style.display = 'none';
    });

    document.getElementById('save-settings')?.addEventListener('click', saveSettings);
    document.getElementById('cancel-settings')?.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });

    // Slider dinamici
    document.getElementById('temperature')?.addEventListener('input', (e) => {
        document.getElementById('temperature-value').textContent = e.target.value;
    });

    document.getElementById('max-tokens')?.addEventListener('input', (e) => {
        document.getElementById('max-tokens-value').textContent = e.target.value;
    });
    
    // Provider selection
    document.getElementById('provider-select')?.addEventListener('change', (e) => {
        const provider = e.target.value;
        // Update models based on selected provider
        updateModelSelection({}, provider);
    });
}

function saveSettings() {
    API_CONFIG.model_name = modelSelect.value;
    API_CONFIG.temperature = parseFloat(document.getElementById('temperature').value);
    API_CONFIG.max_tokens = parseInt(document.getElementById('max-tokens').value);
    API_CONFIG.provider = document.getElementById('provider-select').value;
    settingsModal.style.display = 'none';
    console.log("Impostazioni salvate:", API_CONFIG);
}

// Invio messaggio
function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessageToUI('user', text);
    userInput.value = '';
    showTypingIndicator();
    getBotResponse(text);
}

// UI Messaggi
function addMessageToUI(role, content) {
    // Rimuovi indicatore di digitazione
    document.querySelector('.enhanced-typing-indicator')?.remove();

    const div = document.createElement('div');
    div.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (role === 'bot' && isCodeContent(content)) {
        const pre = document.createElement('pre');
        const code = document.createElement('code');
        code.textContent = content.trim();
        pre.appendChild(code);

        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-button';
        copyBtn.textContent = 'Copy';
        copyBtn.onclick = () => copyCodeToClipboard(content, copyBtn);
        pre.appendChild(copyBtn);

        contentDiv.appendChild(pre);
    } else {
        contentDiv.innerHTML = formatMarkdown(content);
    }

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    div.appendChild(avatar);
    div.appendChild(contentDiv);
    if (role === 'bot') div.appendChild(timeDiv); // Solo per bot

    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return div;
}

// Helper
function isCodeContent(content) {
    const patterns = [
        /^\s*[\{\[\(\w]+\s*[=\{\[\(]/,
        /function\s+\w+\s*\(/,
        /(const|let)\s+\w+\s*=/,
        /class\s+\w+/,
        /import\s+.*\s+from/,
        /export\s+(default\s+)?(function|class|const|let)/,
        /\w+\s*\([^)]*\)\s*\{/,
        /```[\s\S]*```/
    ];
    return patterns.some(p => new RegExp(p).test(content));
}

function formatMarkdown(text) {
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/`(.*?)`/g, '<code>$1</code>');
    text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    text = text.replace(/^\s*\*\s+(.*$)/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

function copyCodeToClipboard(code, button) {
    navigator.clipboard.writeText(code).then(() => {
        const orig = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');
        setTimeout(() => {
            button.textContent = orig;
            button.classList.remove('copied');
        }, 2000);
    });
}

function showTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'enhanced-typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = '🤖';

    const text = document.createElement('div');
    text.className = 'typing-text';
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        text.appendChild(dot);
    }

    div.appendChild(avatar);
    div.appendChild(text);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Risposta Bot (Streaming)
async function getBotResponse(userMessage) {
    try {
        currentBotMessageElement = addMessageToUI('bot', '');
        currentBotMessageContent = "";
        const contentDiv = currentBotMessageElement.querySelector('.message-content');

        const response = await fetch(`${API_CONFIG.endpoint}/v1/chat/completions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: API_CONFIG.model_name,
                messages: [
                    { role: "system", content: "You are KrakenGPT, a helpful AI coding partner." },
                    { role: "user", content: userMessage }
                ],
                temperature: API_CONFIG.temperature,
                max_tokens: API_CONFIG.max_tokens,
                stream: true,
                provider: API_CONFIG.provider
            })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const jsonStr = line.slice(6);
                    if (jsonStr === "[DONE]") break;

                    try {
                        const data = JSON.parse(jsonStr);
                        const content = data.choices?.[0]?.delta?.content;
                        if (content) {
                            currentBotMessageContent += content;

                            if (isCodeContent(currentBotMessageContent)) {
                                let pre = contentDiv.querySelector('pre');
                                let code;
                                if (!pre) {
                                    pre = document.createElement('pre');
                                    code = document.createElement('code');
                                    pre.appendChild(code);
                                    const copyBtn = document.createElement('button');
                                    copyBtn.className = 'copy-button';
                                    copyBtn.textContent = 'Copy';
                                    copyBtn.onclick = () => copyCodeToClipboard(currentBotMessageContent, copyBtn);
                                    pre.appendChild(copyBtn);
                                    contentDiv.innerHTML = '';
                                    contentDiv.appendChild(pre);
                                } else {
                                    code = pre.querySelector('code');
                                }
                                code.textContent = currentBotMessageContent.trim();
                            } else {
                                contentDiv.innerHTML = formatMarkdown(currentBotMessageContent);
                            }

                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                    } catch (e) {
                        console.warn("Parse error:", e);
                    }
                }
            }
        }
    } catch (error) {
        console.error("Errore:", error);
        document.querySelector('.enhanced-typing-indicator')?.remove();
        if (currentBotMessageElement) {
            currentBotMessageElement.querySelector('.message-content').textContent = 
                "❌ Errore nella risposta. Riprova.";
        } else {
            addMessageToUI('bot', "❌ Errore. Riprova più tardi.");
        }
    } finally {
        currentBotMessageElement = null;
        currentBotMessageContent = "";
    }
}

// Messaggio di benvenuto
function addWelcomeMessage() {
    const msg = addMessageToUI('bot', `
# 🚀 Benvenuto in KrakenGPT!

Sono il tuo assistente AI per sviluppo software. Posso:

- ✍️ Scrivere e correggere codice
- 📚 Spiegare concetti complessi
- 🐞 Debuggare errori
- 📄 Generare documentazione

**Prova a chiedermi:**
\`\`\`js
// Scrivi una funzione che calcola il fattoriale
\`\`\`
    `);
    // Rimuovi il timestamp dal welcome message se preferisci
    msg.querySelector('.message-time')?.remove();
}
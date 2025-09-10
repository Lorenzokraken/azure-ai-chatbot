import React, { useState, useEffect, useRef } from 'react';
// Rimosso l'import di ReactMarkdown e remarkGfm
import MarkdownRenderer from './MarkdownRenderer'; // Importa il nuovo componente
import './style.css';

// Configurazione
const API_CONFIG = {
    endpoint: "/api", // Utilizza il proxy di React
    model_name: "gpt-4.1",
    temperature: 0.7,
    max_tokens: 13107
};

function App() {
    // Elementi DOM
    const chatMessagesRef = useRef(null);
    const userInputRef = useRef(null);
    const sendButtonRef = useRef(null);
    const modelSelectRef = useRef(null);
    
    // Stato
    const [userInput, setUserInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [isBotTyping, setIsBotTyping] = useState(false);
    const [settings, setSettings] = useState({
        model: API_CONFIG.model_name,
        temperature: API_CONFIG.temperature,
        maxTokens: API_CONFIG.max_tokens
    });
    const [showSettings, setShowSettings] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false); // Sidebar chiusa di default
    const [projects, setProjects] = useState([]);
    const [projectChats, setProjectChats] = useState([]); // Chat del progetto corrente
    const [independentChats, setIndependentChats] = useState([]); // Chat indipendenti
    const [currentProject, setCurrentProject] = useState(null);
    const [currentChat, setCurrentChat] = useState(null);
    const [showProjectForm, setShowProjectForm] = useState(false);
    const [editingProject, setEditingProject] = useState(null);
    const [projectForm, setProjectForm] = useState({
        name: '',
        description: '',
        prompt: ''
    });
    const [showChatForm, setShowChatForm] = useState(false);
    const [chatForm, setChatForm] = useState({
        title: '',
        projectId: null
    });
    const [showContextModal, setShowContextModal] = useState(false);
    const [currentContext, setCurrentContext] = useState("");
    
    // Stato streaming
    const [currentBotMessage, setCurrentBotMessage] = useState('');
    
    // Inizializzazione
    
    // Carica progetti dal backend
    async function loadProjects() {
        try {
            const response = await fetch('/api/projects');
            if (response.ok) {
                const data = await response.json();
                setProjects(data);
                if (data.length > 0) {
                    setCurrentProject(data[0]);
                    loadChats(data[0].id);
                }
            }
        } catch (err) {
            console.error("Errore caricamento progetti:", err);
        }
    }
    
    // Carica chat per un progetto
    async function loadChats(projectId) {
        try {
            const response = await fetch(`/api/projects/${projectId}/chats`);
            if (response.ok) {
                const data = await response.json();
                setProjectChats(data);
            }
        } catch (err) {
            console.error("Errore caricamento chat:", err);
        }
    }
    
    // Carica messaggi di una chat specifica
    async function loadChatMessages(chatId) {
        try {
            const response = await fetch(`/api/chats/${chatId}`);
            if (response.ok) {
                const chat = await response.json();
                
                // Converti i timestamp da stringhe a oggetti Date
                // E converti i ruoli 'bot' in 'assistant' per compatibilità con Azure AI
                const messagesWithDates = (chat.messages || []).map(msg => ({
                    ...msg,
                    role: msg.role === 'bot' ? 'assistant' : msg.role,
                    timestamp: new Date(msg.timestamp)
                }));
                
                setMessages(messagesWithDates);
            }
        } catch (err) {
            console.error("Errore caricamento messaggi:", err);
        }
    }
    
    // Salva messaggi di una chat
    async function saveChatMessages(chatId, messages) {
        try {
            const response = await fetch(`/api/chats/${chatId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: messages })
            });
            
            if (!response.ok) {
                console.error("Errore salvataggio messaggi:", response.statusText);
            }
        } catch (err) {
            console.error("Errore salvataggio messaggi:", err);
        }
    }
    
    // Carica chat indipendenti (per ora vuoto, da implementare nel backend)
    async function loadIndependentChats() {
        try {
            // TODO: Implementare API per chat indipendenti nel backend
            // const response = await fetch('/api/independent-chats');
            // if (response.ok) {
            //     const data = await response.json();
            //     setIndependentChats(data);
            // }
            setIndependentChats([]);
        } catch (err) {
            console.error("Errore caricamento chat indipendenti:", err);
        }
    }
    
    // Inizializzazione
    useEffect(() => {
        loadSupportedModels();
        loadProjects();
        loadIndependentChats();
    }, []);
    
    // Apri form per nuovo progetto
    function openProjectForm(project = null) {
        if (project) {
            setEditingProject(project);
            setProjectForm({
                name: project.name,
                description: project.description || '',
                prompt: project.prompt || ''
            });
        } else {
            setEditingProject(null);
            setProjectForm({
                name: '',
                description: '',
                prompt: ''
            });
        }
        setShowProjectForm(true);
    }
    
    // Chiudi form progetto
    function closeProjectForm() {
        setShowProjectForm(false);
        setEditingProject(null);
        setProjectForm({
            name: '',
            description: '',
            prompt: ''
        });
    }
    
    // Salva progetto (crea o modifica)
    async function saveProject(e) {
        e.preventDefault();
        if (!projectForm.name.trim()) return;
        
        try {
            const url = editingProject ? `/api/projects/${editingProject.id}` : '/api/projects';
            const method = editingProject ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: projectForm.name.trim(),
                    description: projectForm.description.trim(),
                    prompt: projectForm.prompt.trim()
                })
            });
            
            if (response.ok) {
                const savedProject = await response.json();
                
                if (editingProject) {
                    // Aggiorna progetto esistente
                    setProjects(prev => prev.map(p => p.id === editingProject.id ? savedProject : p));
                    if (currentProject?.id === editingProject.id) {
                        setCurrentProject(savedProject);
                    }
                } else {
                    // Aggiungi nuovo progetto
                    setProjects(prev => [...prev, savedProject]);
                    setCurrentProject(savedProject);
                    setProjectChats([]);
                }
                
                closeProjectForm();
            }
        } catch (err) {
            console.error("Errore salvataggio progetto:", err);
        }
    }
    
    // Elimina progetto
    async function deleteProject(projectId) {
        if (!window.confirm("Sei sicuro di voler eliminare questo progetto?")) return;
        
        try {
            const response = await fetch(`/api/projects/${projectId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                setProjects(prev => prev.filter(p => p.id !== projectId));
                if (currentProject?.id === projectId) {
                    setCurrentProject(null);
                    setProjectChats([]);
                }
            }
        } catch (err) {
            console.error("Errore eliminazione progetto:", err);
        }
    }
    
    // Elimina chat
    async function deleteChat(chatId, isIndependent = false) {
        if (!window.confirm("Sei sicuro di voler eliminare questa chat? Questa azione non può essere annullata.")) return;
        
        try {
            const response = await fetch(`/api/chats/${chatId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                if (isIndependent) {
                    setIndependentChats(prev => prev.filter(c => c.id !== chatId));
                } else {
                    setProjectChats(prev => prev.filter(c => c.id !== chatId));
                }
                
                // Se la chat eliminata è quella corrente, deseleziona
                if (currentChat?.id === chatId) {
                    setCurrentChat(null);
                    setMessages([]);
                }
            }
        } catch (err) {
            console.error("Errore eliminazione chat:", err);
        }
    }
    
    // Apri form per nuova chat
    function openChatForm() {
        setChatForm({
            title: '',
            projectId: currentProject?.id || null
        });
        setShowChatForm(true);
    }
    
    // Chiudi form chat
    function closeChatForm() {
        setShowChatForm(false);
        setChatForm({
            title: '',
            projectId: null
        });
    }
    
    // Crea nuova chat
    async function createChat(e) {
        e.preventDefault();
        if (!chatForm.title.trim()) return;
        
        try {
            // Per ora, le chat indipendenti non sono supportate dal backend
            // Creiamo sempre una chat di progetto
            const projectId = chatForm.projectId || (projects.length > 0 ? projects[0].id : null);
            
            if (!projectId) {
                alert("Crea prima un progetto per poter creare chat!");
                return;
            }
            
            const response = await fetch('/api/chats', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    project_id: projectId, 
                    title: chatForm.title.trim(),
                    messages: []
                })
            });
            
            if (response.ok) {
                const newChat = await response.json();
                
                // Aggiorna la lista delle chat del progetto
                setProjectChats(prev => [...prev, newChat]);
                
                // Se è il progetto corrente, seleziona la chat
                if (currentProject?.id === projectId) {
                    setCurrentChat(newChat);
                    setMessages([]);
                }
                
                closeChatForm();
            }
        } catch (err) {
            console.error("Errore creazione chat:", err);
        }
    }
    
    // Salva il contesto della chat
    async function saveChatContext() {
        if (!currentChat) return;

        try {
            const response = await fetch(`/api/chats/${currentChat.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ context: currentContext })
            });

            if (response.ok) {
                const updatedChat = await response.json();
                // Aggiorna la chat corrente nello stato per riflettere il nuovo contesto
                setCurrentChat(updatedChat);
                // Aggiorna anche la lista delle chat
                if (updatedChat.project_id) {
                    setProjectChats(prev => prev.map(c => c.id === updatedChat.id ? updatedChat : c));
                } else {
                    setIndependentChats(prev => prev.map(c => c.id === updatedChat.id ? updatedChat : c));
                }
            }
        } catch (err) {
            console.error("Errore salvataggio contesto:", err);
        } finally {
            setShowContextModal(false);
        }
    }
    
    // Effetto per lo scroll automatico
    useEffect(() => {
        if (chatMessagesRef.current) {
            chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
        }
    }, [messages, isBotTyping]);
    
    // Carica modelli dal backend
    async function loadSupportedModels() {
        try {
            const response = await fetch('/models');
            if (response.ok) {
                const data = await response.json();
                console.log("Modelli supportati:", data.models);
            }
        } catch (err) {
            console.error("Errore caricamento modelli:", err);
        }
    }
    
    
    // Invio messaggio
    function sendMessage(e) {
        e.preventDefault();
        const text = userInput.trim();
        if (!text) return;
        
        // Aggiungi messaggio utente
        const userMsg = {
            id: Date.now(),
            role: 'user',
            content: text,
            timestamp: new Date()
        };
        
        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        setUserInput('');
        setIsBotTyping(true);
        setCurrentBotMessage('');
        
        // Salva i messaggi nel database se c'è una chat corrente
        if (currentChat) {
            saveChatMessages(currentChat.id, updatedMessages);
        }
        
        // Ottieni risposta del bot
        getBotResponse(updatedMessages);
    }
    
    // Risposta Bot (Streaming)
    async function getBotResponse(currentMessages) {
        try {
            console.log("Inviando richiesta al bot con modello:", settings.model);
            
            const systemMessage = `You are KrakenGPT, a helpful AI coding partner. Always format your responses using Markdown. For code blocks, use triple backticks (\`\`\`) and specify the language.`;
            const context = currentChat?.context || "";
            const systemMessageWithContext = context 
                ? `${systemMessage}\n\n--- CONTEXT ---\n${context}\n--- END CONTEXT ---`
                : systemMessage;

            // Formatta i messaggi per l'API (solo 'role' e 'content')
            // Azure AI richiede ruoli specifici: 'system', 'assistant', 'user', 'function', 'tool', 'developer'
            const apiMessages = currentMessages.map(({ role, content }) => {
                // Converti 'bot' in 'assistant' per compatibilità con Azure AI
                const azureRole = role === 'bot' ? 'assistant' : role;
                return { role: azureRole, content };
            });

            const requestBody = {
                model: settings.model,
                messages: [
                    { role: "system", content: systemMessageWithContext },
                    ...apiMessages
                ],
                temperature: settings.temperature,
                max_tokens: settings.maxTokens,
                stream: true
            };
            
            console.log("Corpo della richiesta:", requestBody);
            
            const response = await fetch('/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            console.log("Risposta ricevuta:", response.status, response.statusText);
            console.log("Headers della risposta:", [...response.headers.entries()]);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error("Errore HTTP:", response.status, errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            // Verifica se la risposta è effettivamente uno stream
            if (!response.body) {
                console.error("La risposta non contiene un body streamabile");
                throw new Error("La risposta non contiene un body streamabile");
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let botMessageContent = "";
            
            let chunkCount = 0;
            let hasReceivedContent = false;
            
            while (true) {
                const { done, value } = await reader.read();
                chunkCount++;
                console.log(`Chunk ${chunkCount}: done=${done}, value length=${value?.length || 0}`);
                
                if (done) {
                    console.log("Stream completato");
                    break;
                }
                
                // Segnala che abbiamo ricevuto almeno un chunk
                hasReceivedContent = true;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop();
                
                for (const line of lines) {
                    console.log("Linea ricevuta:", line);
                    if (line.startsWith("data: ")) {
                        const jsonStr = line.slice(6);
                        if (jsonStr === "[DONE]") {
                            console.log("Stream terminato con [DONE]");
                            break;
                        }
                        
                        try {
                            const data = JSON.parse(jsonStr);
                            console.log("Dati ricevuti:", data);
                            const content = data.choices?.[0]?.delta?.content;
                            if (content) {
                                botMessageContent += content;
                                setCurrentBotMessage(botMessageContent);
                            }
                        } catch (e) {
                            console.warn("Parse error:", e, "Line:", line);
                        }
                    }
                }
            }
            
            console.log("Contenuto finale del bot:", botMessageContent);
            
            // Determina il contenuto del messaggio del bot
            let finalContent;
            if (!hasReceivedContent) {
                finalContent = "❌ Nessuna risposta ricevuta dal modello. Il server ha restituito una risposta vuota.";
            } else if (!botMessageContent) {
                finalContent = "❌ Nessun contenuto ricevuto dal modello. La risposta potrebbe essere stata interrotta.";
            } else {
                finalContent = botMessageContent;
            }
            
            // Aggiungi messaggio completo del bot
            const botMsg = {
                id: Date.now(),
                role: 'assistant',  // Usiamo 'assistant' invece di 'bot' per compatibilità con Azure AI
                content: finalContent,
                timestamp: new Date()
            };
            
            setMessages(prev => {
                const updatedMessages = [...prev, botMsg];
                
                // Salva i messaggi nel database se c'è una chat corrente
                if (currentChat) {
                    saveChatMessages(currentChat.id, updatedMessages);
                }
                
                return updatedMessages;
            });
        } catch (error) {
            console.error("Errore completo:", error);
            const errorMsg = {
                id: Date.now(),
                role: 'bot',
                content: `❌ Errore: ${error.message}`,
                timestamp: new Date()
            };
            setMessages(prev => {
                const updatedMessages = [...prev, errorMsg];
                
                // Salva i messaggi nel database se c'è una chat corrente
                if (currentChat) {
                    saveChatMessages(currentChat.id, updatedMessages);
                }
                
                return updatedMessages;
            });
        } finally {
            setIsBotTyping(false);
            setCurrentBotMessage('');
        }
    }
    
    // Copia codice negli appunti
    // Salva impostazioni
    function saveSettings() {
        setSettings({
            model: "gpt-4.1",
            temperature: parseFloat(document.getElementById('temperature')?.value || settings.temperature),
            maxTokens: parseInt(document.getElementById('max-tokens')?.value || settings.maxTokens)
        });
        setShowSettings(false);
    }
    
    return (
        <div className="app-container">
            {/* Sidebar */}
            <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
                {/* Header Sidebar con pulsante chiudi */}
                <div className="sidebar-header">
                    <h2>KrakenGPT</h2>
                    <button 
                        className="icon-btn close-sidebar-btn" 
                        onClick={() => setSidebarOpen(false)}
                        title="Chiudi sidebar"
                    >
                        ☰
                    </button>
                </div>
                
                {/* Sezione Progetti */}
                <section className="sidebar-section">
                    <div className="section-header">
                        <h3>📂 Progetti</h3>
                        <button 
                            className="icon-btn new-project-btn" 
                            onClick={() => openProjectForm()}
                            title="Nuovo Progetto" 
                            aria-label="Crea nuovo progetto"
                        >
                            +
                        </button>
                    </div>
                    <ul className="projects-list">
                        {projects.map(project => (
                            <li 
                                key={project.id} 
                                className={`sidebar-item project-item ${currentProject?.id === project.id ? 'active' : ''}`}
                            >
                                <div 
                                    className="project-name"
                                    onClick={() => {
                                        setCurrentProject(project);
                                        loadChats(project.id);
                                    }}
                                >
                                    {project.name}
                                </div>
                                <div className="project-actions">
                                    <button 
                                        className="icon-btn edit-project-btn" 
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            openProjectForm(project);
                                        }}
                                        title="Modifica progetto"
                                        aria-label="Modifica progetto"
                                    >
                                        ✎
                                    </button>
                                    <button 
                                        className="icon-btn delete-project-btn" 
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteProject(project.id);
                                        }}
                                        title="Elimina progetto"
                                        aria-label="Elimina progetto"
                                    >
                                        ⊗
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </section>
                
                {/* Sezione Chat Recenti */}
                <section className="sidebar-section">
                    <div className="section-header">
                        <h3>💬 Chat recenti</h3>
                        <button 
                            className="icon-btn new-chat-btn" 
                            onClick={openChatForm}
                            title="Nuova Chat" 
                            aria-label="Avvia nuova chat"
                        >
                            +
                        </button>
                    </div>
                    <ul className="conversation-history">
                        {projectChats.map(chat => (
                            <li 
                                key={chat.id} 
                                className={`sidebar-item chat-item ${currentChat?.id === chat.id ? 'active' : ''}`}
                            >
                                <div 
                                    className="chat-content"
                                    onClick={() => {
                                        setCurrentChat(chat);
                                        loadChatMessages(chat.id);
                                    }}
                                >
                                    <div className="chat-info">
                                        <span className="chat-title">{chat.title}</span>
                                        <span className="chat-project">{currentProject?.name}</span>
                                    </div>
                                </div>
                                <div className="chat-actions">
                                    <button 
                                        className="icon-btn delete-chat-btn" 
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteChat(chat.id, false);
                                        }}
                                        title="Elimina chat"
                                        aria-label="Elimina chat"
                                    >
                                        ⊗
                                    </button>
                                </div>
                            </li>
                        ))}
                        {independentChats.map(chat => (
                            <li 
                                key={`ind-${chat.id}`} 
                                className={`sidebar-item chat-item ${currentChat?.id === chat.id ? 'active' : ''}`}
                            >
                                <div 
                                    className="chat-content"
                                    onClick={() => {
                                        setCurrentChat(chat);
                                        loadChatMessages(chat.id);
                                    }}
                                >
                                    <div className="chat-info">
                                        <span className="chat-title">{chat.title}</span>
                                        <span className="chat-project independent">Indipendente</span>
                                    </div>
                                </div>
                                <div className="chat-actions">
                                    <button 
                                        className="icon-btn delete-chat-btn" 
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteChat(chat.id, true);
                                        }}
                                        title="Elimina chat"
                                        aria-label="Elimina chat"
                                    >
                                        ⊗
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </section>
                
                {/* Footer Sidebar */}
                <footer className="sidebar-footer">
                    <div className="user-info">
                        <div className="user-avatar" aria-hidden="true">👤</div>
                        <span className="user-name">Utente</span>
                    </div>
                    <button className="settings-btn" onClick={() => setShowSettings(true)}>⚙ Impostazioni</button>
                </footer>
            </aside>
            
            {/* Main Container */}
            <main className="main-container">
                {/* Pulsante per aprire sidebar quando è chiusa */}
                {!sidebarOpen && (
                    <button 
                        className="open-sidebar-btn"
                        onClick={() => setSidebarOpen(true)}
                        title="Apri sidebar"
                    >
                        ☰
                    </button>
                )}
                
                {/* Header Chat */}
                <header className="chat-header">
                    <div className="chat-header-main">
                        <h1 id="chat-title">
                            KrakenGPT
                        </h1>
                        {currentChat && (
                            <button 
                                className="edit-context-btn"
                                onClick={() => {
                                    setCurrentContext(currentChat.context || "");
                                    setShowContextModal(true);
                                }}
                                title="Aggiungi Contesto RAG"
                            >
                                📚
                            </button>
                        )}
                    </div>
                </header>
                
                {/* Messaggi Chat */}
                <section className="chat-messages" ref={chatMessagesRef} aria-live="polite" aria-atomic="false">
                    {currentChat && (
                        <>
                            {messages.map(msg => (
                                <div key={msg.id} className={`message ${msg.role}`}>
                                    <div className="message-content">
                                        <MarkdownRenderer content={typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content, null, 2)} />
                                    </div>
                                    <div className="message-time">
                                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>
                            ))}
                            
                            {/* Messaggio in streaming */}
                            {isBotTyping && currentBotMessage && (
                                <div className="message bot streaming">
                                    <div className="message-content">
                                        <MarkdownRenderer content={typeof currentBotMessage === 'string' ? currentBotMessage : JSON.stringify(currentBotMessage, null, 2)} />
                                    </div>
                                </div>
                            )}
                            
                            {/* Indicatore di digitazione */}
                            {isBotTyping && !currentBotMessage && (
                                <div className="enhanced-typing-indicator">
                                    <div className="typing-text">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </section>
                
                {/* Dialogo "Nessuna chat selezionata" - Floating */}
                {!currentChat && (
                    <div className="no-chat-selected">
                        <div className="welcome-box">
                            <h2>Benvenuto in KrakenGPT</h2>
                            <p>Seleziona una chat esistente o creane una nuova per iniziare.</p>
                            <div className="recent-chats-box">
                                <h3>Chat Recenti</h3>
                                {projectChats.length > 0 ? (
                                    <ul className="recent-chats-list">
                                        {projectChats.slice(0, 5).map(chat => (
                                            <li 
                                                key={chat.id} 
                                                className="recent-chat-item"
                                                onClick={() => {
                                                    setCurrentChat(chat);
                                                    loadChatMessages(chat.id);
                                                }}
                                            >
                                                <span className="recent-chat-title">{chat.title}</span>
                                                <span className="recent-chat-project">{currentProject?.name}</span>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="no-recent-chats">Nessuna chat recente disponibile.</p>
                                )}
                            </div>
                            <button 
                                className="new-chat-button"
                                onClick={openChatForm}
                            >
                                + Nuova Chat
                            </button>
                        </div>
                    </div>
                )}
                
                {/* Input Chat */}
                {currentChat && (
                    <footer className="chat-input-container">
                        <form className="input-row" onSubmit={sendMessage} autoComplete="off">
                            <label htmlFor="file-input" className="file-upload-btn">
                                📎
                                <input type="file" id="file-input" accept="image/*,.pdf,.txt" hidden />
                            </label>
                            <textarea
                                value={userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                ref={userInputRef}
                                placeholder="Chiedi qualcosa a KrakenGPT..."
                                aria-label="Inserisci messaggio"
                                required
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        sendMessage(e);
                                    }
                                }}
                            />
                            <button 
                                type="submit" 
                                ref={sendButtonRef} 
                                aria-label="Invia messaggio"
                                disabled={isBotTyping}
                            >
                                ➤
                            </button>
                        </form>
                        <div className="input-warning">
                            <span>KrakenGPT può commettere errori. Verifica le informazioni importanti.</span>
                        </div>
                    </footer>
                )}
            </main>
            
            {/* Modale Form Progetto */}
            {showProjectForm && (
                <div className="modal" role="dialog" aria-modal="true" aria-labelledby="project-form-title">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h2 id="project-form-title">
                                {editingProject ? 'Modifica Progetto' : 'Nuovo Progetto'}
                            </h2>
                            <button 
                                className="close-btn" 
                                onClick={closeProjectForm}
                                aria-label="Chiudi form progetto"
                            >
                                &times;
                            </button>
                        </div>
                        <form className="modal-body" onSubmit={saveProject}>
                            <div className="form-group">
                                <label htmlFor="project-name">Nome Progetto *</label>
                                <input 
                                    type="text" 
                                    id="project-name" 
                                    value={projectForm.name}
                                    onChange={(e) => setProjectForm(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="Inserisci il nome del progetto"
                                    required
                                />
                            </div>
                            
                            <div className="form-group">
                                <label htmlFor="project-description">Descrizione</label>
                                <textarea 
                                    id="project-description" 
                                    value={projectForm.description}
                                    onChange={(e) => setProjectForm(prev => ({ ...prev, description: e.target.value }))}
                                    placeholder="Descrizione del progetto (opzionale)"
                                    rows="3"
                                />
                            </div>
                            
                            <div className="form-group">
                                <label htmlFor="project-prompt">Project Prompt</label>
                                <textarea 
                                    id="project-prompt" 
                                    value={projectForm.prompt}
                                    onChange={(e) => setProjectForm(prev => ({ ...prev, prompt: e.target.value }))}
                                    placeholder="Prompt di sistema per questo progetto (es: 'Sei un assistente specializzato in React e JavaScript...')"
                                    rows="4"
                                />
                                <small className="form-help">
                                    Questo prompt verrà utilizzato come contesto di sistema per tutte le chat di questo progetto.
                                </small>
                            </div>
                        </form>
                        <div className="modal-footer">
                            <button 
                                type="button" 
                                onClick={saveProject}
                                className="btn-primary"
                                disabled={!projectForm.name.trim()}
                            >
                                {editingProject ? 'Salva Modifiche' : 'Crea Progetto'}
                            </button>
                            <button 
                                type="button" 
                                onClick={closeProjectForm}
                                className="btn-secondary"
                            >
                                Annulla
                            </button>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Modale Form Chat */}
            {showChatForm && (
                <div className="modal" role="dialog" aria-modal="true" aria-labelledby="chat-form-title">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h2 id="chat-form-title">Nuova Chat</h2>
                            <button 
                                className="close-btn" 
                                onClick={closeChatForm}
                                aria-label="Chiudi form chat"
                            >
                                &times;
                            </button>
                        </div>
                        <form className="modal-body" onSubmit={createChat}>
                            <div className="form-group">
                                <label htmlFor="chat-title">Titolo Chat *</label>
                                <input 
                                    type="text" 
                                    id="chat-title" 
                                    value={chatForm.title}
                                    onChange={(e) => setChatForm(prev => ({ ...prev, title: e.target.value }))}
                                    placeholder="Inserisci il titolo della chat"
                                    required
                                />
                            </div>
                            
                            <div className="form-group">
                                <label htmlFor="chat-project">Progetto</label>
                                <select 
                                    id="chat-project" 
                                    value={chatForm.projectId || ''}
                                    onChange={(e) => setChatForm(prev => ({ ...prev, projectId: e.target.value || null }))}
                                >
                                    <option value="">Nessun progetto (Chat indipendente)</option>
                                    {projects.map(project => (
                                        <option key={project.id} value={project.id}>
                                            {project.name}
                                        </option>
                                    ))}
                                </select>
                                <small className="form-help">
                                    Scegli un progetto per associare la chat, oppure lascia vuoto per una chat indipendente.
                                </small>
                            </div>
                        </form>
                        <div className="modal-footer">
                            <button 
                                type="submit" 
                                onClick={createChat}
                                className="btn-primary"
                                disabled={!chatForm.title.trim()}
                            >
                                Crea Chat
                            </button>
                            <button 
                                type="button" 
                                onClick={closeChatForm}
                                className="btn-secondary"
                            >
                                Annulla
                            </button>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Modale Impostazioni */}
            {showSettings && (
                <div className="modal" role="dialog" aria-modal="true" aria-labelledby="settings-title">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h2 id="settings-title">Impostazioni</h2>
                            <button 
                                className="close-btn" 
                                onClick={() => setShowSettings(false)}
                                aria-label="Chiudi impostazioni"
                            >
                                &times;
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="setting-group">
                                <label htmlFor="model-select">Modello</label>
                                <select 
                                    id="model-select" 
                                    ref={modelSelectRef}
                                    defaultValue="gpt-4.1"
                                >
                                    <option value="gpt-4.1">GPT-4.1</option>
                                </select>
                            </div>
                            
                            <div className="setting-group">
                                <label htmlFor="temperature">
                                    Temperatura: <span id="temperature-value">{settings.temperature}</span>
                                </label>
                                <input 
                                    type="range" 
                                    id="temperature" 
                                    min="0" 
                                    max="1" 
                                    step="0.1" 
                                    defaultValue={settings.temperature}
                                    onChange={(e) => {
                                        document.getElementById('temperature-value').textContent = e.target.value;
                                    }}
                                />
                            </div>
                            
                            <div className="setting-group">
                                <label htmlFor="max-tokens">
                                    Token massimi: <span id="max-tokens-value">{settings.maxTokens}</span>
                                </label>
                                <input 
                                    type="range" 
                                    id="max-tokens" 
                                    min="100" 
                                    max="32768" 
                                    step="100" 
                                    defaultValue={settings.maxTokens}
                                    onChange={(e) => {
                                        document.getElementById('max-tokens-value').textContent = e.target.value;
                                    }}
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button id="save-settings" onClick={saveSettings}>Salva</button>
                            <button id="cancel-settings" onClick={() => setShowSettings(false)}>Annulla</button>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Modale Contesto RAG */}
            {showContextModal && (
                <div className="modal" role="dialog" aria-modal="true" aria-labelledby="context-modal-title">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h2 id="context-modal-title">📚 Aggiungi Contesto RAG</h2>
                            <button 
                                className="close-btn" 
                                onClick={() => setShowContextModal(false)}
                                aria-label="Chiudi modale contesto"
                            >
                                &times;
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label htmlFor="chat-context">Contesto per la Chat</label>
                                <textarea 
                                    id="chat-context" 
                                    value={currentContext}
                                    onChange={(e) => setCurrentContext(e.target.value)}
                                    placeholder="Incolla qui il testo da usare come contesto per l'AI..."
                                    rows="8"
                                />
                                <small className="form-help">
                                    Questo testo verrà aggiunto al prompt di sistema per fornire contesto all'AI (RAG).
                                </small>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button 
                                type="button" 
                                onClick={saveChatContext}
                                className="btn-primary"
                            >
                                Salva Contesto
                            </button>
                            <button 
                                type="button" 
                                onClick={() => setShowContextModal(false)}
                                className="btn-secondary"
                            >
                                Annulla
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
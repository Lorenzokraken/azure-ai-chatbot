:root {
  --bg-primary: #1E1E1E;        /* Sfondo principale (editor) */
  --bg-secondary: #252526;      /* Sfondo pannelli/chat */
  --bg-tertiary: #2D2D30;       /* Hover / selezione leggera */
  --text-primary: #D4D4D4;      /* Testo principale */
  --text-secondary: #9E9E9E;    /* Testo secondario / placeholder */
  --text-muted: #6A6A6A;        /* Testo disattivato / metadati */
  --accent-blue: #569CD6;       /* Accento primario (link, bottoni, AI) */
  --accent-green: #6A9955;      /* Commenti / successo */
  --accent-purple: #C586C0;     /* Keyword / funzioni */
  --border: #3E3E42;            /* Bordi sottili */
  --shadow: rgba(0, 0, 0, 0.3); /* Ombre morbide */
  --selection: #264F78;         /* Sfondo selezione testo */
  --error: #F48771;             /* Errori / warning */
  --success: #89D185;           /* Azioni completate */
}
.chat-container {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 8px;
  border: 1px solid var(--border);
  box-shadow: 0 4px 12px var(--shadow);
  overflow: hidden;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.chat-header {
  background-color: var(--bg-primary);
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-header .avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-blue), #3A70B3);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.chat-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.message.bot .message-content {
  background-color: var(--bg-primary);
  border: 1px solid var(--border);
}

.message.user .message-content {
  background-color: var(--accent-blue);
  color: white;
}

.message-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  text-align: right;
}

.chat-input-container {
  padding: 16px;
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 14px;
  outline: none;
}

.chat-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(86, 156, 214, 0.3);
}

.send-button {
  padding: 0 16px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.send-button:hover {
  background-color: #4b89c0;
}

.send-button:active {
  background-color: #3a70b3;
}

/* Scroll personalizzato (stile VS Code) */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background-color: var(--border);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-track {
  background-color: transparent;
}



┌───────────────┬──────────────────────────────────────┐
│ 📂 Progetti   │  👤 KrakenGPT — main.py              │
│ main.py — Ass │ ──────────────────────────────────── │
│ index.html    │ Bot: Ciao! Come posso aiutarti?     │
│ script.js     │       [10:30]                        │
│ + Nuovo       │                                      │
│               │                 Ciao! 😊            │
│ 💬 Chat rec.  │                 [10:31]              │
│ Refactor...   │                                      │
│ Explain...    │ ⚪ ⚪ ⚪                               │
│ Generate...   │                                      │
│ + Nuova chat  │ [INPUT]                      [INVIA] │
└───────────────┴──────────────────────────────────────┘
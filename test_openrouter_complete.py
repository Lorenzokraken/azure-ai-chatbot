#!/usr/bin/env python3
"""
Script finale per testare modelli OpenRouter e aggiornare automaticamente App.js
Versione migliorata che gestisce i casi comuni di errore.
"""

import requests
import os
import json
import time
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Lista estesa di modelli free da testare
MODELS_TO_TEST = [
    # Modelli più probabili di funzionare
    'meta-llama/llama-3.1-8b-instruct:free',
    'microsoft/phi-3-mini-128k-instruct:free', 
    'google/gemma-2-9b-it:free',
    
    # Altri modelli da testare
    'qwen/qwen-2-7b-instruct:free',
    'mistralai/mistral-7b-instruct:free',
    'openchat/openchat-7b:free',
    'microsoft/phi-3-medium-128k-instruct:free',
    'meta-llama/llama-3.1-70b-instruct:free',
    'huggingfaceh4/zephyr-7b-beta:free',
    'nousresearch/nous-capybara-7b:free',
    
    # Modelli premium (per test di connettività)
    'openai/gpt-3.5-turbo',
    'anthropic/claude-3-haiku'
]

def test_model(model_name, timeout=15):
    """Testa un singolo modello"""
    print(f"🧪 Testando {model_name}...")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "KrakenGPT Test"
    }
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Rispondi solo 'OK'"}],
        "max_tokens": 5,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                print(f"   ✅ FUNZIONA: {content.strip()}")
                return True
            else:
                print(f"   ❌ Nessun contenuto")
        elif response.status_code == 401:
            print(f"   🔑 Errore autenticazione - chiave API non valida")
            return "auth_error"
        elif response.status_code == 429:
            print(f"   ⏳ Rate limit - attendo...")
            return "rate_limit"
        elif response.status_code == 402:
            print(f"   💳 Crediti insufficienti")
        else:
            print(f"   ❌ Errore {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout")
    except Exception as e:
        print(f"   ❌ Errore: {str(e)[:50]}...")
    
    return False

def test_api_connection():
    """Verifica se la connessione API funziona"""
    print("🔌 Verificando connessione API...")
    
    if not OPENROUTER_API_KEY:
        print("   ❌ OPENROUTER_API_KEY non trovata")
        return False
    
    # Test con un modello semplice
    result = test_model('meta-llama/llama-3.1-8b-instruct:free', timeout=10)
    
    if result == "auth_error":
        print("   ❌ Chiave API non valida")
        return False
    elif result == "rate_limit":
        print("   ⚠️  Rate limit attivo, rallento i test")
        return "rate_limit"
    elif result is True:
        print("   ✅ Connessione API funzionante")
        return True
    else:
        print("   ⚠️  Possibili problemi di connettività")
        return "maybe"

def update_app_js(working_models):
    """Aggiorna App.js con i modelli funzionanti"""
    app_js_path = "react-frontend/src/App.js"
    
    if not os.path.exists(app_js_path):
        print(f"❌ File {app_js_path} non trovato")
        return
    
    # Leggi il file
    with open(app_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Genera la nuova lista modelli
    models_js = "    openrouter: [\n"
    for model in working_models:
        # Crea un nome leggibile
        display_name = model.split('/')[-1]
        display_name = display_name.replace(':free', ' (Free)')
        display_name = display_name.replace('-instruct', '')
        display_name = display_name.replace('-', ' ').title()
        
        models_js += f"        {{ value: '{model}', label: '{display_name}' }},\n"
    models_js += "    ]"
    
    # Trova e sostituisci la sezione openrouter
    import re
    pattern = r'(openrouter:\s*\[)[^}]+(\]\s*})'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(
            pattern, 
            f"\\1\n{models_js[16:]}", # Rimuove "    openrouter: " dall'inizio
            content, 
            flags=re.DOTALL
        )
        
        # Salva il file
        with open(app_js_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ {app_js_path} aggiornato con {len(working_models)} modelli funzionanti")
    else:
        print("❌ Non riesco a trovare la sezione openrouter in App.js")

def main():
    print("🤖 Test Completo Modelli OpenRouter")
    print("=" * 60)
    
    # Verifica connessione
    connection_status = test_api_connection()
    
    if connection_status is False:
        print("\n💡 Per risolvere:")
        print("   1. Vai su https://openrouter.ai/keys")
        print("   2. Genera una nuova chiave API")
        print("   3. Aggiorna OPENROUTER_API_KEY nel file .env")
        return
    
    print(f"\n🎯 Testando {len(MODELS_TO_TEST)} modelli...")
    
    working_models = []
    rate_limit_delay = 1 if connection_status == "rate_limit" else 0.5
    
    for i, model in enumerate(MODELS_TO_TEST, 1):
        print(f"\n[{i}/{len(MODELS_TO_TEST)}]", end=" ")
        
        result = test_model(model)
        
        if result is True:
            working_models.append(model)
        elif result == "rate_limit":
            print("   ⏳ Rate limit - attendo 5s...")
            time.sleep(5)
            
        time.sleep(rate_limit_delay)
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI FINALI")
    print("=" * 60)
    
    if working_models:
        print(f"✅ MODELLI FUNZIONANTI ({len(working_models)}):")
        for model in working_models:
            print(f"   • {model}")
        
        print(f"\n🔧 Aggiornamento App.js...")
        update_app_js(working_models)
        
        print(f"\n🎉 Test completato! {len(working_models)} modelli disponibili.")
    else:
        print("❌ Nessun modello funzionante trovato")
        print("\n💡 Possibili cause:")
        print("   • Chiave API non valida")
        print("   • Crediti OpenRouter esauriti") 
        print("   • Problemi temporanei con OpenRouter")

if __name__ == "__main__":
    main()
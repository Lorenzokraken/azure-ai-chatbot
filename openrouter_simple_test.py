#!/usr/bin/env python3
"""
Test rapido per verificare alcuni modelli OpenRouter più affidabili.
Proviamo con modelli che tipicamente funzionano meglio.
"""

import requests
import os
from dotenv import load_dotenv
import time

# Carica variabili d'ambiente
load_dotenv()

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Modelli da testare - solo quelli più affidabili
RELIABLE_MODELS = [
    'meta-llama/llama-3.1-8b-instruct:free',
    'microsoft/phi-3-mini-128k-instruct:free',
    'google/gemma-2-9b-it:free',
    'openai/gpt-3.5-turbo'  # Anche se a pagamento, verifica se l'API funziona
]

def test_api_key():
    """Testa se la chiave API è valida"""
    print("🔑 Testando validità chiave API...")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "KrakenGPT Test"
    }
    
    try:
        # Test con endpoint per verificare l'autenticazione
        response = requests.get(
            "https://openrouter.ai/api/v1/auth/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Key valida! User: {data.get('data', {}).get('username', 'N/A')}")
            return True
        else:
            print(f"   ❌ API Key non valida: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Errore nella verifica API: {e}")
        return False

def test_model_simple(model):
    """Test semplice di un modello"""
    print(f"🧪 Testando {model}...")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "KrakenGPT Test"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Rispondi solo con 'OK' per confermare che funzioni."}
        ],
        "max_tokens": 5,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                print(f"   ✅ FUNZIONA: {content.strip()}")
                return True
            else:
                print(f"   ❌ Nessun contenuto nella risposta")
        else:
            print(f"   ❌ Errore {response.status_code}: {response.text[:100]}...")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Errore: {str(e)[:100]}...")
        return False

def main():
    print("🤖 Test Rapido Modelli OpenRouter")
    print("=" * 50)
    
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY non trovata nel file .env")
        return
    
    print(f"🔧 API Key trovata: {OPENROUTER_API_KEY[:20]}...")
    
    # Test validità API key
    if not test_api_key():
        print("\n💡 Suggerimenti:")
        print("   1. Verifica che la chiave API sia corretta")
        print("   2. Vai su https://openrouter.ai/keys per generare una nuova chiave")
        print("   3. Aggiorna il file .env con la nuova chiave")
        return
    
    print(f"\n🎯 Testando {len(RELIABLE_MODELS)} modelli...")
    working_models = []
    
    for model in RELIABLE_MODELS:
        if test_model_simple(model):
            working_models.append(model)
        time.sleep(1)  # Pausa per evitare rate limiting
        print()
    
    print("=" * 50)
    print("📊 RISULTATI")
    print("=" * 50)
    
    if working_models:
        print(f"✅ MODELLI FUNZIONANTI ({len(working_models)}):")
        for model in working_models:
            print(f"   • {model}")
        
        print(f"\n🔧 CODICE PER App.js:")
        print("openrouter: [")
        for model in working_models:
            model_name = model.split("/")[-1].replace(":free", "").replace("-instruct", "")
            model_name = model_name.replace("-", " ").title()
            if ":free" in model:
                model_name += " (Free)"
            print(f"    {{ value: '{model}', label: '{model_name}' }},")
        print("]")
    else:
        print("❌ Nessun modello funzionante trovato")
        print("\n💡 Possibili cause:")
        print("   • API key non valida o scaduta")
        print("   • Crediti OpenRouter esauriti")
        print("   • Problemi temporanei con OpenRouter")

if __name__ == "__main__":
    main()
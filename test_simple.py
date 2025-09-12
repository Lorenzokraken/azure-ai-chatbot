#!/usr/bin/env python3
"""
Test semplice modelli OpenRouter con debug completo
"""

import requests
import os
from dotenv import load_dotenv
import json

# Ricarica le variabili d'ambiente
load_dotenv(override=True)

def test_simple_model():
    """Testa un modello semplice con debug completo"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ Chiave API non trovata")
        return False
    
    print(f"🔑 Chiave: {api_key[:20]}...")
    
    # URL e headers
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Azure AI Chatbot Test"
    }
    
    # Prova prima con un modello molto semplice e sempre disponibile
    models_to_test = [
        "openai/gpt-3.5-turbo",  # Dovrebbe sempre funzionare
        "meta-llama/llama-3.2-3b-instruct:free",
        "huggingface/zephyr-7b-beta:free"
    ]
    
    for model in models_to_test:
        print(f"\n🧪 Testando: {model}")
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 5,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            print(f"📡 Status: {response.status_code}")
            print(f"📄 Headers di risposta: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successo! Risposta: {result}")
                return True
            else:
                print(f"❌ Errore {response.status_code}")
                print(f"📄 Risposta completa: {response.text}")
                
        except Exception as e:
            print(f"❌ Eccezione: {e}")
    
    return False

def list_available_models():
    """Lista i modelli disponibili"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    print("\n🔍 Recupero lista modelli disponibili...")
    
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Trovati {len(models.get('data', []))} modelli")
            
            # Mostra solo i primi 5 modelli gratuiti
            free_models = []
            for model in models.get('data', [])[:20]:
                pricing = model.get('pricing', {})
                if (pricing.get('prompt') == '0' or pricing.get('prompt') == 0) and \
                   (pricing.get('completion') == '0' or pricing.get('completion') == 0):
                    free_models.append(model)
            
            print(f"🆓 Modelli gratuiti trovati: {len(free_models)}")
            for model in free_models[:5]:
                print(f"  - {model['id']}: {model.get('name', 'N/A')}")
                
        else:
            print(f"❌ Errore nel recupero modelli: {response.status_code}")
            print(f"📄 Risposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    print("🤖 Test Semplice OpenRouter")
    print("=" * 30)
    
    list_available_models()
    test_simple_model()
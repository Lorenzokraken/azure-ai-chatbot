#!/usr/bin/env python3
"""
Test finale dei modelli OpenRouter funzionanti
Aggiorna automaticamente App.js con i modelli che funzionano
"""

import asyncio
import aiohttp
import os
import json
import re
from dotenv import load_dotenv

# Ricarica le variabili d'ambiente
load_dotenv(override=True)

# Modelli da testare (basato su quello che funziona)
MODELS_TO_TEST = [
    {
        "id": "meta-llama/llama-3.2-3b-instruct:free",
        "name": "Llama 3.2 3B Instruct (Free)"
    },
    {
        "id": "meta-llama/llama-3.2-1b-instruct:free", 
        "name": "Llama 3.2 1B Instruct (Free)"
    },
    {
        "id": "nvidia/nemotron-nano-9b-v2:free",
        "name": "NVIDIA Nemotron Nano 9B V2 (Free)"
    },
    {
        "id": "openrouter/sonoma-dusk-alpha",
        "name": "Sonoma Dusk Alpha (Free)"
    },
    {
        "id": "openrouter/sonoma-sky-alpha",
        "name": "Sonoma Sky Alpha (Free)"
    },
    {
        "id": "huggingface/zephyr-7b-beta:free",
        "name": "Zephyr 7B β (Free)"
    },
    {
        "id": "microsoft/phi-3-mini-128k-instruct:free",
        "name": "Phi-3 Mini 128K Instruct (Free)"
    }
]

async def test_model(session, model):
    """Testa un singolo modello"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000", 
        "X-Title": "Azure AI Chatbot"
    }
    
    data = {
        "model": model["id"],
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5,
        "temperature": 0.1
    }
    
    try:
        async with session.post(url, headers=headers, json=data, timeout=20) as response:
            if response.status == 200:
                result = await response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    return True, model, f"✅ Risposta: '{content}'"
                else:
                    return False, model, "❌ Risposta vuota"
            elif response.status == 404:
                error_text = await response.text()
                if "data policy" in error_text:
                    return False, model, "❌ Non disponibile (privacy policy)"
                else:
                    return False, model, f"❌ Non trovato: {error_text[:50]}"
            else:
                error_text = await response.text()
                return False, model, f"❌ Errore {response.status}: {error_text[:50]}"
                
    except asyncio.TimeoutError:
        return False, model, "⏱️ Timeout"
    except Exception as e:
        return False, model, f"❌ Errore: {str(e)[:50]}"

async def test_all_models():
    """Testa tutti i modelli in parallelo"""
    print("🤖 Test Modelli OpenRouter Finali")
    print("=" * 35)
    
    async with aiohttp.ClientSession() as session:
        # Testa tutti i modelli in parallelo
        tasks = [test_model(session, model) for model in MODELS_TO_TEST]
        results = await asyncio.gather(*tasks)
    
    # Analizza i risultati
    working_models = []
    failed_models = []
    
    for success, model, message in results:
        if success:
            working_models.append(model)
            print(f"✅ {model['name']}: {message}")
        else:
            failed_models.append((model, message))
            print(f"❌ {model['name']}: {message}")
    
    print(f"\n📊 Risultati finali:")
    print(f"✅ Modelli funzionanti: {len(working_models)}")
    print(f"❌ Modelli non funzionanti: {len(failed_models)}")
    
    return working_models

def update_app_js(working_models):
    """Aggiorna App.js con solo i modelli funzionanti"""
    if not working_models:
        print("❌ Nessun modello funzionante trovato - non aggiorno App.js")
        return False
    
    app_js_path = "react-frontend/src/App.js"
    
    if not os.path.exists(app_js_path):
        print(f"❌ File {app_js_path} non trovato")
        return False
    
    try:
        with open(app_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Crea la nuova lista di modelli
        models_js = "const openrouterModels = [\n"
        for model in working_models:
            models_js += f'  {{ value: "{model["id"]}", label: "{model["name"]}" }},\n'
        models_js += "];"
        
        # Sostituisce la lista esistente
        pattern = r'const openrouterModels = \[[\s\S]*?\];'
        new_content = re.sub(pattern, models_js, content, flags=re.MULTILINE)
        
        # Scrive il file aggiornato
        with open(app_js_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ App.js aggiornato con {len(working_models)} modelli funzionanti!")
        
        # Mostra i modelli aggiunti
        print(f"\n📋 Modelli ora disponibili nel chatbot:")
        for model in working_models:
            print(f"   • {model['name']}")
            
        return True
        
    except Exception as e:
        print(f"❌ Errore nell'aggiornamento di App.js: {e}")
        return False

async def main():
    """Funzione principale"""
    working_models = await test_all_models()
    
    if working_models:
        update_app_js(working_models)
        print(f"\n🎉 Completato! Il chatbot ora ha {len(working_models)} modelli OpenRouter funzionanti.")
        print(f"🚀 Riavvia il chatbot per vedere i nuovi modelli!")
    else:
        print(f"\n❌ Nessun modello funzionante trovato.")

if __name__ == "__main__":
    asyncio.run(main())
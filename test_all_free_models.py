#!/usr/bin/env python3
"""
Script completo per recuperare e testare TUTTI i modelli gratuiti di OpenRouter
Aggiorna automaticamente App.js con tutti i modelli che funzionano davvero
"""

import asyncio
import aiohttp
import os
import json
import re
from dotenv import load_dotenv

# Ricarica le variabili d'ambiente
load_dotenv(override=True)

async def get_all_free_models():
    """Recupera tutti i modelli gratuiti direttamente da OpenRouter"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ Chiave API non trovata")
        return []
    
    print("🔍 Recupero tutti i modelli disponibili da OpenRouter...")
    
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('data', [])
                    
                    print(f"📊 Trovati {len(models)} modelli totali")
                    
                    # Filtra solo i modelli gratuiti
                    free_models = []
                    for model in models:
                        model_id = model.get('id', '')
                        pricing = model.get('pricing', {})
                        
                        # Criteri per modelli gratuiti
                        is_free = (
                            ':free' in model_id or 
                            pricing.get('prompt') == '0' or 
                            pricing.get('completion') == '0' or
                            (pricing.get('prompt') == 0 and pricing.get('completion') == 0)
                        )
                        
                        if is_free:
                            # Crea un nome più leggibile
                            name = model.get('name', model_id)
                            if ':free' in model_id:
                                name = f"{name} (Free)"
                            
                            free_models.append({
                                'id': model_id,
                                'name': name,
                                'context': model.get('context_length', 4096)
                            })
                    
                    print(f"🆓 Trovati {len(free_models)} modelli gratuiti:")
                    for model in free_models[:10]:  # Mostra solo i primi 10
                        print(f"  • {model['name']}")
                    if len(free_models) > 10:
                        print(f"  ... e altri {len(free_models) - 10} modelli")
                    
                    return free_models
                else:
                    print(f"❌ Errore nel recupero modelli: {response.status}")
                    return []
                    
    except Exception as e:
        print(f"❌ Errore: {e}")
        return []

async def test_model(session, model, semaphore):
    """Testa un singolo modello con controllo di concorrenza"""
    async with semaphore:  # Limita le richieste simultanee
        api_key = os.getenv('OPENROUTER_API_KEY')
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000", 
            "X-Title": "Azure AI Chatbot Test"
        }
        
        data = {
            "model": model["id"],
            "messages": [{"role": "user", "content": "Say hi"}],
            "max_tokens": 5,
            "temperature": 0.1
        }
        
        try:
            async with session.post(url, headers=headers, json=data, timeout=25) as response:
                if response.status == 200:
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        return True, model, f"✅ Risposta: '{content.strip()}'"
                    else:
                        return False, model, "❌ Risposta vuota"
                elif response.status == 404:
                    error_text = await response.text()
                    if "data policy" in error_text.lower() or "zero data retention" in error_text.lower():
                        return False, model, "❌ Bloccato da privacy policy"
                    else:
                        return False, model, f"❌ Non trovato"
                elif response.status == 400:
                    error_text = await response.text()
                    return False, model, f"❌ Richiesta non valida"
                elif response.status == 429:
                    return False, model, "❌ Rate limit superato"
                else:
                    return False, model, f"❌ Errore {response.status}"
                    
        except asyncio.TimeoutError:
            return False, model, "⏱️ Timeout (25s)"
        except Exception as e:
            return False, model, f"❌ Errore: {str(e)[:30]}"

async def test_all_free_models(free_models):
    """Testa tutti i modelli gratuiti con rate limiting"""
    print(f"\n🧪 Testando {len(free_models)} modelli gratuiti...")
    print("=" * 60)
    
    # Limita a 5 richieste simultanee per evitare rate limiting
    semaphore = asyncio.Semaphore(5)
    
    working_models = []
    failed_models = []
    
    async with aiohttp.ClientSession() as session:
        # Testa i modelli in batch per evitare sovraccarico
        batch_size = 10
        for i in range(0, len(free_models), batch_size):
            batch = free_models[i:i + batch_size]
            print(f"\n📦 Testando batch {i//batch_size + 1} ({len(batch)} modelli)...")
            
            # Testa il batch corrente
            tasks = [test_model(session, model, semaphore) for model in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processa i risultati
            for result in results:
                if isinstance(result, Exception):
                    print(f"❌ Errore generale: {result}")
                    continue
                    
                success, model, message = result
                if success:
                    working_models.append(model)
                    print(f"✅ {model['name'][:50]}: {message}")
                else:
                    failed_models.append((model, message))
                    print(f"❌ {model['name'][:50]}: {message}")
            
            # Pausa tra i batch per rispettare rate limits
            if i + batch_size < len(free_models):
                print("⏳ Pausa 3 secondi tra i batch...")
                await asyncio.sleep(3)
    
    print(f"\n📊 Risultati finali:")
    print(f"✅ Modelli funzionanti: {len(working_models)}")
    print(f"❌ Modelli non funzionanti: {len(failed_models)}")
    
    return working_models

def update_app_js(working_models):
    """Aggiorna App.js con tutti i modelli funzionanti"""
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
        models_js = "    openrouter: [\n"
        models_js += "        // Modelli testati e funzionanti ✅\n"
        for model in working_models:
            # Escape delle virgolette nel nome
            safe_name = model['name'].replace("'", "\\'").replace('"', '\\"')
            models_js += f'        {{ value: "{model["id"]}", label: "{safe_name}" }},\n'
        models_js += "    ]"
        
        # Pattern per trovare la sezione openrouter
        pattern = r'openrouter: \[[\s\S]*?\]'
        new_content = re.sub(pattern, models_js, content, flags=re.MULTILINE)
        
        # Scrive il file aggiornato
        with open(app_js_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ App.js aggiornato con {len(working_models)} modelli funzionanti!")
        
        # Mostra i modelli aggiunti (primi 10)
        print(f"\n📋 Primi 10 modelli ora disponibili:")
        for i, model in enumerate(working_models[:10]):
            print(f"   {i+1:2d}. {model['name']}")
        if len(working_models) > 10:
            print(f"   ... e altri {len(working_models) - 10} modelli!")
            
        return True
        
    except Exception as e:
        print(f"❌ Errore nell'aggiornamento di App.js: {e}")
        return False

async def main():
    """Funzione principale"""
    print("🤖 Test Completo Modelli OpenRouter Gratuiti")
    print("=" * 55)
    
    # Step 1: Recupera tutti i modelli gratuiti
    free_models = await get_all_free_models()
    
    if not free_models:
        print("❌ Nessun modello gratuito trovato")
        return
    
    # Step 2: Testa tutti i modelli
    working_models = await test_all_free_models(free_models)
    
    # Step 3: Aggiorna App.js
    if working_models:
        update_app_js(working_models)
        print(f"\n🎉 Completato! Il chatbot ora ha {len(working_models)} modelli OpenRouter funzionanti.")
        print(f"🔄 Ricarica la pagina del chatbot per vedere tutti i nuovi modelli!")
    else:
        print(f"\n❌ Nessun modello funzionante trovato.")
        print("💡 Possibili cause:")
        print("   - Rate limiting temporaneo")
        print("   - Privacy policy di OpenRouter")
        print("   - Modelli temporaneamente non disponibili")

if __name__ == "__main__":
    asyncio.run(main())
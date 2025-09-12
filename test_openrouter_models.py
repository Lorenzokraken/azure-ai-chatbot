#!/usr/bin/env python3
"""
Test script per verificare quali modelli gratuiti di OpenRouter funzionano correttamente.
Questo script testa tutti i modelli free e mostra quali rispondono.
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Optional

# Modelli gratuiti da testare
FREE_MODELS = [
    'meta-llama/llama-3.1-8b-instruct:free',
    'microsoft/phi-3-mini-128k-instruct:free',
    'google/gemma-2-9b-it:free',
    'qwen/qwen-2-7b-instruct:free',
    'microsoft/phi-3-medium-128k-instruct:free',
    'meta-llama/llama-3.1-70b-instruct:free',
    'google/gemma-2-27b-it:free',
    'anthropic/claude-3-haiku:beta',
    'openai/gpt-3.5-turbo',
    'huggingfaceh4/zephyr-7b-beta:free',
    'openchat/openchat-7b:free',
    'gryphe/mythomist-7b:free',
    'undi95/toppy-m-7b:free',
    'openrouter/auto',
    'nousresearch/nous-capybara-7b:free',
    'mistralai/mistral-7b-instruct:free',
    'pygmalionai/mythalion-13b:free',
    'xwin-lm/xwin-lm-70b:free',
    'alpindale/goliath-120b:free',
    'neversleep/noromaid-mixtral-8x7b-instruct:free'
]

# Messaggio di test semplice
TEST_MESSAGE = "Ciao! Puoi rispondere con un semplice 'OK' per confermare che funzioni?"

class OpenRouterTester:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.results = []
        
    async def test_model(self, session: aiohttp.ClientSession, model: str) -> Dict:
        """Testa un singolo modello"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "KrakenGPT Test"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": TEST_MESSAGE}
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        start_time = time.time()
        result = {
            "model": model,
            "status": "unknown",
            "response": None,
            "error": None,
            "response_time": None
        }
        
        try:
            print(f"🧪 Testando {model}...")
            
            async with session.post(
                self.base_url, 
                headers=headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                response_time = time.time() - start_time
                result["response_time"] = round(response_time, 2)
                
                if response.status == 200:
                    data = await response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        result["status"] = "success"
                        result["response"] = content.strip()
                        print(f"   ✅ Successo ({response_time:.2f}s): {content.strip()[:50]}...")
                    else:
                        result["status"] = "no_content"
                        result["error"] = "Nessun contenuto nella risposta"
                        print(f"   ❌ Nessun contenuto nella risposta")
                else:
                    error_text = await response.text()
                    result["status"] = "http_error"
                    result["error"] = f"HTTP {response.status}: {error_text[:200]}"
                    print(f"   ❌ Errore HTTP {response.status}: {error_text[:100]}...")
                    
        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = "Timeout (>30s)"
            print(f"   ⏰ Timeout per {model}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"   ❌ Errore per {model}: {str(e)[:100]}...")
            
        return result
    
    async def test_all_models(self) -> List[Dict]:
        """Testa tutti i modelli in parallelo (con limite di concorrenza)"""
        connector = aiohttp.TCPConnector(limit=5)  # Limite connessioni simultanee
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Testa i modelli in batch per evitare sovraccarico
            batch_size = 3
            all_results = []
            
            for i in range(0, len(FREE_MODELS), batch_size):
                batch = FREE_MODELS[i:i + batch_size]
                print(f"\n📦 Batch {i//batch_size + 1}: {', '.join(batch)}")
                
                tasks = [self.test_model(session, model) for model in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        print(f"   ❌ Eccezione: {result}")
                    else:
                        all_results.append(result)
                
                # Pausa tra i batch per evitare rate limiting
                if i + batch_size < len(FREE_MODELS):
                    print("   ⏸️  Pausa 2s tra i batch...")
                    await asyncio.sleep(2)
            
            return all_results
    
    def print_summary(self, results: List[Dict]):
        """Stampa il riepilogo dei risultati"""
        print("\n" + "="*80)
        print("📊 RIEPILOGO RISULTATI")
        print("="*80)
        
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] != "success"]
        
        print(f"\n✅ MODELLI FUNZIONANTI ({len(successful)}/{len(results)}):")
        print("-" * 50)
        for result in sorted(successful, key=lambda x: x["response_time"]):
            print(f"  • {result['model']:<45} ({result['response_time']}s)")
        
        print(f"\n❌ MODELLI NON FUNZIONANTI ({len(failed)}):")
        print("-" * 50)
        for result in failed:
            status_emoji = {
                "timeout": "⏰",
                "http_error": "🌐", 
                "no_content": "📭",
                "error": "💥"
            }.get(result["status"], "❓")
            print(f"  {status_emoji} {result['model']:<45} ({result['status']})")
            if result["error"]:
                print(f"     └─ {result['error'][:70]}...")
        
        # Genera codice per App.js
        print(f"\n🔧 CODICE PER App.js (solo modelli funzionanti):")
        print("-" * 50)
        print("openrouter: [")
        for result in sorted(successful, key=lambda x: x["model"]):
            model_name = result["model"].split("/")[-1].replace(":free", "").replace("-instruct", "")
            model_name = model_name.replace("-", " ").title()
            if ":free" in result["model"]:
                model_name += " (Free)"
            print(f"    {{ value: '{result['model']}', label: '{model_name}' }},")
        print("]")

async def main():
    """Funzione principale"""
    print("🤖 Test dei modelli gratuiti OpenRouter")
    print("="*50)
    
    # Leggi la chiave API dal file .env
    import os
    from dotenv import load_dotenv
    
    # Carica variabili d'ambiente
    load_dotenv()
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Errore: OPENROUTER_API_KEY non trovata nel file .env")
        print("   Assicurati di avere il file .env con OPENROUTER_API_KEY=your-key")
        return
    
    tester = OpenRouterTester(api_key)
    
    print(f"🎯 Testando {len(FREE_MODELS)} modelli gratuiti...")
    print("   (Questo potrebbe richiedere qualche minuto)\n")
    
    start_time = time.time()
    results = await tester.test_all_models()
    total_time = time.time() - start_time
    
    tester.print_summary(results)
    
    print(f"\n⏱️  Tempo totale: {total_time:.1f} secondi")
    print("🏁 Test completato!")
    
    # Salva i risultati in un file JSON
    with open('openrouter_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("💾 Risultati salvati in 'openrouter_test_results.json'")

if __name__ == "__main__":
    asyncio.run(main())
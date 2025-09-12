#!/usr/bin/env python3
"""
Script per validare la chiave API OpenRouter
Testa se la chiave è valida usando l'endpoint di autenticazione
"""

import requests
import os
from dotenv import load_dotenv

# Ricarica le variabili d'ambiente
load_dotenv(override=True)

def test_openrouter_key():
    """Testa la validità della chiave OpenRouter"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ Chiave API non trovata nel file .env")
        return False
    
    print(f"🔑 Testando chiave: {api_key[:20]}...")
    print(f"🔍 Lunghezza chiave: {len(api_key)} caratteri")
    
    # URL dell'endpoint di autenticazione
    auth_url = "https://openrouter.ai/api/v1/auth/key"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Prova la richiesta di autenticazione
        response = requests.get(auth_url, headers=headers, timeout=10)
        
        print(f"📡 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chiave API valida!")
            print(f"📊 Dati account: {data}")
            return True
        elif response.status_code == 401:
            print("❌ Chiave API non valida o scaduta")
            print(f"📄 Risposta: {response.text}")
        elif response.status_code == 404:
            print("❌ Endpoint non trovato - potrebbe essere un problema temporaneo")
            print(f"📄 Risposta: {response.text[:200]}...")
        else:
            print(f"❌ Errore inatteso: {response.status_code}")
            print(f"📄 Risposta: {response.text[:200]}...")
            
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore di connessione: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Test Validazione Chiave OpenRouter (v2)")
    print("=" * 45)
    test_openrouter_key()
#!/usr/bin/env python3
"""
TESTEUR COMPLET DE L'API LCP
Ce script teste tous les endpoints de l'API LCP pour comprendre son fonctionnement
"""

import requests
import json
from datetime import datetime

def tester_api_lcp_complet():
    print("🧪 TEST COMPLET API LCP - LOTUS CAPITAL PLATFORM")
    print("=" * 60)
    print(f"⏰ Début du test: {datetime.now()}")
    print("🌐 URL de base: http://51.195.222.3:8080")
    print("=" * 60)
    
    base_url = "http://51.195.222.3:8080"
    
    # 1. TEST DE LA DOCUMENTATION
    print("\n📖 1. TEST DOCUMENTATION")
    print("-" * 30)
    
    docs_endpoints = [
        "/docs",
        "/swagger",
        "/swagger-ui.html",
        "/api-docs",
        "/v2/api-docs",
        "/v3/api-docs"
    ]
    
    for endpoint in docs_endpoints:
        url = base_url + endpoint
        print(f"\n🔍 Test documentation: {endpoint}")
        print(f"   📍 URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   ✅ Status: {response.status_code}")
            
            if response.status_code == 200:
                if "swagger" in response.text.lower() or "openapi" in response.text.lower():
                    print("   🎯 Type: Documentation Swagger/OpenAPI trouvée!")
                elif "html" in response.headers.get('content-type', ''):
                    print("   📄 Type: Page HTML")
                else:
                    print("   🔍 Type: Autre format")
                    
                # Afficher un extrait
                preview = response.text[:200].replace('\n', ' ')
                print(f"   📝 Aperçu: {preview}...")
            else:
                print(f"   ❌ Non accessible")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection refused")
        except Exception as e:
            print(f"   💥 Erreur: {e}")

    # 2. TEST DES ENDPOINTS API
    print("\n🔌 2. TEST ENDPOINTS API")
    print("-" * 30)
    
    api_endpoints = [
        # Endpoints traders
        "/api/traders",
        "/traders", 
        "/api/traders/list",
        "/traders/list",
        "/api/accounts",
        "/accounts",
        
        # Endpoints metrics
        "/api/metrics",
        "/metrics",
        "/api/performance",
        "/performance",
        
        # Endpoints santé
        "/health",
        "/api/health", 
        "/status",
        "/api/status",
        
        # Endpoints génériques
        "/api",
        "/api/v1",
        "/api/v2",
        "/info",
        "/api/info"
    ]
    
    for endpoint in api_endpoints:
        url = base_url + endpoint
        print(f"\n🔌 Test endpoint: {endpoint}")
        print(f"   📍 URL: {url}")
        
        try:
            response = requests.get(url, timeout=8)
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    try:
                        data = response.json()
                        print(f"   ✅ Format: JSON")
                        print(f"   🏗️  Structure: {list(data.keys())[:5]}...")
                        
                        # Afficher un échantillon des données
                        sample = str(data)[:150]
                        print(f"   📋 Échantillon: {sample}...")
                        
                    except json.JSONDecodeError:
                        print(f"   ⚠️  Format: JSON invalide")
                        print(f"   📝 Contenu: {response.text[:100]}...")
                else:
                    print(f"   📄 Format: {content_type}")
                    print(f"   📝 Aperçu: {response.text[:100]}...")
                    
            elif response.status_code == 404:
                print(f"   ❌ Endpoint non trouvé")
            elif response.status_code == 401:
                print(f"   🔐 Authentification requise")
            elif response.status_code == 403:
                print(f"   🚫 Accès interdit")
            elif response.status_code == 405:
                print(f"   ⚠️  Méthode non autorisée")
            else:
                print(f"   ❌ Erreur {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection refused")
        except Exception as e:
            print(f"   💥 Erreur: {e}")

    # 3. TEST AVEC AUTHENTIFICATION (si vous avez une clé API)
    print("\n🔑 3. TEST AVEC AUTHENTIFICATION")
    print("-" * 30)
    
    # Remplacez par votre vraie clé API si vous l'avez
    api_key = "VOTRE_CLE_API_ICI"  # À modifier
    
    if api_key != "VOTRE_CLE_API_ICI":
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        endpoints_proteges = [
            "/api/traders",
            "/api/metrics",
            "/api/performance"
        ]
        
        for endpoint in endpoints_proteges:
            url = base_url + endpoint
            print(f"\n🔑 Test authentifié: {endpoint}")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                print(f"   📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ Authentification réussie!")
                    data = response.json()
                    print(f"   📦 Données: {len(data)} éléments")
                elif response.status_code == 401:
                    print(f"   ❌ Clé API invalide")
                elif response.status_code == 403:
                    print(f"   🚫 Permission insuffisante")
                    
            except Exception as e:
                print(f"   💥 Erreur: {e}")
    else:
        print("   ⚠️  Aucune clé API configurée - test ignoré")

    # 4. TEST DE DONNÉES SPÉCIFIQUES (avec un exemple de trader)
    print("\n👤 4. TEST AVEC UN TRADER SPÉCIFIQUE")
    print("-" * 30)
    
    # Exemple de username LCP - à adapter
    traders_test = ["john_trader", "test_user", "demo", "user123"]
    
    for trader in traders_test:
        endpoints_trader = [
            f"/api/traders/{trader}",
            f"/traders/{trader}",
            f"/api/accounts/{trader}",
            f"/accounts/{trader}",
            f"/api/traders/{trader}/metrics",
            f"/traders/{trader}/metrics"
        ]
        
        for endpoint in endpoints_trader:
            url = base_url + endpoint
            print(f"\n👤 Test trader '{trader}': {endpoint}")
            
            try:
                response = requests.get(url, timeout=5)
                print(f"   📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ Données trouvées pour {trader}!")
                    data = response.json()
                    print(f"   🏗️  Structure: {list(data.keys())}")
                    
                    # Afficher les métriques importantes
                    if 'profit' in data or 'drawdown' in data:
                        profit = data.get('profit', data.get('profitPercentage', 'N/A'))
                        drawdown = data.get('drawdown', data.get('dailyDrawdown', 'N/A'))
                        print(f"   📈 Profit: {profit}% | Drawdown: {drawdown}%")
                        
                elif response.status_code == 404:
                    print(f"   ❌ Trader '{trader}' non trouvé")
                    break  # Passer au trader suivant
                    
            except Exception as e:
                print(f"   💥 Erreur: {e}")

    # 5. RÉCAPITULATIF
    print("\n" + "=" * 60)
    print("📊 RÉCAPITULATIF DU TEST API LCP")
    print("=" * 60)
    print("💡 Conseils pour la suite:")
    print("   1. Identifiez les endpoints qui fonctionnent")
    print("   2. Notez le format des données renvoyées") 
    print("   3. Configurez votre clé API si nécessaire")
    print("   4. Adaptez monitoring_a2.py au bon format")
    print("=" * 60)
    print(f"✅ Test terminé à: {datetime.now()}")

if __name__ == "__main__":
    tester_api_lcp_complet()

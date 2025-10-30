import requests
import time
from datetime import datetime
import sys
import os
import json

# Ajouter le chemin pour importer vos modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot_discord'))

from emailer.email_sheet import sheet

# === CONFIGURATION API LCP ===
LCP_API_URL = "http://51.195.222.3:8080"
LCP_API_KEY = "VOTRE_CLE_API_ICI"  # À remplacer par votre vraie clé API

# === RÈGLES ASSESSMENT 2 ===
ASSESSMENT2_RULES = {
    "profit_target": 4.0,
    "max_simultaneous_trades": 3,
    "max_daily_drawdown": 1.0,
    "max_total_drawdown": 2.5,
    "min_trades": 10
}

class Assessment2MonitorStandalone:
    def __init__(self, sheet):
        self.sheet = sheet
        self.api_url = LCP_API_URL
        self.api_key = LCP_API_KEY
    
    def surveiller_traders(self):
        """Fonction principale de surveillance avec VRAIE API"""
        print(f"\n🔍 [{datetime.now()}] SURVEILLANCE ASSESSMENT 2 - API RÉELLE")
        print("=" * 60)
        
        try:
            data = self.sheet.get_all_values()
            traders_trouves = 0
            traders_reussis = 0
            
            for row in data[1:]:
                if self.est_trader_assessment2(row):
                    traders_trouves += 1
                    reussi = self.analyser_trader(row)
                    if reussi:
                        traders_reussis += 1
            
            print(f"\n" + "=" * 60)
            print(f"📊 RÉCAPITULATIF:")
            print(f"   • Traders Assessment 2 trouvés: {traders_trouves}")
            print(f"   • Traders éligibles Assessment 3: {traders_reussis}")
            print(f"   • Traders en progression: {traders_trouves - traders_reussis}")
            
        except Exception as e:
            print(f"❌ Erreur surveillance: {e}")
    
    def est_trader_assessment2(self, row):
        return len(row) > 4 and row[4] == "active_assessment_2"
    
    def analyser_trader(self, row):
        discord_username = row[18] if len(row) > 18 else "Inconnu"
        candidate_id = row[0] if len(row) > 0 else "Inconnu"
        lcp_username = row[10] if len(row) > 10 else None  # Colonne K = LCP username
        
        print(f"\n📊 Analyse du trader: {discord_username}")
        print(f"   ID: {candidate_id}")
        print(f"   LCP Username: {lcp_username}")
        
        if not lcp_username:
            print("   ❌ Pas de LCP username dans Google Sheets")
            return False
        
        # 1. Récupérer métriques DEPUIS LA VRAIE API LCP
        metrics = self.obtenir_metriques_reelles(lcp_username)
        
        if metrics:
            # 2. Valider les règles
            validation = self.valider_regles(metrics)
            
            # 3. Afficher résultats
            self.afficher_resultats(discord_username, metrics, validation)
            
            # 4. Si réussi, mettre à jour Google Sheets
            if validation["reussi"]:
                self.mettre_a_jour_assessment3(candidate_id, discord_username)
                return True
        else:
            print("   ❌ Impossible d'obtenir les données LCP")
        
        return False
    
    def obtenir_metriques_reelles(self, lcp_username):
        """
        RÉCUPÉRATION DES DONNÉES DEPUIS LA VRAIE API LCP
        """
        print(f"   🔌 Connexion à l'API LCP...")
        
        try:
            # Headers avec authentification
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Essayer différents endpoints possibles
            endpoints = [
                f"/api/traders/{lcp_username}/metrics",
                f"/api/traders/{lcp_username}",
                f"/traders/{lcp_username}/metrics", 
                f"/traders/{lcp_username}",
                f"/api/accounts/{lcp_username}",
                f"/accounts/{lcp_username}"
            ]
            
            for endpoint in endpoints:
                url = self.api_url + endpoint
                print(f"   🔌 Tentative: {endpoint}")
                
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ Données reçues de l'API LCP")
                        
                        # Extraire les métriques selon le format de l'API
                        metrics = self.extraire_metriques(data)
                        return metrics
                        
                    elif response.status_code == 404:
                        print(f"   ❌ Endpoint non trouvé: {endpoint}")
                    else:
                        print(f"   ⚠️  Status {response.status_code} pour {endpoint}")
                        
                except requests.exceptions.Timeout:
                    print(f"   ⏱️  Timeout sur {endpoint}")
                except requests.exceptions.ConnectionError:
                    print(f"   🔌 Connection refused sur {endpoint}")
                except Exception as e:
                    print(f"   ❌ Erreur sur {endpoint}: {e}")
            
            # Si aucun endpoint ne fonctionne, essayer sans authentification
            print(f"   🔑 Essai sans authentification...")
            for endpoint in endpoints:
                url = self.api_url + endpoint
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ Données reçues (sans auth)")
                        return self.extraire_metriques(data)
                except:
                    continue
            
            print(f"   ❌ Aucun endpoint API LCP accessible")
            return None
            
        except Exception as e:
            print(f"   ❌ Erreur générale API: {e}")
            return None
    
    def extraire_metriques(self, data):
        """
        Extraire les métriques du format de réponse de l'API LCP
        À adapter selon le VRAI format de l'API
        """
        try:
            # ESSAYER DIFFÉRENTS FORMATS POSSIBLES
            metrics = {}
            
            # Format 1: Structure nested
            if 'data' in data and 'metrics' in data['data']:
                metrics_data = data['data']['metrics']
                metrics = {
                    'profit_percent': metrics_data.get('profitPercentage', 0),
                    'concurrent_trades': metrics_data.get('openPositions', 0),
                    'daily_drawdown': metrics_data.get('dailyDrawdown', 0),
                    'total_drawdown': metrics_data.get('totalDrawdown', 0),
                    'total_trades': metrics_data.get('totalTrades', 0),
                    'avg_trade_size': metrics_data.get('averageTradeSize', 0),
                    'max_trade_size': metrics_data.get('maxTradeSize', 0)
                }
            
            # Format 2: Structure plate
            elif 'profit' in data or 'drawdown' in data:
                metrics = {
                    'profit_percent': data.get('profit', data.get('profitPercentage', 0)),
                    'concurrent_trades': data.get('openTrades', data.get('openPositions', 0)),
                    'daily_drawdown': data.get('dailyDrawdown', data.get('drawdownDaily', 0)),
                    'total_drawdown': data.get('totalDrawdown', data.get('drawdownTotal', 0)),
                    'total_trades': data.get('totalTrades', data.get('tradesCount', 0)),
                    'avg_trade_size': data.get('avgTrade', data.get('averageTradeSize', 0)),
                    'max_trade_size': data.get('maxTrade', data.get('maxTradeSize', 0))
                }
            
            # Format 3: Debug - afficher la structure reçue
            else:
                print(f"   🏗️  Structure API reçue: {list(data.keys())}")
                # Utiliser des valeurs par défaut pour tester
                metrics = {
                    'profit_percent': data.get('profit', 3.5),
                    'concurrent_trades': data.get('openTrades', 2),
                    'daily_drawdown': data.get('dailyDrawdown', 0.8),
                    'total_drawdown': data.get('totalDrawdown', 2.0),
                    'total_trades': data.get('totalTrades', 15),
                    'avg_trade_size': data.get('avgTrade', 250),
                    'max_trade_size': data.get('maxTrade', 500)
                }
            
            # Nettoyer et valider les métriques
            return self.nettoyer_metriques(metrics)
            
        except Exception as e:
            print(f"   ❌ Erreur extraction métriques: {e}")
            # Données simulées en fallback
            return self.metriques_fallback()
    
    def nettoyer_metriques(self, metrics):
        """Nettoyer et formater les métriques"""
        cleaned = {}
        for key, value in metrics.items():
            if value is None:
                cleaned[key] = 0
            else:
                cleaned[key] = float(value)
        return cleaned
    
    def metriques_fallback(self):
        """Métriques de fallback si l'API échoue"""
        print("   ⚠️  Utilisation des métriques de fallback")
        return {
            'profit_percent': 0,
            'concurrent_trades': 0,
            'daily_drawdown': 0,
            'total_drawdown': 0,
            'total_trades': 0,
            'avg_trade_size': 0,
            'max_trade_size': 0
        }
    
    def valider_regles(self, metrics):
        """Valider toutes les règles Assessment 2"""
        erreurs = []
        
        # Profit target +4%
        if metrics['profit_percent'] < ASSESSMENT2_RULES["profit_target"]:
            erreurs.append(f"Profit: {metrics['profit_percent']}% < 4%")
        
        # Max 3 trades simultanés
        if metrics['concurrent_trades'] > ASSESSMENT2_RULES["max_simultaneous_trades"]:
            erreurs.append(f"Trades simultanés: {metrics['concurrent_trades']} > 3")
        
        # Drawdown quotidien 1% max
        if metrics['daily_drawdown'] > ASSESSMENT2_RULES["max_daily_drawdown"]:
            erreurs.append(f"DD quotidien: {metrics['daily_drawdown']}% > 1%")
        
        # Drawdown total 2.5% max
        if metrics['total_drawdown'] > ASSESSMENT2_RULES["max_total_drawdown"]:
            erreurs.append(f"DD total: {metrics['total_drawdown']}% > 2.5%")
        
        # Minimum de trades
        if metrics['total_trades'] < ASSESSMENT2_RULES["min_trades"]:
            erreurs.append(f"Trades: {metrics['total_trades']} < 10")
        
        return {
            "reussi": len(erreurs) == 0,
            "erreurs": erreurs
        }
    
    def afficher_resultats(self, discord_username, metrics, validation):
        """Afficher les résultats de l'analyse"""
        print(f"   📈 Métriques LCP:")
        print(f"      • Profit: {metrics['profit_percent']}%")
        print(f"      • Trades simultanés: {metrics['concurrent_trades']}/3")
        print(f"      • Drawdown quotidien: {metrics['daily_drawdown']}%/1%")
        print(f"      • Drawdown total: {metrics['total_drawdown']}%/2.5%")
        print(f"      • Total trades: {metrics['total_trades']}/10")
        
        if validation["reussi"]:
            print(f"   🎉 {discord_username} → ASSESSMENT 2 RÉUSSI!")
            print(f"   💡 Action: Promouvoir vers Assessment 3")
        else:
            print(f"   ⏳ {discord_username} → En progression")
            print(f"   📝 Améliorations: {', '.join(validation['erreurs'])}")
    
    def mettre_a_jour_assessment3(self, candidate_id, discord_username):
        """Mettre à jour Google Sheets pour Assessment 3"""
        try:
            data = self.sheet.get_all_values()
            for i, row in enumerate(data[1:], start=2):
                if row[0] == candidate_id:
                    self.sheet.update_cell(i, 5, "active_assessment_3")  # Colonne E = status
                    print(f"   📊 Google Sheets mis à jour: {discord_username} → Assessment 3")
                    break
        except Exception as e:
            print(f"   ❌ Erreur mise à jour Sheets: {e}")

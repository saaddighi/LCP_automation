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

# === RÈGLES ASSESSMENT 3 === (Plus strictes que Assessment 2)
ASSESSMENT3_RULES = {
    "profit_target": 6.0,           # +6% (au lieu de +4%)
    "max_simultaneous_trades": 2,   # Max 2 trades simultanés (au lieu de 3)
    "max_daily_drawdown": 0.5,      # 0.5% drawdown quotidien (au lieu de 1%)
    "max_total_drawdown": 1.5,      # 1.5% drawdown total (au lieu de 2.5%)
    "time_window_days": 30,         # 30 jours (au lieu de 21)
    "min_trades": 20,               # Minimum 20 trades (au lieu de 10)
    "consistency_strict": True      # Vérification cohérence renforcée
}

class Assessment3MonitorStandalone:
    def __init__(self, bot, sheet):
        self.sheet = sheet
        self.api_url = LCP_API_URL
        self.api_key = LCP_API_KEY
    
    def surveiller_traders(self):
        """Fonction principale de surveillance Assessment 3"""
        print(f"\n🔍 [{datetime.now()}] SURVEILLANCE ASSESSMENT 3 - PHASE FINALE")
        print("=" * 60)
        print("🎯 Règles renforcées: +6% profit, 0.5% DD quotidien, max 2 trades")
        print("=" * 60)
        
        try:
            data = self.sheet.get_all_values()
            traders_trouves = 0
            traders_reussis = 0
            
            for row in data[1:]:
                if self.est_trader_assessment3(row):
                    traders_trouves += 1
                    reussi = self.analyser_trader(row)
                    if reussi:
                        traders_reussis += 1
            
            print(f"\n" + "=" * 60)
            print(f"📊 RÉCAPITULATIF ASSESSMENT 3:")
            print(f"   • Traders Assessment 3 trouvés: {traders_trouves}")
            print(f"   • Traders éligibles FUNDED: {traders_reussis}")
            print(f"   • Traders en progression: {traders_trouves - traders_reussis}")
            
        except Exception as e:
            print(f"❌ Erreur surveillance Assessment 3: {e}")
    
    def est_trader_assessment3(self, row):
        """Vérifier si le trader est en Assessment 3"""
        return len(row) > 4 and row[4] == "active_assessment_3"
    
    def analyser_trader(self, row):
        discord_username = row[18] if len(row) > 18 else "Inconnu"
        candidate_id = row[0] if len(row) > 0 else "Inconnu"
        lcp_username = row[10] if len(row) > 10 else None
        
        print(f"\n📊 Analyse Assessment 3: {discord_username}")
        print(f"   ID: {candidate_id}")
        print(f"   LCP Username: {lcp_username}")
        
        if not lcp_username:
            print("   ❌ Pas de LCP username dans Google Sheets")
            return False
        
        # Récupérer métriques depuis API LCP
        metrics = self.obtenir_metriques_reelles(lcp_username)
        
        if metrics:
            # Validation des règles STRICTES Assessment 3
            validation = self.valider_regles_assessment3(metrics)
            
            # Afficher résultats
            self.afficher_resultats(discord_username, metrics, validation)
            
            # Si réussi, promouvoir vers FUNDED
            if validation["reussi"]:
                self.promouvoir_funded(candidate_id, discord_username)
                return True
        else:
            print("   ❌ Impossible d'obtenir les données LCP")
        
        return False
    
    def obtenir_metriques_reelles(self, lcp_username):
        """Récupération des données depuis l'API LCP (même méthode que A2)"""
        print(f"   🔌 Connexion à l'API LCP...")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
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
                
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ Données reçues de l'API LCP")
                        return self.extraire_metriques(data)
                        
                except requests.exceptions.Timeout:
                    continue
                except requests.exceptions.ConnectionError:
                    continue
                except Exception as e:
                    continue
            
            # Fallback sans authentification
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
        """Extraire les métriques du format de réponse de l'API LCP"""
        try:
            metrics = {}
            
            # Même logique d'extraction que Assessment 2
            if 'data' in data and 'metrics' in data['data']:
                metrics_data = data['data']['metrics']
                metrics = {
                    'profit_percent': metrics_data.get('profitPercentage', 0),
                    'concurrent_trades': metrics_data.get('openPositions', 0),
                    'daily_drawdown': metrics_data.get('dailyDrawdown', 0),
                    'total_drawdown': metrics_data.get('totalDrawdown', 0),
                    'total_trades': metrics_data.get('totalTrades', 0),
                    'avg_trade_size': metrics_data.get('averageTradeSize', 0),
                    'max_trade_size': metrics_data.get('maxTradeSize', 0),
                    'win_rate': metrics_data.get('winRate', 0),
                    'profit_factor': metrics_data.get('profitFactor', 0)
                }
            
            elif 'profit' in data or 'drawdown' in data:
                metrics = {
                    'profit_percent': data.get('profit', data.get('profitPercentage', 0)),
                    'concurrent_trades': data.get('openTrades', data.get('openPositions', 0)),
                    'daily_drawdown': data.get('dailyDrawdown', data.get('drawdownDaily', 0)),
                    'total_drawdown': data.get('totalDrawdown', data.get('drawdownTotal', 0)),
                    'total_trades': data.get('totalTrades', data.get('tradesCount', 0)),
                    'avg_trade_size': data.get('avgTrade', data.get('averageTradeSize', 0)),
                    'max_trade_size': data.get('maxTrade', data.get('maxTradeSize', 0)),
                    'win_rate': data.get('winRate', data.get('successRate', 0)),
                    'profit_factor': data.get('profitFactor', data.get('pf', 0))
                }
            
            else:
                print(f"   🏗️  Structure API reçue: {list(data.keys())}")
                # Valeurs par défaut pour testing
                metrics = {
                    'profit_percent': data.get('profit', 5.8),
                    'concurrent_trades': data.get('openTrades', 1),
                    'daily_drawdown': data.get('dailyDrawdown', 0.4),
                    'total_drawdown': data.get('totalDrawdown', 1.2),
                    'total_trades': data.get('totalTrades', 22),
                    'avg_trade_size': data.get('avgTrade', 300),
                    'max_trade_size': data.get('maxTrade', 600),
                    'win_rate': data.get('winRate', 65),
                    'profit_factor': data.get('profitFactor', 1.8)
                }
            
            return self.nettoyer_metriques(metrics)
            
        except Exception as e:
            print(f"   ❌ Erreur extraction métriques: {e}")
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
            'max_trade_size': 0,
            'win_rate': 0,
            'profit_factor': 0
        }
    
    def valider_regles_assessment3(self, metrics):
        """Valider les règles STRICTES Assessment 3"""
        erreurs = []
        echec_critique = False
        
        # 1. Profit target +6% (plus strict)
        if metrics['profit_percent'] < ASSESSMENT3_RULES["profit_target"]:
            erreurs.append(f"Profit: {metrics['profit_percent']}% < 6%")
        
        # 2. Max 2 trades simultanés (plus strict)
        if metrics['concurrent_trades'] > ASSESSMENT3_RULES["max_simultaneous_trades"]:
            erreurs.append(f"Trades simultanés: {metrics['concurrent_trades']} > 2")
            echec_critique = True
        
        # 3. Drawdown quotidien 0.5% max (plus strict)
        if metrics['daily_drawdown'] > ASSESSMENT3_RULES["max_daily_drawdown"]:
            erreurs.append(f"DD quotidien: {metrics['daily_drawdown']}% > 0.5%")
            echec_critique = True
        
        # 4. Drawdown total 1.5% max (plus strict)
        if metrics['total_drawdown'] > ASSESSMENT3_RULES["max_total_drawdown"]:
            erreurs.append(f"DD total: {metrics['total_drawdown']}% > 1.5%")
            echec_critique = True
        
        # 5. Minimum 20 trades (plus strict)
        if metrics['total_trades'] < ASSESSMENT3_RULES["min_trades"]:
            erreurs.append(f"Trades: {metrics['total_trades']} < 20")
        
        # 6. Cohérence renforcée
        if not self.verifier_coherence_renforce(metrics):
            erreurs.append("Incohérence trading détectée")
            echec_critique = True
        
        # 7. Win rate minimum 60%
        if metrics.get('win_rate', 0) < 60:
            erreurs.append(f"Win rate: {metrics.get('win_rate', 0)}% < 60%")
        
        # 8. Profit factor minimum 1.5
        if metrics.get('profit_factor', 0) < 1.5:
            erreurs.append(f"Profit factor: {metrics.get('profit_factor', 0)} < 1.5")
        
        return {
            "reussi": len(erreurs) == 0,
            "echec_critique": echec_critique,
            "erreurs": erreurs
        }
    
    def verifier_coherence_renforce(self, metrics):
        """Vérification cohérence RENFORCÉE pour Assessment 3"""
        if metrics['avg_trade_size'] == 0:
            return True
        
        # Trade max <= 2x la moyenne (plus strict que A2)
        ratio_taille = metrics['max_trade_size'] / metrics['avg_trade_size']
        
        # Vérifier consistance du win rate
        win_rate_ok = metrics.get('win_rate', 0) >= 40  # Minimum 40% de win rate
        
        return ratio_taille <= 2.0 and win_rate_ok
    
    def afficher_resultats(self, discord_username, metrics, validation):
        """Afficher les résultats de l'analyse Assessment 3"""
        print(f"   📈 Métriques LCP (Assessment 3):")
        print(f"      • Profit: {metrics['profit_percent']}%/6%")
        print(f"      • Trades simultanés: {metrics['concurrent_trades']}/2")
        print(f"      • DD quotidien: {metrics['daily_drawdown']}%/0.5%")
        print(f"      • DD total: {metrics['total_drawdown']}%/1.5%")
        print(f"      • Total trades: {metrics['total_trades']}/20")
        
        if 'win_rate' in metrics:
            print(f"      • Win rate: {metrics['win_rate']}%/60%")
        if 'profit_factor' in metrics:
            print(f"      • Profit factor: {metrics['profit_factor']}/1.5")
        
        if validation["reussi"]:
            print(f"   🏆 {discord_username} → ASSESSMENT 3 RÉUSSI!")
            print(f"   💰 FÉLICITATIONS - TRADER FUNDED!")
        else:
            print(f"   ⏳ {discord_username} → En progression")
            print(f"   📝 Améliorations nécessaires: {', '.join(validation['erreurs'])}")
    
    def promouvoir_funded(self, candidate_id, discord_username):
        """Promouvoir un trader vers FUNDED (phase finale)"""
        try:
            # 1. Mettre à jour Google Sheets
            self.mettre_a_jour_statut_sheets(candidate_id, "funded")
            
            # 2. Log de succès
            print(f"   🎉 {discord_username} promu TRADER FUNDED!")
            print(f"   💰 Accès aux fonds réels activé!")
            
            # Note: Pour Discord, vous utiliserez vos fonctions existantes
            # depuis le monitoring principal quand il sera intégré
            
        except Exception as e:
            print(f"   ❌ Erreur promotion FUNDED: {e}")
    
    def mettre_a_jour_statut_sheets(self, candidate_id, nouveau_statut):
        """Mettre à jour le statut dans Google Sheets"""
        try:
            data = self.sheet.get_all_values()
            for i, row in enumerate(data[1:], start=2):
                if row[0] == candidate_id:
                    self.sheet.update_cell(i, 5, nouveau_statut)  # Colonne E = status
                    print(f"   📊 Sheets mis à jour: {candidate_id} → {nouveau_statut}")
                    break
        except Exception as e:
            print(f"   ❌ Erreur mise à jour Sheets: {e}")

# Fonction pour démarrer le monitoring Assessment 3
def demarrer_monitoring_assessment3(bot, sheet):
    """Démarrer le monitoring Assessment 3"""
    monitor = Assessment3MonitorStandalone(bot, sheet)
    monitor.surveiller_traders()
    print("🚀 Monitoring Assessment 3 démarré!")
    return monitor


import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot_discord'))

from monitoring_a2 import Assessment2MonitorStandalone
from monitoring_a3 import Assessment3MonitorStandalone
from emailer.email_sheet import sheet

def main():
    print("🚀 MONITORING COMPLET LOTUS CAPITAL")
    print("=" * 50)
    print("📡 Connexion à l'API LCP: http://51.195.222.3:8080")
    print("⏰ Surveillance quotidienne des traders")
    print("=" * 50)
    
    # Monitoring Assessment 2
    print("\n🎯 ASSESSMENT 2")
    monitor_a2 = Assessment2MonitorStandalone(sheet)
    monitor_a2.surveiller_traders()
    
    # Monitoring Assessment 3  
    print("\n🏆 ASSESSMENT 3")
    monitor_a3 = Assessment3MonitorStandalone(None, sheet)  # Pas besoin du bot pour l'instant
    monitor_a3.surveiller_traders()
    
    print("\n" + "=" * 50)
    print("✅ Monitoring complet terminé!")
    print("💡 Pensez à configurer votre clé API LCP")

if __name__ == "__main__":
    main()

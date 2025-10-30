import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot_discord'))

from monitoring_a2 import Assessment2MonitorStandalone
from emailer.email_sheet import sheet

def main():
    print("🚀 MONITORING ASSESSMENT 2 - API LCP RÉELLE")
    print("=" * 50)
    print("📡 Connexion à l'API LCP: http://51.195.222.3:8080")
    print("⏰ Surveillance quotidienne des traders Assessment 2")
    print("=" * 50)
    
    # Créer le monitor
    monitor = Assessment2MonitorStandalone(sheet)
    
    # Lancer la surveillance
    monitor.surveiller_traders()
    
    print("\n" + "=" * 50)
    print("✅ Monitoring terminé!")
    print("💡 Pensez à configurer votre clé API LCP dans monitoring_a2.py")

if __name__ == "__main__":
    main()

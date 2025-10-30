import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import sys
import requests
import threading
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === IMPORTS CORRIGÉS ===
from emailer.email_sheet import sheet
from emailer.mailer import first_assessment_email

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# --- CONFIGURATION ---
COHORTES = {
    "1": {"max_membres": 10, "statut": "ouverte", "role": "Cohorte 1", "salon": "cohorte-1-privee"},
    "2": {"max_membres": 10, "statut": "ouverte", "role": "Cohorte 2", "salon": "cohorte-2-privee"}
}

COHORTE_ACTUELLE = "2"

# --- FAQ ---
FAQ_DATA = {
    "drawdown": {"keywords": ["drawdown", "daily drawdown"], "reponse": "Your daily drawdown limit is 3%. Exceeding it will disqualify you from the current assessment."},
    "assessment": {"keywords": ["assessment"], "reponse": "There are 3 assessments: [1 □ Evaluation, 2 Consistency, 3 □ Funded Phase]. You can view full details here: [link to FAQ]."},
    "platform": {"keywords": ["platform", "broker"], "reponse": "We currently use MT5 and cTrader for trading assessments."},
    "rules": {"keywords": ["rules", "targets"], "reponse": "Each assessment phase has its own profit target and drawdown rules. Check the summary here: [link]."},
    "cohort start": {"keywords": ["cohort start"], "reponse": "Cohort X started on [date]. The next cohort opens on [date]. You'll get notified automatically."}
}

# --- NOTIFICATIONS INTERNES ---
async def notifier_interne(message):
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if "admin" in channel.name.lower() or "log" in channel.name.lower():
                await channel.send(f"🔔 **NOTIFICATION:** {message}")
                return

# --- GESTION DES NOUVELLES CANDIDATURES ---
@tasks.loop(minutes=5)
async def surveiller_formulaires():
    try:
        data = sheet.get_all_values()
        nouvelles_soumissions = 0
        cohorte_pleine = False
        
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= 3:
                email = row[2]
                statut = row[4] if len(row) > 4 else ""
                
                if email and not statut:
                    nouvelles_soumissions += 1
                    cohorte, nouveau_statut = assigner_candidat_automatique()
                    sheet.update_cell(i, 5, nouveau_statut)
                    if cohorte != "waiting":
                        sheet.update_cell(i, 4, cohorte)
        
        if nouvelles_soumissions > 0:
            await notifier_interne(f"New applications: {nouvelles_soumissions}")
            
        for cohorte_id, config in COHORTES.items():
            if config["statut"] == "ouverte":
                membres = compter_membres_cohorte(cohorte_id)
                if membres >= config["max_membres"]:
                    await notifier_interne(f"Cohort fills up: Cohort {cohorte_id} is now full!")
                    COHORTES[cohorte_id]["statut"] = "fermee"
                    cohorte_pleine = True
        
        if cohorte_pleine:
            await notifier_interne("Cohort transitions to closed status")
                    
    except Exception as e:
        print(f"❌ Erreur surveillance: {e}")

def assigner_candidat_automatique():
    cohorte_actuelle = COHORTE_ACTUELLE
    config = COHORTES[cohorte_actuelle]
    
    if config["statut"] == "ouverte":
        membres_actuels = compter_membres_cohorte(cohorte_actuelle)
        if membres_actuels < config["max_membres"]:
            return cohorte_actuelle, "active"
    return "waiting", "waiting"

def compter_membres_cohorte(cohorte):
    data = sheet.get_all_values()
    return sum(1 for row in data[1:] if len(row) > 3 and row[3] == cohorte and row[4] == "active")

# --- AUTO-RÉPONDEUR FAQ ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content_lower = message.content.lower()
    for faq_id, faq in FAQ_DATA.items():
        for keyword in faq['keywords']:
            if keyword in content_lower:
                await message.channel.send(f"**{faq_id.upper()}:** {faq['reponse']}")
                break
    await bot.process_commands(message)

# --- COMMANDES ---
@bot.tree.command(name="help", description="Show all commands")
async def help_command(interaction: discord.Interaction):
    msg = """
**Available Commands:**
`/help` - Shows available commands
`/drawdown` - Drawdown rules  
`/assessment` - Assessment stages info
`/faq` - FAQ page
`/platform` - Platforms used
`/cohort_start` - Shows your cohort status
"""
    await interaction.response.send_message(msg)

# --- NOUVELLES FONCTIONS : GESTION DES RÉSULTATS D'ÉVALUATION ---
async def ajouter_a_assessment2(discord_username):
    """
    Fonction pour ajouter un trader à la Cohorte 2 (Assessment 2) après réussite.
    """
    for guild in bot.guilds:
        for member in guild.members:
            if member.name.lower() == discord_username.lower():
                role = discord.utils.get(guild.roles, name="Cohorte 2")
                salon = discord.utils.get(guild.channels, name="cohorte-2-privee")
                
                if role:
                    await member.add_roles(role)
                if salon:
                    await salon.set_permissions(member, read_messages=True, send_messages=True)
                    await salon.send(f"🎉 **FÉLICITATIONS {member.mention} !**\nTu viens de réussir l’Assessment 1 🚀\nBienvenue dans **l’Assessment 2** !\nDécouvre ton nouvel espace de trading privé.")
                
                try:
                    await member.send("🎉 **Bravo !**\nTu as réussi l’Assessment 1 ✅\nBienvenue dans **l’Assessment 2 🚀**\nTu as maintenant accès à ton salon privé.")
                except:
                    print(f"⚠️ Impossible d’envoyer un message privé à {member.name}")
                print(f"✅ {member.name} ajouté à la Cohorte 2")
                return
    print(f"❌ Aucun membre trouvé avec le pseudo '{discord_username}'")

async def notifier_echec_assessment(discord_username):
    """
    Fonction pour notifier un trader qui a échoué l’Assessment 1.
    """
    for guild in bot.guilds:
        for member in guild.members:
            if member.name.lower() == discord_username.lower():
                try:
                    await member.send(
                        "⚠️ **Résultat de ton évaluation - Assessment 1**\n\n"
                        "Tu n’as pas atteint les objectifs requis cette fois-ci.\n"
                        "Ne te décourage pas 💪 Tu pourras retenter l’évaluation lors de la prochaine cohorte.\n"
                        "Reste connecté sur Discord, tu seras notifié dès qu’une nouvelle session s’ouvrira."
                    )
                    print(f"📩 Message d'échec envoyé à {member.name}")
                except:
                    print(f"⚠️ Impossible d’envoyer un message d'échec à {member.name}")
                return
    print(f"❌ Aucun membre trouvé avec le pseudo Discord '{discord_username}' pour notification d'échec.")

# --- ÉVÉNEMENTS ---
@bot.event
async def on_ready():
    print(f'✅ Bot connecté: {bot.user}')
    surveiller_formulaires.start()
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
    except Exception as e:
        print(f"❌ Erreur synchronisation: {e}")

# --- KEEP-ALIVE REPLIT ---
def ping_self():
    while True:
        try:
            requests.get("https://LCPautomation.mzaouizinab.repl.co", timeout=10)
        except:
            pass
        time.sleep(300)

ping_thread = threading.Thread(target=ping_self)
ping_thread.daemon = True
ping_thread.start()

print("🔄 Auto-ping activé!")

def run_bot():
    bot.run(TOKEN)

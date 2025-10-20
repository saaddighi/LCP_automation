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
from emailer.mailer import yag

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# --- CONFIGURATION ---
COHORTES = {
    "1": {
        "max_membres": 10,
        "statut": "ouverte",
        "role": "Cohorte 1",
        "salon": "cohorte-1-privee"
    },
    "2": {
        "max_membres": 10, 
        "statut": "ouverte",
        "role": "Cohorte 2",
        "salon": "cohorte-2-privee"
    }
}

COHORTE_ACTUELLE = "2"

# --- FAQ ---
FAQ_DATA = {
    "drawdown": {
        "keywords": ["drawdown", "daily drawdown"],
        "reponse": "Your daily drawdown limit is 3%. Exceeding it will disqualify you from the current assessment."
    },
    "assessment": {
        "keywords": ["assessment"],
        "reponse": "There are 3 assessments: [1 □ Evaluation, 2 Consistency, 3 □ Funded Phase]. You can view full details here: [link to FAQ]."
    },
    "platform": {
        "keywords": ["platform", "broker"],
        "reponse": "We currently use MT5 and cTrader for trading assessments."
    },
    "rules": {
        "keywords": ["rules", "targets"],
        "reponse": "Each assessment phase has its own profit target and drawdown rules. Check the summary here: [link]."
    },
    "cohort start": {
        "keywords": ["cohort start"],
        "reponse": "Cohort X started on [date]. The next cohort opens on [date]. You'll get notified automatically."
    }
}

# --- NOTIFICATIONS ---
async def notifier_interne(message):
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if "admin" in channel.name.lower() or "log" in channel.name.lower():
                await channel.send(f"🔔 **NOTIFICATION:** {message}")
                return

# --- SURVEILLANCE FORMULAIRES ---
@tasks.loop(minutes=5)
async def surveiller_formulaires():
    try:
        data = sheet.get_all_values()
        nouvelles_soumissions = 0
        cohorte_pleine = False
        
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= 3:
                email = row[2]  # Colonne C - email
                statut = row[4] if len(row) > 4 else ""  # Colonne E - status
                
                if email and not statut:
                    nouvelles_soumissions += 1
                    cohorte, nouveau_statut = assigner_candidat_automatique()
                    
                    sheet.update_cell(i, 5, nouveau_statut)  # Colonne E - status
                    if cohorte != "waiting":
                        sheet.update_cell(i, 4, cohorte)  # Colonne D - cohort_id
                    
                    # ENVOI D'EMAILS
                    if nouveau_statut == "active":
                        subject = "👋 Welcome to Lotus Capital!"
                        body = f"Congratulations! You've been accepted into Cohort {cohorte}. Join our Discord to start."
                        yag.send(to=email, subject=subject, contents=body)
                    else:
                        subject = "Application Status - Waitlist"
                        body = "Thanks for applying! Current cohort is full. We'll notify you when next cohort opens."
                        yag.send(to=email, subject=subject, contents=body)
        
        # NOTIFICATIONS
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

# --- AUTO-RÉPONDEUR ---
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
    commands_list = """
**Available Commands:**
`/help` - Shows available commands & FAQ list
`/drawdown` - Returns current drawdown limit and rule explanation  
`/assessment` - Lists current phase, targets, and progression
`/faq` - Sends link to complete FAQ page
`/platform` - Returns current trading platform(s) used
`/cohort_start` - Displays user's assigned cohort and status

**FAQ Keywords (type in chat):**
drawdown, assessment, platform, rules, targets, cohort start
"""
    await interaction.response.send_message(commands_list)

@bot.tree.command(name="drawdown", description="Returns current drawdown limit and rule explanation")
async def drawdown(interaction: discord.Interaction):
    response = "Your daily drawdown limit is 3%. Exceeding it will disqualify you from the current assessment."
    await interaction.response.send_message(response)

@bot.tree.command(name="assessment", description="Lists current phase, targets, and progression")
async def assessment(interaction: discord.Interaction):
    response = "There are 3 assessments: [1 □ Evaluation, 2 Consistency, 3 □ Funded Phase]. You can view full details here: [link to FAQ]."
    await interaction.response.send_message(response)

@bot.tree.command(name="platform", description="Returns current trading platform(s) used")
async def platform(interaction: discord.Interaction):
    response = "We currently use MT5 and cTrader for trading assessments."
    await interaction.response.send_message(response)

@bot.tree.command(name="faq", description="Sends link to complete FAQ page")
async def faq(interaction: discord.Interaction):
    response = "Complete FAQ: https://example.com/faq"
    await interaction.response.send_message(response)

@bot.tree.command(name="cohort_start", description="Displays user's assigned cohort and status")
async def cohort_start(interaction: discord.Interaction):
    user_discord_id = str(interaction.user.id)
    
    data = sheet.get_all_values()
    user_cohort = None
    user_status = None
    
    # Rechercher par Discord ID dans colonne P (16)
    for row in data[1:]:
        if len(row) > 15 and row[15] == user_discord_id:
            user_cohort = row[3] if len(row) > 3 else None  # Colonne D
            user_status = row[4] if len(row) > 4 else None  # Colonne E
            break
    
    if user_cohort and user_status == "active":
        response = f"**Status: ACTIVE**\n**Assigned to: Cohort {user_cohort}**"
    else:
        response = "**Status: WAITING**\nYou'll be notified when your cohort opens."
    
    await interaction.response.send_message(response)

# --- SYSTÈME DE GRADUATION ---
@bot.tree.command(name="close_cohort", description="Close current cohort and move to alumni")
@app_commands.default_permissions(administrator=True)
async def close_cohort(interaction: discord.Interaction, cohorte: str):
    if cohorte not in COHORTES:
        await interaction.response.send_message("❌ Cohort not found", ephemeral=True)
        return
    
    COHORTES[cohorte]["statut"] = "fermee"
    
    data = sheet.get_all_values()
    waiting_candidates = []
    
    for row in data[1:]:
        if len(row) > 4 and row[4] == "waiting":  # Colonne E
            waiting_candidates.append(row[2])  # Colonne C - email
    
    await notifier_interne(f"Cohort transitions to closed status: Cohort {cohorte}")
    await notifier_interne(f"New cohort opening: {len(waiting_candidates)} waiting candidates notified")
    
    response = f"**Cohort {cohorte} closed successfully!**\n{len(waiting_candidates)} waiting candidates notified."
    await interaction.response.send_message(response)

# --- ÉVÉNEMENTS ---
@bot.event
async def on_ready():
    print(f'✅ Bot connecté: {bot.user}')
    surveiller_formulaires.start()
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
        for cmd in synced:
            print(f"   - /{cmd.name}")
    except Exception as e:
        print(f"❌ Erreur synchronisation: {e}")

@bot.event
async def on_member_join(member):
    try:
        user_discord_name = member.name  # Pseudo Discord
        user_discord_id = str(member.id)
        
        print(f"🔍 NOUVEAU MEMBRE: {user_discord_name}")
        
        data = sheet.get_all_values()
        candidat_trouve = None
        ligne_index = None
        
        # === RECHERCHE AUTOMATIQUE PAR PSEUDO ===
        for i, row in enumerate(data[1:], start=2):
            if len(row) > 18:  # Colonne S - Discord username
                discord_username_in_sheet = row[18].strip().lower()
                current_username = user_discord_name.lower()
                
                print(f"🔍 Comparaison: '{discord_username_in_sheet}' vs '{current_username}'")
                
                if discord_username_in_sheet == current_username:
                    candidat_trouve = row
                    ligne_index = i
                    print(f"✅ CANDIDAT TROUVÉ ligne {i}")
                    break
        
        if candidat_trouve:
            # Mettre à jour le Discord ID
            if len(candidat_trouve) > 15:
                sheet.update_cell(ligne_index, 16, user_discord_id)
            
            statut = candidat_trouve[4] if len(candidat_trouve) > 4 else "waiting"
            cohorte = candidat_trouve[3] if len(candidat_trouve) > 3 else "waiting"
            
            print(f"📊 Statut: {statut}, Cohorte: {cohorte}")
            
            # === MESSAGE DE BIENVENUE POUR TOUS ===
            await member.send("🎉 **BIENVENUE SUR LOTUS CAPITAL !**\n\nNous sommes ravis de vous accueillir dans notre communauté de traders !")
            
            if statut == "active" and cohorte and cohorte != "waiting":
                # Assigner rôle et salon privé
                role = discord.utils.get(member.guild.roles, name=f"Cohorte {cohorte}")
                salon = discord.utils.get(member.guild.channels, name=f"cohorte-{cohorte}-privee")
                
                if role:
                    await member.add_roles(role)
                    if salon:
                        await salon.set_permissions(member, read_messages=True, send_messages=True)
                        
                        # === MESSAGE DANS LE SALON PRIVÉ ===
                        await salon.send(f"🎉 **BIENVENUE {member.mention} DANS LA COHORTE {cohorte} !**\n\nNous sommes ravis de vous accueillir dans votre espace de trading privé ! 📈\n\nN'hésitez pas à vous présenter et à explorer les ressources disponibles. Bon trading ! 🚀")
                    
                    await member.send(f"✅ **ACCÈS ACTIVÉ !**\n\nVous avez été automatiquement assigné à la **Cohort {cohorte}** et avez maintenant accès à votre salon privé.\n\nUtilisez `/help` pour découvrir toutes les commandes disponibles.")
                    print(f"✅ Rôle assigné: Cohorte {cohorte}")
                else:
                    await member.send("⚠️ **Rôle non trouvé** - Contactez l'administration")
                    print(f"❌ Rôle non trouvé: Cohorte {cohorte}")
            else:
                await member.send("⏳ **STATUT : En attente**\n\nVous êtes actuellement sur liste d'attente. Nous vous notifierons dès qu'une place se libère dans une cohorte.\n\nEn attendant, utilisez `/help` pour voir les informations générales.")
        else:
            await member.send("❌ **PSEUDO NON TROUVÉ**\n\nVotre pseudo Discord ne correspond à aucune candidature dans notre base.\n\nAssurez-vous que :\n• Votre pseudo Discord est exactement le même que dans votre candidature\n• Vous avez bien reçu l'email d'acceptation\n\nContactez l'administration en cas de problème.")
            print(f"❌ Aucun candidat trouvé pour: {user_discord_name}")
            
    except Exception as e:
        print(f"💥 ERREUR CRITIQUE onboarding: {e}")
        await member.send("⚠️ **Erreur système** - Contactez l'administration")

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

bot.run(TOKEN)

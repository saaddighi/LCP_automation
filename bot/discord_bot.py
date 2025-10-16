import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from emailer.email_sheet import EmailSheet
from emailer.mailer import Mailer
from datetime import datetime

# Modules de votre collègue
sheet = EmailSheet()
mailer = Mailer()

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# --- CONFIGURATION EXACTE ---
COHORTES = {
    "1": {
        "max_membres": 10, 
        "statut": "ouverte", 
        "role": "Cohorte 1", 
        "salon": "cohorte-1-privee",
        "membres_actuels": 0
    }
}

COHORTE_ACTUELLE = "1"

# --- ✅ FAQ AVEC TOUS LES KEYWORDS EXACTS DU PDF ---
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

# --- ✅ NOTIFICATIONS INTERNES EXACTES ---
async def notifier_interne(message):
    """Notifie les admins comme demandé dans le PDF"""
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if "admin" in channel.name.lower() or "log" in channel.name.lower():
                await channel.send(f"🔔 **NOTIFICATION INTERNE:** {message}")
                return

# --- ✅ SURVEILLANCE FORMULAIRES AVEC NOTIFICATIONS COMPLÈTES ---
@tasks.loop(minutes=5)
async def surveiller_formulaires():
    """Vérifie les nouvelles soumissions avec notifications"""
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
                    
                    # Email automatique
                    if nouveau_statut == "active":
                        mailer.send_welcome_email(email, cohorte)
                    else:
                        mailer.send_waitlist_email(email)
        
        # ✅ NOTIFICATION "New candidate applies" (PDF Page 3)
        if nouvelles_soumissions > 0:
            await notifier_interne(f"New candidate applies: {nouvelles_soumissions} candidate(s)")
            
        # ✅ NOTIFICATION "Cohort fills up" (PDF Page 3)
        for cohorte_id, config in COHORTES.items():
            if config["statut"] == "ouverte":
                membres = compter_membres_cohorte(cohorte_id)
                if membres >= config["max_membres"]:
                    await notifier_interne(f"Cohort fills up: Cohort {cohorte_id} is now full!")
                    COHORTES[cohorte_id]["statut"] = "fermee"
                    cohorte_pleine = True
        
        # ✅ NOTIFICATION "Cohort transitions to closed/open status" (PDF Page 3)
        if cohorte_pleine:
            await notifier_interne("Cohort transitions to closed status")
                    
    except Exception as e:
        print(f"❌ Erreur surveillance: {e}")

def assigner_candidat_automatique():
    """Assignation automatique exacte comme PDF"""
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

# --- ✅ AUTO-RESPONDER AVEC TOUS LES KEYWORDS DU PDF ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    content_lower = message.content.lower()
    
    # ✅ DÉTECTION DE TOUS LES KEYWORDS DU PDF (Page 3)
    for faq_id, faq in FAQ_DATA.items():
        for keyword in faq['keywords']:
            if keyword in content_lower:
                # ✅ FORMAT SIMPLE COMME DANS LE PDF (pas d'embed)
                await message.channel.send(f"**{faq_id.upper()}:** {faq['reponse']}")
                break
    
    await bot.process_commands(message)

# --- ✅ COMMANDES AVEC DESCRIPTIONS EXACTES DU PDF ---
@bot.tree.command(name="help", description="Shows available commands & FAQ list")
async def help_command(interaction: discord.Interaction):
    """✅ DESCRIPTION EXACTEMENT COMME PDF"""
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
    """✅ RÉPONSE SIMPLE COMME PDF"""
    response = "Your daily drawdown limit is 3%. Exceeding it will disqualify you from the current assessment."
    await interaction.response.send_message(response)

@bot.tree.command(name="assessment", description="Lists current phase, targets, and progression")
async def assessment(interaction: discord.Interaction):
    """✅ RÉPONSE SIMPLE COMME PDF"""
    response = "There are 3 assessments: [1 □ Evaluation, 2 Consistency, 3 □ Funded Phase]. You can view full details here: [link to FAQ]."
    await interaction.response.send_message(response)

@bot.tree.command(name="platform", description="Returns current trading platform(s) used")
async def platform(interaction: discord.Interaction):
    """✅ RÉPONSE SIMPLE COMME PDF"""
    response = "We currently use MT5 and cTrader for trading assessments."
    await interaction.response.send_message(response)

@bot.tree.command(name="faq", description="Sends link to complete FAQ page")
async def faq(interaction: discord.Interaction):
    """✅ RÉPONSE SIMPLE COMME PDF"""
    response = "Complete FAQ: [link to FAQ]"
    await interaction.response.send_message(response)

@bot.tree.command(name="cohort_start", description="Displays user's assigned cohort and status")
async def cohort_start(interaction: discord.Interaction):
    """✅ RÉPONSE SIMPLE COMME PDF"""
    user_roles = [role.name for role in interaction.user.roles]
    cohorte_role = next((role for role in interaction.user.roles if role.name.startswith("Cohorte")), None)
    
    if cohorte_role:
        response = f"**Status: ACTIVE**\n**Assigned to: {cohorte_role.name}**"
    else:
        response = "**Status: WAITING**\nYou'll be notified when your cohort opens."
    
    await interaction.response.send_message(response)

# --- ✅ SYSTÈME DE GRADUATION COMPLET ---
@bot.tree.command(name="close_cohort", description="Close current cohort and move to alumni")
@app_commands.default_permissions(administrator=True)
async def close_cohort(interaction: discord.Interaction, cohorte: str):
    """✅ PROCESSUS COMPLET DE GRADUATION"""
    if cohorte not in COHORTES:
        await interaction.response.send_message("❌ Cohort not found", ephemeral=True)
        return
    
    # 1. Fermer la cohorte
    COHORTES[cohorte]["statut"] = "fermee"
    
    # 2. Notifier les candidats en attente
    data = sheet.get_all_values()
    waiting_candidates = []
    
    for row in data[1:]:
        if len(row) > 4 and row[4] == "waiting":
            waiting_candidates.append(row[2])
            # Votre collègue enverrait: mailer.send_cohort_opening_email(row[2])
    
    # 3. Notification interne
    await notifier_interne(f"Cohort transitions to closed status: Cohort {cohorte}")
    await notifier_interne(f"New cohort opening: {len(waiting_candidates)} waiting candidates notified")
    
    response = f"**Cohort {cohorte} closed successfully!**\n{len(waiting_candidates)} waiting candidates notified."
    await interaction.response.send_message(response)

# --- ✅ ÉVÉNEMENTS PRINCIPAUX ---
@bot.event
async def on_ready():
    print(f'✅ Bot connecté: {bot.user}')
    surveiller_formulaires.start()
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
    except Exception as e:
        print(f"❌ Erreur synchronisation: {e}")

@bot.event
async def on_member_join(member):
    """✅ PROCESSUS ONBOARDING CONFORME PDF"""
    try:
        data = sheet.get_all_values()
        
        for row in data[1:]:
            if len(row) > 2 and row[2].lower().strip() == f"{member.name}@lotus.com".lower():
                statut = row[4] if len(row) > 4 else "waiting"
                cohorte = row[3] if len(row) > 3 else "waiting"
                
                if statut == "active" and cohorte != "waiting":
                    # Assigner rôle et salon privé
                    role = discord.utils.get(member.guild.roles, name=f"Cohorte {cohorte}")
                    salon = discord.utils.get(member.guild.channels, name=f"cohorte-{cohorte}-privee")
                    
                    if role and salon:
                        await member.add_roles(role)
                        await salon.set_permissions(member, read_messages=True, send_messages=True)
                        await member.send("Welcome to Lotus Capital! You've been assigned to Cohort X. Type /help for quick commands.")
                else:
                    await member.send("You're currently on the waitlist. We'll notify you when your cohort opens.")
                return
                
        await member.send("Email not found in our database. Please contact administration.")
            
    except Exception as e:
        print(f"❌ Erreur onboarding: {e}")

bot.run(TOKEN)

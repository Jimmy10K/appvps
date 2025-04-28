import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv
import os
import signal
import sys
import time

# Charger les variables d'environnement
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))

print(f"🔑 Token du bot : {TELEGRAM_BOT_TOKEN}")
print(f"📱 Chat ID : {TELEGRAM_CHAT_ID}")

# Variable pour gérer l'arrêt propre
should_stop = False

async def start(update, context):
    await update.message.reply_text('👋 Bonjour! Le bot fonctionne.')

def signal_handler(signum, frame):
    global should_stop
    print("\n⏳ Arrêt du bot en cours...")
    should_stop = True

async def main():
    try:
        # Configurer le gestionnaire de signal
        signal.signal(signal.SIGINT, signal_handler)
        
        print("🚀 Démarrage du bot...")
        
        # Test de connexion
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        me = await bot.get_me()
        print(f"✅ Connecté en tant que : {me.username}")
        
        # Configuration de l'application
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Ajout des commandes
        app.add_handler(CommandHandler("start", start))
        
        # Démarrage
        print("📡 Démarrage du polling...")
        
        # Démarrer le polling dans une tâche séparée
        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            
            print("✅ Bot prêt à recevoir des commandes")
            
            try:
                # Boucle principale
                while not should_stop:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            finally:
                # Arrêt propre
                print("🛑 Arrêt du bot...")
                await app.stop()
                await app.shutdown()
        
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
    finally:
        print("✅ Bot arrêté proprement")

if __name__ == '__main__':
    try:
        # Attendre un peu pour s'assurer que les anciennes instances sont arrêtées
        print("⏳ Attente de 5 secondes pour s'assurer que les anciennes instances sont arrêtées...")
        time.sleep(5)
        
        # Démarrer le bot
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
    sys.exit(0) 
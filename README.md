# Biglobe Validator

Un validateur SMTP professionnel pour les comptes Biglobe.

## Fonctionnalités
- Validation Biglobe rapide et fiable
- Connexion sécurisée SSL/TLS
- Support du format email:password
- Résultats sauvegardés proprement
- Multi-threading pour plus de vitesse
- Notifications Telegram en temps réel
- Statistiques détaillées

## Installation sur VPS Debian 12
```bash
# Mise à jour du système
apt update && apt upgrade -y

# Installation des dépendances
apt install python3 python3-pip python3-venv git -y

# Création du dossier
mkdir -p /opt/biglobe
cd /opt/biglobe

# Téléchargement du programme
wget https://raw.githubusercontent.com/JYMMI10K/biglobe/main/main.py

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances Python
pip install python-telegram-bot

# Création du fichier de configuration
nano .env
```

## Configuration
Créez un fichier `.env` avec :
```
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id
```

## Utilisation
```bash
python3 main.py
```

## Service Systemd
```bash
# Création du service
nano /etc/systemd/system/biglobe.service
```

Contenu du service :
```ini
[Unit]
Description=Biglobe Validator Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/biglobe
Environment=PYTHONPATH=/opt/biglobe
ExecStart=/opt/biglobe/venv/bin/python3 /opt/biglobe/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Commandes utiles
```bash
# Démarrer le service
systemctl start biglobe

# Voir les logs
journalctl -u biglobe -f

# Arrêter le service
systemctl stop biglobe

# Redémarrer le service
systemctl restart biglobe

# Voir le statut
systemctl status biglobe
```

## Support
Pour toute question ou support : @JYMMI10K

# Bot Telegram

Ce projet contient un bot Telegram simple qui permet d'envoyer des messages à un chat spécifique.

## Configuration

1. Assurez-vous d'avoir Python 3 installé sur votre système
2. Installez les dépendances nécessaires :
   ```bash
   pip3 install --break-system-packages python-telegram-bot
   ```

## Configuration du Bot

Le fichier `bot.py` contient deux variables importantes à configurer :

- `TELEGRAM_BOT_TOKEN` : Le token de votre bot Telegram (obtenu via @BotFather)
- `TELEGRAM_CHAT_ID` : L'ID du chat où vous voulez envoyer les messages

## Utilisation

Pour envoyer un message, vous pouvez :

1. Exécuter directement le script :
   ```bash
   python3 bot.py
   ```
   Cela enverra un message de test.

2. Importer et utiliser la fonction `send_message` dans votre code :
   ```python
   from bot import send_message
   send_message("Votre message ici")
   ```

## Utilisation depuis Telegram

1. **Commandes du Bot** :
   - `/start` - Démarrer le bot
   - `/help` - Afficher l'aide
   - `/send <message>` - Envoyer un message
   - `/status` - Vérifier le statut du bot

2. **Exemples d'utilisation** :
   ```
   /send Bonjour, ceci est un test
   /status
   ```

3. **Format des messages** :
   - Texte simple : `/send Hello`
   - Texte avec formatage : `/send *Gras* _Italique_ `code``
   - Messages longs : `/send Votre message sur plusieurs lignes`

4. **Gestion des erreurs** :
   - Si le message est trop long, le bot vous avertira
   - En cas d'erreur de connexion, le bot vous informera
   - Les messages invalides seront rejetés avec une explication

## Utilisation sur Telegram

1. **Création du Bot** :
   - Ouvrez Telegram et cherchez @BotFather
   - Envoyez `/newbot`
   - Suivez les instructions pour créer votre bot
   - Copiez le token fourni par BotFather

2. **Obtenir le Chat ID** :
   - Ajoutez votre bot à un groupe ou démarrez une conversation privée
   - Envoyez un message au bot
   - Visitez `https://api.telegram.org/bot<votre_token>/getUpdates`
   - Cherchez "chat":{"id": dans la réponse

3. **Permissions du Bot** :
   - Dans un groupe, assurez-vous que le bot a les permissions :
     - Envoyer des messages
     - Lire les messages
   - Pour un chat privé, aucune configuration supplémentaire n'est nécessaire

4. **Test du Bot** :
   - Envoyez un message au bot
   - Vérifiez que vous recevez bien les notifications
   - Si le bot ne répond pas, vérifiez :
     - Le token est correct
     - Le chat ID est correct
     - Le bot est bien ajouté au chat

## Fonctionnalités

- Envoi de messages texte simples
- Support asynchrone pour une meilleure performance
- Configuration facile via les variables d'environnement
- Commandes interactives depuis Telegram
- Support du formatage Markdown
- Gestion des erreurs en temps réel

## Sécurité

- Ne partagez jamais votre token de bot
- Gardez votre chat ID privé
- Utilisez des variables d'environnement pour les informations sensibles en production

# Biglobe Validator Bot

Bot Telegram pour valider des combos Biglobe.

## Installation sur Debian

1. Téléchargez le code :
```bash
wget https://github.com/votre-username/biglobe-validator/archive/main.zip
unzip main.zip
cd biglobe-validator-main
```

2. Exécutez le script d'installation :
```bash
chmod +x install_debian.sh
./install_debian.sh
```

3. Configurez le fichier `.env` :
```bash
nano .env
```
Remplissez les informations suivantes :
```
TELEGRAM_BOT_TOKEN=votre_token_bot
TELEGRAM_CHAT_ID=votre_chat_id
```

4. Lancez le bot :
```bash
./start.sh
```

## Fonctionnalités

- Validation de combos Biglobe
- Statistiques en temps réel
- Gestion des erreurs SMTP
- Interface Telegram simple

## Dépendances

- Python 3.8 ou supérieur
- Bibliothèques Python (voir requirements.txt)
- Accès à un serveur SMTP

## Utilisation

1. Envoyez la commande `/combo` au bot
2. Envoyez un fichier texte contenant les combos
3. Le bot traitera les combos et enverra les résultats

## Support

Pour toute question ou problème, contactez @JYMMI10K sur Telegram.


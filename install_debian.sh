#!/bin/bash

# Mise à jour du système
sudo apt-get update
sudo apt-get upgrade -y

# Installation des dépendances système
sudo apt-get install -y python3 python3-pip python3-venv git

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances Python
pip install --upgrade pip
pip install -r requirements.txt

# Création du fichier .env
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env
echo "TELEGRAM_CHAT_ID=your_chat_id_here" >> .env

# Rendre le script d'installation exécutable
chmod +x start.sh

echo "Installation terminée !"
echo "1. Modifiez le fichier .env avec vos informations"
echo "2. Lancez le bot avec : ./start.sh" 
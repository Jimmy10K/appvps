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

# Demande des informations Telegram
read -p "Entrez votre token Telegram Bot: " BOT_TOKEN
read -p "Entrez votre Chat ID Telegram: " CHAT_ID

# Création du fichier .env
echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" > .env
echo "TELEGRAM_CHAT_ID=$CHAT_ID" >> .env

# Rendre le script d'installation exécutable
chmod +x start.sh

echo "Installation terminée !"
echo "Le fichier .env a été configuré avec vos informations"
echo "Lancez le bot avec : ./start.sh" 

#!/bin/bash

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Fonction pour afficher les messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

# Nettoyage complet de l'ancienne installation
print_message "Nettoyage de l'ancienne installation..."

# Arrêt du service
print_message "Arrêt du service biglobe..."
sudo systemctl stop biglobe

# Suppression des processus Python
print_message "Suppression des processus Python..."
sudo pkill -f "python3 main.py"

# Suppression des fichiers temporaires
print_message "Suppression des fichiers temporaires..."
sudo rm -f /tmp/tmp*
sudo rm -f /home/appvps/tmp*

# Suppression de l'ancien service
print_message "Suppression de l'ancien service..."
sudo systemctl disable biglobe
sudo rm -f /etc/systemd/system/biglobe.service

# Suppression de l'ancien environnement virtuel
print_message "Suppression de l'ancien environnement virtuel..."
sudo rm -rf /home/appvps/venv

# Création du répertoire de travail
print_message "Création du répertoire de travail..."
sudo mkdir -p /home/appvps
sudo chown -R root:root /home/appvps
sudo chmod -R 755 /home/appvps
cd /home/appvps

# Installation des dépendances système
print_message "Installation des dépendances système..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Création de l'environnement virtuel
print_message "Création de l'environnement virtuel..."
sudo python3 -m venv venv
sudo chown -R root:root venv
sudo chmod -R 755 venv
source venv/bin/activate

# Installation des dépendances Python
print_message "Installation des dépendances Python..."
sudo pip install python-telegram-bot==20.7 python-dotenv requests

# Configuration du service systemd
print_message "Configuration du service systemd..."
sudo tee /etc/systemd/system/biglobe.service << 'EOL'
[Unit]
Description=Biglobe Validator Service
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/home/appvps
Environment=PATH=/home/appvps/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/home/appvps/venv/bin/python3 /home/appvps/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Configuration des permissions
print_message "Configuration des permissions..."
sudo chown -R root:root /home/appvps
sudo chmod -R 755 /home/appvps
sudo chmod 644 /etc/systemd/system/biglobe.service

# Rechargement de systemd
print_message "Rechargement de systemd..."
sudo systemctl daemon-reload

# Démarrage du service
print_message "Démarrage du service..."
sudo systemctl enable biglobe
sudo systemctl start biglobe

# Vérification du statut
print_message "Vérification du statut du service..."
sleep 2
sudo systemctl status biglobe

print_message "Installation terminée !"
print_warning "N'oubliez pas de configurer le fichier .env avec vos informations Telegram" 

#!/bin/bash

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_message() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 n'est pas installé. Veuillez l'installer."
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 n'est pas installé. Veuillez l'installer."
    exit 1
fi

# Vérifier si le fichier known_hosts existe et contient l'ancienne clé
if [ -f ~/.ssh/known_hosts ]; then
    if grep -q "96.9.124.6" ~/.ssh/known_hosts; then
        print_message "Une ancienne clé SSH existe pour ce serveur."
        read -p "Voulez-vous supprimer l'ancienne clé ? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ssh-keygen -R 96.9.124.6
            print_success "Ancienne clé supprimée."
        fi
    fi
fi

# Demander uniquement les informations Telegram
print_message "Configuration du bot Telegram :"
read -p "Entrez votre TELEGRAM_BOT_TOKEN : " TELEGRAM_BOT_TOKEN
read -p "Entrez votre TELEGRAM_CHAT_ID : " TELEGRAM_CHAT_ID

# Créer le fichier .env
cat > .env << EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
EOF

print_success "Fichier .env créé avec succès."

# Créer un environnement virtuel s'il n'existe pas
if [ ! -d "venv" ]; then
    print_message "Création de l'environnement virtuel..."
    python3 -m venv venv
    print_success "Environnement virtuel créé"
fi

# Activer l'environnement virtuel
print_message "Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
print_message "Installation des dépendances..."
pip3 install -r requirements.txt

# Configuration du service systemd
print_message "Configuration du service systemd..."
cat > /etc/systemd/system/biglobe.service << EOF
[Unit]
Description=Biglobe Validator Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
Environment=PYTHONPATH=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 $(pwd)/main.py
Restart=always
RestartSec=10
StartLimitBurst=0

[Install]
WantedBy=multi-user.target
EOF

# Configuration SSH pour éviter les déconnexions
print_message "Configuration SSH..."
cat >> /etc/ssh/sshd_config << EOF
ClientAliveInterval 60
ClientAliveCountMax 3
EOF

# Redémarrage des services
print_message "Redémarrage des services..."
systemctl daemon-reload
systemctl restart sshd

# Installation de screen
print_message "Installation de screen..."
apt install screen -y

# Création de la session screen
print_message "Création de la session screen..."
screen -dmS biglobe bash -c 'cd $(pwd) && source venv/bin/activate && python3 main.py'

# Activation et démarrage du service
print_message "Activation du service..."
systemctl enable biglobe
systemctl start biglobe

# Vérification du statut
print_message "Vérification du statut..."
systemctl status biglobe

print_success "Configuration terminée !"
echo "📝 Commandes utiles :"
echo "   - Voir les logs : journalctl -u biglobe -f"
echo "   - Redémarrer : systemctl restart biglobe"
echo "   - Arrêter : systemctl stop biglobe"
echo "   - Voir la session screen : screen -r biglobe"

# En cas d'erreur
if [ $? -ne 0 ]; then
    print_error "Le bot a rencontré une erreur. Vérifiez les logs ci-dessus."
    deactivate
    exit 1
fi

# Désactiver l'environnement virtuel
deactivate 
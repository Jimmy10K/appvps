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

# Vérifier si le fichier .env existe
if [ ! -f .env ]; then
    print_error "Le fichier .env n'existe pas. Veuillez le créer avec les variables suivantes :"
    echo "TELEGRAM_BOT_TOKEN=votre_token_ici"
    echo "TELEGRAM_CHAT_ID=votre_chat_id_ici"
    exit 1
fi

# Vérifier si les variables d'environnement sont définies
if ! grep -q "TELEGRAM_BOT_TOKEN" .env || ! grep -q "TELEGRAM_CHAT_ID" .env; then
    print_error "Les variables TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID doivent être définies dans le fichier .env"
    exit 1
fi

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
echo "⚙️ Configuration du service systemd..."
cat > /etc/systemd/system/biglobe.service << EOF
[Unit]
Description=Biglobe Validator Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=root
WorkingDirectory=/opt/biglobe
Environment=PYTHONPATH=/opt/biglobe
ExecStart=/opt/biglobe/venv/bin/python3 /opt/biglobe/main.py
Restart=always
RestartSec=10
StartLimitBurst=0

[Install]
WantedBy=multi-user.target
EOF

# Configuration SSH pour éviter les déconnexions
echo "🔌 Configuration SSH..."
cat >> /etc/ssh/sshd_config << EOF
ClientAliveInterval 60
ClientAliveCountMax 3
EOF

# Redémarrage des services
echo "🔄 Redémarrage des services..."
systemctl daemon-reload
systemctl restart sshd

# Installation de screen
echo "📺 Installation de screen..."
apt install screen -y

# Création de la session screen
echo "🖥️ Création de la session screen..."
screen -dmS biglobe bash -c 'cd /opt/biglobe && source venv/bin/activate && python3 main.py'

# Activation et démarrage du service
echo "🚀 Activation du service..."
systemctl enable biglobe
systemctl start biglobe

# Vérification du statut
echo "📊 Vérification du statut..."
systemctl status biglobe

echo "✅ Configuration terminée !"
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
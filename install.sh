#!/bin/bash
# Enhanced Wazuh Telegram Integration Installer
# Author Mursal Aliyev

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

WAZUH_PATH="/var/ossec"
INTEGRATION_PATH="$WAZUH_PATH/integrations"
CONFIG_FILE="$INTEGRATION_PATH/telegram_config.json"
LOG_FILE="$WAZUH_PATH/logs/telegram_integration.log"

echo -e "${BLUE}========================================${NC}"
echo -e "${PURPLE}Enhanced Wazuh Telegram Integration${NC}"
echo -e "${PURPLE}Author Mursal Aliyev${NC}"
echo -e "${BLUE}========================================${NC}"

# Check root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Must run as root${NC}"
   exit 1
fi

# Check Wazuh
if [ ! -d "$WAZUH_PATH" ]; then
    echo -e "${RED}❌ Wazuh not found at $WAZUH_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Wazuh found${NC}"

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
$WAZUH_PATH/framework/python/bin/python3 -m pip install requests urllib3

# Create directories
mkdir -p "$INTEGRATION_PATH"
mkdir -p "$(dirname "$LOG_FILE")"

# Download files if not present
if [ ! -f "custom-telegram.py" ]; then
    echo -e "${YELLOW}📥 Downloading integration files...${NC}"
    curl -sSL https://raw.githubusercontent.com/mursalaliyev/enhanced-wazuh-telegram/main/custom-telegram.py -o custom-telegram.py
    curl -sSL https://raw.githubusercontent.com/mursalaliyev/enhanced-wazuh-telegram/main/custom-telegram -o custom-telegram
fi

# Copy files
echo -e "${YELLOW}📁 Installing files...${NC}"
cp custom-telegram "$INTEGRATION_PATH/"
cp custom-telegram.py "$INTEGRATION_PATH/"

# Set permissions
echo -e "${YELLOW}🔐 Setting permissions...${NC}"
chown root:wazuh "$INTEGRATION_PATH/custom-telegram"*
chmod 750 "$INTEGRATION_PATH/custom-telegram"*

# Create config
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚙️ Creating config...${NC}"
    cat > "$CONFIG_FILE" << 'EOF'
{
  "chat_id": "",
  "parse_mode": "HTML",
  "disable_notification": false,
  "rate_limit_seconds": 1,
  "max_message_length": 4096,
  "severity_levels": {
    "low": [0, 1, 2],
    "medium": [3, 4, 5, 6, 7], 
    "high": [8, 9, 10, 11],
    "critical": [12, 13, 14, 15]
  }
}
EOF
    chown root:wazuh "$CONFIG_FILE"
    chmod 640 "$CONFIG_FILE"
fi

# Setup logging
touch "$LOG_FILE"
chown wazuh:wazuh "$LOG_FILE"
chmod 640 "$LOG_FILE"

echo -e "${GREEN}🎉 Installation complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Edit $CONFIG_FILE - add your chat_id"
echo -e "2. Add integration to $WAZUH_PATH/etc/ossec.conf"
echo -e "3. Restart: systemctl restart wazuh-manager"

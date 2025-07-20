#!/bin/bash
# Enhanced Wazuh Telegram Integration Installer
# Author: Mursal Aliyev
# GitHub: https://github.com/aliyevmursal/wazuh-telegram-bot

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
REPO_URL="https://raw.githubusercontent.com/aliyevmursal/wazuh-telegram-bot/main"

echo -e "${BLUE}========================================${NC}"
echo -e "${PURPLE}Enhanced Wazuh Telegram Integration${NC}"
echo -e "${PURPLE}Author: Mursal Aliyev${NC}"
echo -e "${PURPLE}GitHub: github.com/aliyevmursal/wazuh-telegram-bot${NC}"
echo -e "${BLUE}========================================${NC}"

# Check root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}"
   exit 1
fi

# Check Wazuh installation
if [ ! -d "$WAZUH_PATH" ]; then
    echo -e "${RED}❌ Wazuh installation not found at $WAZUH_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Wazuh installation found${NC}"

# Check Python version
PYTHON_VERSION=$($WAZUH_PATH/framework/python/bin/python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python version: $PYTHON_VERSION${NC}"

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
$WAZUH_PATH/framework/python/bin/python3 -m pip install --upgrade pip
$WAZUH_PATH/framework/python/bin/python3 -m pip install requests urllib3

# Create integration directory
mkdir -p "$INTEGRATION_PATH"
mkdir -p "$(dirname "$LOG_FILE")"

# Download integration files
echo -e "${YELLOW}📥 Downloading integration files...${NC}"

# Download custom-telegram (executable)
if curl -sSL "$REPO_URL/custom-telegram" -o /tmp/custom-telegram; then
    cp /tmp/custom-telegram "$INTEGRATION_PATH/"
    echo -e "${GREEN}✅ Downloaded custom-telegram${NC}"
else
    echo -e "${RED}❌ Failed to download custom-telegram${NC}"
    exit 1
fi

# Download custom-telegram.py
if curl -sSL "$REPO_URL/custom-telegram.py" -o /tmp/custom-telegram.py; then
    cp /tmp/custom-telegram.py "$INTEGRATION_PATH/"
    echo -e "${GREEN}✅ Downloaded custom-telegram.py${NC}"
else
    echo -e "${RED}❌ Failed to download custom-telegram.py${NC}"
    exit 1
fi

# Download telegram_config.json
if curl -sSL "$REPO_URL/telegram_config.json" -o /tmp/telegram_config.json; then
    if [ ! -f "$CONFIG_FILE" ]; then
        cp /tmp/telegram_config.json "$CONFIG_FILE"
        echo -e "${GREEN}✅ Downloaded telegram_config.json${NC}"
    else
        echo -e "${YELLOW}⚠️  Configuration file already exists, skipping...${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Could not download config, creating default...${NC}"
    # Create default config if download fails
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
    "high":

#!/usr/bin/env python3
"""
Enhanced Wazuh Telegram Integration
Advanced security alert notification system for Wazuh SIEM

Author: Mursal Aliyev
GitHub: https://github.com/aliyevmursal
License: MIT
"""

import sys
import json
import requests
import logging
import time
import os
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

__version__ = "2.0.1"
__author__ = "Mursal Aliyev"

class WazuhTelegramIntegration:
    def __init__(self, config_file="/var/ossec/integrations/telegram_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.session = self.setup_session()
        
        # Rate limiting
        self.last_message_time = 0
        self.min_interval = self.config.get('rate_limit_seconds', 1)
        
        # Emoji mapping
        self.level_emojis = {
            0: "ℹ️", 1: "ℹ️", 2: "ℹ️", 3: "⚠️", 4: "⚠️", 5: "⚠️",
            6: "🟡", 7: "🟡", 8: "🟠", 9: "🟠", 10: "🔴", 11: "🔴",
            12: "🚨", 13: "🚨", 14: "🚨", 15: "🚨"
        }
        
        self.logger.info(f"Wazuh Telegram Integration v{__version__} by {__author__}")
    
    def load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            "chat_id": "",
            "parse_mode": "HTML",
            "disable_notification": False,
            "rate_limit_seconds": 1,
            "max_message_length": 4096,
            "severity_levels": {
                "low": [0, 1, 2],
                "medium": [3, 4, 5, 6, 7],
                "high": [8, 9, 10, 11],
                "critical": [12, 13, 14, 15]
            },
            "custom_filters": {
                "exclude_rules": [],
                "include_only_rules": [],
                "exclude_agents": [],
                "include_only_agents": []
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            else:
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
        except Exception as e:
            print(f"Config error: {e}")
            
        return default_config
    
    def setup_logging(self):
        """Setup logging"""
        log_file = "/var/ossec/logs/telegram_integration.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"WazuhTelegram-{__author__}")
    
    def setup_session(self):
        """Setup requests session"""
        session = requests.Session()
        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({'User-Agent': f'WazuhTelegramIntegration/{__version__} (by {__author__})'})
        return session
    
    def get_severity_level(self, level):
        """Get severity from level"""
        for severity, levels in self.config['severity_levels'].items():
            if level in levels:
                return severity
        return "unknown"
    
    def format_timestamp(self, timestamp_str):
        """Format timestamp"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            return timestamp_str
    
    def should_filter_alert(self, alert_data):
        """Check if alert should be filtered"""
        filters = self.config.get('custom_filters', {})
        
        # Check rule filters
        rule_id = alert_data.get('rule_id')
        if rule_id and rule_id != 'N/A':
            try:
                rule_id_int = int(rule_id)
                if filters.get('exclude_rules') and rule_id_int in filters['exclude_rules']:
                    return True
                if filters.get('include_only_rules') and rule_id_int not in filters['include_only_rules']:
                    return True
            except ValueError:
                pass
        
        # Check agent filters
        agent_name = alert_data.get('agent_name')
        if agent_name and agent_name != 'N/A':
            if filters.get('exclude_agents') and agent_name in filters['exclude_agents']:
                return True
            if filters.get('include_only_agents') and agent_name not in filters['include_only_agents']:
                return True
        
        return False
    
    def extract_alert_data(self, alert_json):
        """Extract alert data"""
        data = {}
        data['timestamp'] = alert_json.get('timestamp', 'N/A')
        
        rule = alert_json.get('rule', {})
        data['rule_id'] = rule.get('id', 'N/A')
        data['rule_level'] = rule.get('level', 0)
        data['rule_description'] = rule.get('description', 'N/A')
        data['rule_groups'] = ', '.join(rule.get('groups', []))
        
        agent = alert_json.get('agent', {})
        data['agent_name'] = agent.get('name', 'N/A')
        data['agent_id'] = agent.get('id', 'N/A')
        data['agent_ip'] = agent.get('ip', 'N/A')
        
        data['location'] = alert_json.get('location', 'N/A')
        data['srcip'] = alert_json.get('srcip', 'N/A')
        data['dstip'] = alert_json.get('dstip', 'N/A')
        
        # Handle nested data fields
        alert_data = alert_json.get('data', {})
        if isinstance(alert_data, dict):
            data['user'] = alert_data.get('user', 'N/A')
        else:
            data['user'] = 'N/A'
            
        data['program_name'] = alert_json.get('program_name', 'N/A')
        data['full_log'] = alert_json.get('full_log', 'N/A')
        
        return data
    
    def create_message(self, alert_data):
        """Create formatted message"""
        level = alert_data['rule_level']
        severity = self.get_severity_level(level)
        emoji = self.level_emojis.get(level, "📊")
        
        severity_styles = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
        severity_emoji = severity_styles.get(severity, '📊')
        
        message = f"""
{emoji} <b>Wazuh Security Alert</b> {severity_emoji}

<b>🎯 Severity:</b> {severity.upper()} (Level {level})
<b>📋 Rule:</b> {alert_data['rule_description']}
<b>🔢 Rule ID:</b> {alert_data['rule_id']}
<b>📅 Time:</b> {self.format_timestamp(alert_data['timestamp'])}

<b>🖥️ Agent:</b> {alert_data['agent_name']} ({alert_data['agent_ip']})
<b>📍 Location:</b> {alert_data['location']}
"""

        if alert_data['srcip'] != 'N/A':
            message += f"<b>🌐 Source IP:</b> <code>{alert_data['srcip']}</code>\n"
        if alert_data['dstip'] != 'N/A':
            message += f"<b>🌐 Destination IP:</b> <code>{alert_data['dstip']}</code>\n"
        if alert_data['user'] != 'N/A':
            message += f"<b>👤 User:</b> <code>{alert_data['user']}</code>\n"
        if alert_data['program_name'] != 'N/A':
            message += f"<b>⚙️ Program:</b> <code>{alert_data['program_name']}</code>\n"
        if alert_data['rule_groups']:
            message += f"<b>🏷️ Groups:</b> <code>{alert_data['rule_groups']}</code>\n"

        if alert_data['full_log'] != 'N/A':
            log_snippet = alert_data['full_log'][:300]
            if len(alert_data['full_log']) > 300:
                log_snippet += "..."
            message += f"\n<b>📝 Log:</b>\n<pre>{log_snippet}</pre>"
        
        message += f"\n\n<i>🔧 Enhanced Wazuh Telegram Integration v{__version__}</i>"
        
        if len(message) > self.config['max_message_length']:
            message = message[:self.config['max_message_length']-3] + "..."
        
        return message
    
    def apply_rate_limiting(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_diff = current_time - self.last_message_time
        
        if time_diff < self.min_interval:
            sleep_time = self.min_interval - time_diff
            time.sleep(sleep_time)
        
        self.last_message_time = time.time()
    
    def send_message(self, message, hook_url):
        """Send message to Telegram"""
        try:
            self.apply_rate_limiting()
            
            msg_data = {
                'chat_id': self.config['chat_id'],
                'text': message,
                'parse_mode': self.config['parse_mode'],
                'disable_notification': self.config['disable_notification']
            }
            
            headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
            
            response = self.session.post(hook_url, headers=headers, data=json.dumps(msg_data), timeout=30)
            
            if response.status_code == 200:
                self.logger.info("Message sent successfully")
                return True
            else:
                self.logger.error(f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return False
    
    def process_alert(self, alert_file_path, hook_url):
        """Process alert"""
        try:
            if not self.config['chat_id']:
                self.logger.error("CHAT_ID not configured")
                return False
            
            with open(alert_file_path, 'r') as alert_file:
                alert_json = json.load(alert_file)
            
            alert_data = self.extract_alert_data(alert_json)
            
            # Apply filtering
            if self.should_filter_alert(alert_data):
                self.logger.info(f"Alert filtered out: Rule {alert_data['rule_id']}")
                return True
            
            message = self.create_message(alert_data)
            success = self.send_message(message, hook_url)
            
            if success:
                self.logger.info(f"Alert processed: Rule {alert_data['rule_id']} - Level {alert_data['rule_level']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing alert: {str(e)}")
            return False

def main():
    """Main function"""
    print(f"Enhanced Wazuh Telegram Integration v{__version__}")
    print(f"Author: {__author__}")
    print("=" * 50)
    
    if len(sys.argv) != 4:
        print("Usage: custom-telegram.py <alert_file> <rule_id> <hook_url>")
        sys.exit(1)
    
    alert_file_path = sys.argv[1]
    hook_url = sys.argv[3]
    
    integration = WazuhTelegramIntegration()
    success = integration.process_alert(alert_file_path, hook_url)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

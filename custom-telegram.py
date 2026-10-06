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
import html
import re
import logging
import time
import os
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

__version__ = "2.2.0"
__author__ = "Mursal Aliyev"

INTEGRATION_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_FILE = os.path.join(INTEGRATION_DIR, "telegram_config.json")
DEFAULT_LOG_FILE = os.path.normpath(os.path.join(INTEGRATION_DIR, "..", "logs", "telegram_integration.log"))

TELEGRAM_MAX_LENGTH = 4096
LOG_SNIPPET_LENGTH = 500

# Matches the bot token inside a Telegram API URL so it never ends up in logs
TOKEN_PATTERN = re.compile(r"bot\d+:[A-Za-z0-9_-]+")


def mask_token(text):
    return TOKEN_PATTERN.sub("bot<hidden>", str(text))


class WazuhTelegramIntegration:
    def __init__(self, config_file=DEFAULT_CONFIG_FILE):
        self.config_file = config_file
        self.setup_logging()
        self.config = self.load_config()
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

        self.logger.debug(f"Wazuh Telegram Integration v{__version__} by {__author__}")

    def load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            "chat_id": "",
            "hook_url": "",
            "message_thread_id": None,
            "parse_mode": "HTML",
            "disable_notification": False,
            "rate_limit_seconds": 1,
            "max_message_length": TELEGRAM_MAX_LENGTH,
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
            },
            "message_templates": {
                "custom_header": "",
                "custom_footer": ""
            }
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                for key, value in config.items():
                    # Merge nested sections so a partial section keeps its defaults
                    if isinstance(value, dict) and isinstance(default_config.get(key), dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            else:
                self.logger.warning(f"Config file not found: {self.config_file}, using defaults")
        except Exception as e:
            self.logger.error(f"Config error ({self.config_file}): {e}")

        # Environment overrides
        env_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if env_chat_id and env_chat_id.strip():
            default_config['chat_id'] = env_chat_id.strip()

        max_len = default_config.get('max_message_length') or TELEGRAM_MAX_LENGTH
        default_config['max_message_length'] = min(int(max_len), TELEGRAM_MAX_LENGTH)

        return default_config

    def resolve_hook_url(self, cli_hook_url=None):
        """Resolve hook URL from CLI, environment, or config"""
        if cli_hook_url and isinstance(cli_hook_url, str) and cli_hook_url.strip():
            return cli_hook_url.strip()

        # Env vars take precedence if CLI not provided
        env_hook = os.getenv("TELEGRAM_HOOK_URL") or os.getenv("HOOK_URL")
        if env_hook and env_hook.strip():
            return env_hook.strip()

        # Config fallback
        cfg_hook = self.config.get("hook_url")
        if cfg_hook and isinstance(cfg_hook, str) and cfg_hook.strip():
            return cfg_hook.strip()

        return None

    def resolve_chat_id(self, cli_api_key=None):
        """Use chat_id from config/env, falling back to the <api_key> integration option"""
        chat_id = str(self.config.get('chat_id') or '').strip()
        if chat_id:
            return chat_id
        if cli_api_key and re.fullmatch(r"-?\d+|@\w+", cli_api_key.strip()):
            return cli_api_key.strip()
        return None

    def setup_logging(self):
        """Setup logging (never fail the integration because of logging)"""
        self.logger = logging.getLogger("WazuhTelegram")
        self.logger.setLevel(logging.DEBUG if os.getenv("TELEGRAM_DEBUG") else logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        log_file = os.getenv("TELEGRAM_LOG_FILE", DEFAULT_LOG_FILE)
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: cannot write log file {log_file}: {e}", file=sys.stderr)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def setup_session(self):
        """Setup requests session with retries (POST included)"""
        session = requests.Session()
        retry_kwargs = dict(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=True,
        )
        try:
            retry_strategy = Retry(allowed_methods=frozenset(["POST"]), **retry_kwargs)
        except TypeError:
            # urllib3 < 1.26
            retry_strategy = Retry(method_whitelist=frozenset(["POST"]), **retry_kwargs)
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
        """Format timestamp (Wazuh uses e.g. 2025-07-21T14:30:45.123+0000)"""
        if not timestamp_str or timestamp_str == 'N/A':
            return 'N/A'
        ts = timestamp_str.replace('Z', '+00:00')
        # Python < 3.11 does not accept "+0000" in fromisoformat
        ts = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', ts)
        try:
            dt = datetime.fromisoformat(ts)
            return dt.strftime('%Y-%m-%d %H:%M:%S %Z').strip() if dt.tzinfo else dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                dt = datetime.strptime(ts[:19], '%Y-%m-%dT%H:%M:%S')
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                return timestamp_str

    def should_filter_alert(self, alert_data):
        """Check if alert should be filtered"""
        filters = self.config.get('custom_filters', {}) or {}

        # Rule filters (compare as strings so both 5710 and "5710" work in config)
        rule_id = str(alert_data.get('rule_id', 'N/A'))
        if rule_id != 'N/A':
            exclude_rules = {str(r) for r in filters.get('exclude_rules') or []}
            include_rules = {str(r) for r in filters.get('include_only_rules') or []}
            if rule_id in exclude_rules:
                return True
            if include_rules and rule_id not in include_rules:
                return True

        # Agent filters
        agent_name = alert_data.get('agent_name')
        if agent_name and agent_name != 'N/A':
            exclude_agents = filters.get('exclude_agents') or []
            include_agents = filters.get('include_only_agents') or []
            if agent_name in exclude_agents:
                return True
            if include_agents and agent_name not in include_agents:
                return True

        return False

    @staticmethod
    def _first(*values):
        for value in values:
            if value not in (None, '', [], {}):
                return value
        return 'N/A'

    def extract_alert_data(self, alert_json):
        """Extract alert data"""
        data = {}
        data['timestamp'] = alert_json.get('timestamp', 'N/A')

        rule = alert_json.get('rule', {}) or {}
        data['rule_id'] = str(rule.get('id', 'N/A'))
        try:
            data['rule_level'] = int(rule.get('level', 0))
        except (TypeError, ValueError):
            data['rule_level'] = 0
        data['rule_description'] = rule.get('description', 'N/A')
        data['rule_groups'] = ', '.join(rule.get('groups', []) or [])

        agent = alert_json.get('agent', {}) or {}
        data['agent_name'] = agent.get('name', 'N/A')
        data['agent_id'] = agent.get('id', 'N/A')
        data['agent_ip'] = agent.get('ip', 'N/A')

        data['location'] = alert_json.get('location', 'N/A')

        # Wazuh puts decoded fields under "data", older/custom alerts may have them top-level
        alert_fields = alert_json.get('data', {})
        if not isinstance(alert_fields, dict):
            alert_fields = {}
        win_event = (alert_fields.get('win', {}) or {}).get('eventdata', {}) or {}
        predecoder = alert_json.get('predecoder', {}) or {}

        data['srcip'] = self._first(alert_fields.get('srcip'), alert_json.get('srcip'), win_event.get('ipAddress'))
        data['dstip'] = self._first(alert_fields.get('dstip'), alert_json.get('dstip'))
        data['user'] = self._first(
            alert_fields.get('dstuser'), alert_fields.get('srcuser'), alert_fields.get('user'),
            alert_json.get('dstuser'), alert_json.get('srcuser'), alert_json.get('user'),
            win_event.get('targetUserName'), win_event.get('subjectUserName')
        )
        data['program_name'] = self._first(predecoder.get('program_name'), alert_json.get('program_name'))
        data['full_log'] = self._first(alert_json.get('full_log'))

        syscheck = alert_json.get('syscheck', {}) or {}
        data['file_path'] = self._first(syscheck.get('path'))
        data['file_event'] = self._first(syscheck.get('event'))

        return data

    def create_message(self, alert_data, log_limit=LOG_SNIPPET_LENGTH):
        """Create HTML formatted message (all dynamic values are escaped)"""
        e = lambda v: html.escape(str(v), quote=False)

        level = alert_data['rule_level']
        severity = self.get_severity_level(level)
        emoji = self.level_emojis.get(level, "📊")

        severity_styles = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
        severity_emoji = severity_styles.get(severity, '📊')

        templates = self.config.get('message_templates', {}) or {}
        header = templates.get('custom_header') or ''
        footer = templates.get('custom_footer') or f"<i>🔧 Enhanced Wazuh Telegram Integration v{__version__}</i>"

        lines = []
        if header:
            lines += [header, ""]
        lines += [
            f"{emoji} <b>Wazuh Security Alert</b> {severity_emoji}",
            "",
            f"<b>🎯 Severity:</b> {e(severity.upper())} (Level {level})",
            f"<b>📋 Rule:</b> {e(alert_data['rule_description'])}",
            f"<b>🔢 Rule ID:</b> {e(alert_data['rule_id'])}",
            f"<b>📅 Time:</b> {e(self.format_timestamp(alert_data['timestamp']))}",
            "",
            f"<b>🖥️ Agent:</b> {e(alert_data['agent_name'])} ({e(alert_data['agent_ip'])})",
            f"<b>📍 Location:</b> {e(alert_data['location'])}",
        ]

        optional_fields = [
            ('srcip', '🌐 Source IP'),
            ('dstip', '🌐 Destination IP'),
            ('user', '👤 User'),
            ('program_name', '⚙️ Program'),
            ('file_path', '📄 File'),
            ('file_event', '📝 File event'),
            ('rule_groups', '🏷️ Groups'),
        ]
        for key, label in optional_fields:
            value = alert_data.get(key)
            if value and value != 'N/A':
                lines.append(f"<b>{label}:</b> <code>{e(value)}</code>")

        full_log = alert_data.get('full_log')
        if full_log and full_log != 'N/A' and log_limit > 0:
            log_snippet = full_log[:log_limit]
            if len(full_log) > log_limit:
                log_snippet += "..."
            lines += ["", "<b>📝 Log:</b>", f"<pre>{e(log_snippet)}</pre>"]

        lines += ["", footer]
        return "\n".join(lines)

    def build_message(self, alert_data):
        """Build a message that fits the length limit without breaking HTML tags"""
        max_len = self.config['max_message_length']
        log_limit = LOG_SNIPPET_LENGTH
        message = self.create_message(alert_data, log_limit)
        while len(message) > max_len and log_limit > 0:
            log_limit = max(0, log_limit - max(len(message) - max_len, 50))
            message = self.create_message(alert_data, log_limit)
        if len(message) > max_len:
            # Still too long (huge description etc.): fall back to plain text
            message = html.unescape(re.sub(r'<[^>]+>', '', message))[:max_len - 3] + "..."
        return message

    def apply_rate_limiting(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_diff = current_time - self.last_message_time

        if time_diff < self.min_interval:
            time.sleep(self.min_interval - time_diff)

        self.last_message_time = time.time()

    def _post(self, hook_url, payload):
        return self.session.post(hook_url, json=payload, timeout=30)

    def send_message(self, message, hook_url, chat_id):
        """Send message to Telegram"""
        try:
            self.apply_rate_limiting()

            msg_data = {
                'chat_id': chat_id,
                'text': message,
                'disable_notification': bool(self.config.get('disable_notification')),
                'disable_web_page_preview': True,
            }
            if self.config.get('parse_mode'):
                msg_data['parse_mode'] = self.config['parse_mode']
            if self.config.get('message_thread_id'):
                msg_data['message_thread_id'] = self.config['message_thread_id']

            response = self._post(hook_url, msg_data)

            if response.status_code == 400 and "parse" in response.text.lower() and 'parse_mode' in msg_data:
                # Formatting rejected by Telegram: resend as plain text so the alert is not lost
                self.logger.warning(f"Telegram rejected formatting, resending as plain text: {response.text}")
                msg_data.pop('parse_mode')
                msg_data['text'] = html.unescape(re.sub(r'<[^>]+>', '', message))
                response = self._post(hook_url, msg_data)

            if response.status_code == 200:
                self.logger.info("Message sent successfully")
                return True

            self.logger.error(f"Failed: {response.status_code} - {mask_token(response.text)}")
            return False

        except Exception as ex:
            self.logger.error(f"Error sending message: {mask_token(ex)}")
            return False

    def process_alert(self, alert_file_path, hook_url, chat_id):
        """Process alert"""
        try:
            with open(alert_file_path, 'r', encoding='utf-8', errors='replace') as alert_file:
                content = alert_file.read().strip()
            try:
                alert_json = json.loads(content)
            except json.JSONDecodeError:
                # Some versions write one JSON object per line; use the first one
                alert_json = json.loads(content.splitlines()[0])

            alert_data = self.extract_alert_data(alert_json)

            if self.should_filter_alert(alert_data):
                self.logger.info(f"Alert filtered out: Rule {alert_data['rule_id']}")
                return True

            message = self.build_message(alert_data)
            success = self.send_message(message, hook_url, chat_id)

            if success:
                self.logger.info(f"Alert processed: Rule {alert_data['rule_id']} - Level {alert_data['rule_level']}")

            return success

        except Exception as ex:
            self.logger.error(f"Error processing alert {alert_file_path}: {mask_token(ex)}")
            return False


def main():
    """Main function

    Wazuh integratord calls: <script> <alert_file> <api_key> <hook_url> [<options_file>] [debug]
    """
    args = sys.argv[1:]
    if len(args) < 1 or args[0] in ('-h', '--help'):
        print(f"Enhanced Wazuh Telegram Integration v{__version__} by {__author__}")
        print("Usage: custom-telegram <alert_file> [<api_key|chat_id>] [<hook_url>]")
        print("hook_url can also come from TELEGRAM_HOOK_URL/HOOK_URL env vars or hook_url in telegram_config.json")
        print("chat_id can also come from TELEGRAM_CHAT_ID env var or the <api_key> option in ossec.conf")
        sys.exit(1)

    if 'debug' in args[3:]:
        os.environ['TELEGRAM_DEBUG'] = '1'

    alert_file_path = args[0]
    cli_api_key = args[1] if len(args) > 1 else None
    cli_hook_url = args[2] if len(args) > 2 else None

    integration = WazuhTelegramIntegration()

    hook_url = integration.resolve_hook_url(cli_hook_url)
    if not hook_url:
        integration.logger.error(
            "hook_url not provided: set <hook_url> in ossec.conf, TELEGRAM_HOOK_URL env var, "
            f"or hook_url in {integration.config_file}"
        )
        sys.exit(1)

    chat_id = integration.resolve_chat_id(cli_api_key)
    if not chat_id:
        integration.logger.error(
            f"chat_id not configured: set chat_id in {integration.config_file}, "
            "TELEGRAM_CHAT_ID env var, or <api_key> in ossec.conf"
        )
        sys.exit(1)

    success = integration.process_alert(alert_file_path, hook_url, chat_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

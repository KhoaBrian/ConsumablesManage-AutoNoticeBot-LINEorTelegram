          
import requests
import threading
import logging
import configparser
import os
import sys

try:
    import keyring
except ImportError:
    keyring = None

def get_base_path(source_file=None):
    """Return the directory used for data and bundled runtime files."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    source_file = source_file or __file__
    return os.path.dirname(os.path.abspath(source_file))


BASE_DIR = get_base_path(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, 'settings.ini')
KEYRING_SERVICE = 'MaLab-Chemical-Manager'
SECRET_SETTINGS = {
    ('Telegram', 'BotToken'): 'TELEGRAM_BOT_TOKEN',
    ('LINE', 'ChannelAccessToken'): 'LINE_CHANNEL_ACCESS_TOKEN',
    ('LINE', 'ChannelSecret'): 'LINE_CHANNEL_SECRET',
    ('Ngrok', 'Authtoken'): 'NGROK_AUTHTOKEN',
}

def load_config():
    """Loads configuration from settings.ini, creates default if not found."""
    config = configparser.ConfigParser(defaults={
                           
        'BotToken': 'YOUR_BOT_TOKEN_HERE',
        'ChatID': 'YOUR_CHAT_ID_HERE',
        'NotifyImmediately': 'True',
                       
        'ChannelAccessToken': '',
        'ChannelSecret': '',
        'GroupID': '',
                        
        'Domain': '',
        'Authtoken': '',
                           
        'MonthlyReportEnabled': 'True',
        'MonthlyReportDay': '1',
        'MonthlyReportHour': '8',
        'LastMonthlyReportSent': '2000-01',
        'JokeReportEnabled': 'True',
        'JokeReportHour': '22',
        'LastJokeReportSent': '2000-01',
        'PeriodicCheckEnabled': 'True',
        'PeriodicCheckDays': '2',
        'PeriodicCheckHour': '22',
        'LastPeriodicCheckSent': '2000-01-01 00:00:00',
                        
        'DefaultPasswordChanged': 'False'
    }, inline_comment_prefixes=('#', ';'))

    config.optionxform = str                    

    if not os.path.exists(CONFIG_FILE):
        logging.warning(f"'{CONFIG_FILE}' not found. Creating default settings file.")
                         
        config['Telegram'] = {}
        config['LINE'] = {}
        config['Ngrok'] = {}
        config['Schedule'] = {}
        config['Admin'] = {}
                                                                                 
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            logging.info(f"Default '{CONFIG_FILE}' created. Please edit it with your actual Bot Token and Chat ID.")
        except IOError as e:
             logging.error(f"Could not write default config file '{CONFIG_FILE}': {e}")
                                                                    
             return config
    else:
        try:
            config.read(CONFIG_FILE, encoding='utf-8')
            logging.info(f"Configuration loaded from '{CONFIG_FILE}'.")
                                                     
            if 'Telegram' not in config: config.add_section('Telegram')
            if 'LINE' not in config: config.add_section('LINE')
            if 'Ngrok' not in config: config.add_section('Ngrok')
            if 'Schedule' not in config: config.add_section('Schedule')
            if 'Admin' not in config: config.add_section('Admin')
        except configparser.Error as e:
            logging.error(f"Error reading config file '{CONFIG_FILE}': {e}. Using defaults.")
                                                     
            return configparser.ConfigParser(defaults=config.defaults(), inline_comment_prefixes=('#', ';'))

    migrate_plaintext_secrets(config)
    return config


def get_secret(section, option, config=None, fallback=''):
    """Resolve a secret from environment, OS keyring, then legacy config."""
    env_name = SECRET_SETTINGS.get((section, option))
    if env_name:
        environment_value = os.getenv(env_name)
        if environment_value:
            return environment_value

    if keyring is not None:
        try:
            stored_value = keyring.get_password(KEYRING_SERVICE, f'{section}.{option}')
            if stored_value:
                return stored_value
        except Exception:
            logging.warning("Could not read %s.%s from the OS keyring.", section, option, exc_info=True)

    if config is not None:
        return config.get(section, option, fallback=fallback)
    return fallback


def set_secret(section, option, value, config=None):
    """Store a secret in the OS keyring and remove any plaintext config copy."""
    if keyring is None:
        raise RuntimeError("The keyring package is required to store bot credentials securely.")
    key_name = f'{section}.{option}'
    if value:
        keyring.set_password(KEYRING_SERVICE, key_name, value)
    else:
        try:
            keyring.delete_password(KEYRING_SERVICE, key_name)
        except keyring.errors.PasswordDeleteError:
            pass
    if config is not None and config.has_option(section, option):
        config.remove_option(section, option)


def migrate_plaintext_secrets(config):
    """Move old credentials from settings.ini into the OS keyring once."""
    if keyring is None:
        logging.warning("keyring is unavailable; legacy bot credentials remain in settings.ini.")
        return

    changed = False
    for (section, option), _env_name in SECRET_SETTINGS.items():
        legacy_value = config.get(section, option, fallback='').strip()
        if not legacy_value or legacy_value in ('YOUR_BOT_TOKEN_HERE',):
            continue
        try:
            if not keyring.get_password(KEYRING_SERVICE, f'{section}.{option}'):
                keyring.set_password(KEYRING_SERVICE, f'{section}.{option}', legacy_value)
            config.remove_option(section, option)
            changed = True
            logging.info("Migrated %s.%s to the OS keyring.", section, option)
        except Exception:
            logging.warning("Could not migrate %s.%s to the OS keyring.", section, option, exc_info=True)

    if changed:
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
        except OSError:
            logging.warning("Could not remove migrated secrets from settings.ini.", exc_info=True)


def get_setting(config, section, option, fallback=None):
    """Helper function to get a setting, handling potential errors."""
    if (section, option) in SECRET_SETTINGS:
        return get_secret(section, option, config=config, fallback=fallback)
    return config.get(section, option, fallback=fallback)

def save_setting(config, section, option, value):
    """Helper function to save a setting."""
    try:
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, option, str(value))                               
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        logging.info(f"Setting '{option}' in section '{section}' saved to '{CONFIG_FILE}'.")
        return True
    except IOError as e:
        logging.error(f"Could not write config file '{CONFIG_FILE}' to save setting: {e}")
        return False
    except Exception as e:
         logging.error(f"Error saving setting {section}/{option}: {e}", exc_info=True)
         return False


def send_telegram_message(bot_token, chat_id, message, parse_mode="HTML"):
    """Sends a message to a Telegram chat using the bot API."""
                                      
    if not bot_token or 'YOUR_BOT_TOKEN_HERE' in bot_token:
        logging.error("Invalid or missing Telegram Bot Token.")
        return False
    if not chat_id or 'YOUR_CHAT_ID_HERE' in str(chat_id):
        logging.error("Invalid or missing Telegram Chat ID.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    max_length = 4096
    messages_to_send = [message[i:i + max_length] for i in range(0, len(message), max_length)]
    success_all = True

    for i, msg_part in enumerate(messages_to_send):
        data = {"chat_id": chat_id, "text": msg_part, "parse_mode": parse_mode}
        response = None
        try:
            response = requests.post(url, data=data, timeout=15)                       
            response.raise_for_status()
            logging.info(f"Telegram message part {i+1}/{len(messages_to_send)} sent successfully to chat ID {chat_id}.")
                                                                                   
                                                           
        except requests.exceptions.Timeout:
            logging.error("Telegram request timed out.")
            success_all = False
            break
        except requests.exceptions.RequestException as e:
            error_details = ""
            status_code = "N/A"
            if response is not None:
                status_code = response.status_code
                try:
                    error_details = response.json()
                except requests.exceptions.JSONDecodeError:
                    error_details = response.text
            logging.error(f"Telegram request failed (Status: {status_code}): {e}. Response: {error_details}", exc_info=True)
            success_all = False
            break
        except Exception as e_inner:
             logging.error(f"Unknown error sending Telegram message part: {e_inner}", exc_info=True)
             success_all = False
             break
    return success_all

def send_telegram_in_thread(bot_token, chat_id, message):
    """Starts sending a Telegram message in a separate thread."""
                                                       
    if not bot_token or 'YOUR_BOT_TOKEN_HERE' in bot_token or \
       not chat_id or 'YOUR_CHAT_ID_HERE' in chat_id:
        logging.warning("Cannot start Telegram thread: Bot Token or Chat ID is missing/default.")
        return

    thread = threading.Thread(target=send_telegram_message, args=(bot_token, chat_id, message), daemon=True)
    thread.start()
    logging.info("Started Telegram sending thread.")

                                                   
                                                   
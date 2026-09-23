# Lab Consumables Management App

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41CD52?logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Lab Consumables Management App is a desktop inventory and transaction manager for laboratory consumables. It records FillIn and TakeOut activity, maintains stock levels, provides Excel reports, and delivers operational alerts through Telegram and LINE.

## Key Features

- PyQt6 desktop interface for transactions, users, permissions, and audit history.
- Dual-Platform Bot Integration (Telegram & LINE): Remote transaction logging, stock checking, and activity reviews via Telegram (long-polling) or LINE (webhook & push alerts).
- Static Ngrok tunneling for exposing the LINE webhook endpoint.
- Excel import plus filtered history and monthly usage export.
- Scheduled monthly summaries, end-of-month activity reports, and low-stock checks.
- SQLite persistence with database backup, restore, and audit logging.
- OS keyring storage for bot credentials, with environment-variable overrides.

## Requirements

- Python 3.10 or newer
- [Telegram] Quick setup - A Telegram Bot Token and a target Chat ID. It uses long-polling, meaning no Ngrok, no server setup, and no public IP required
- [LINE] Optional - LINE Developers channel credentials and a static Ngrok domain (or any public HTTPS endpoint) for webhook handling.

## Installation

```bash
git clone https://github.com/KhoaBrian/ConsumablesManage-AutoNoticeBot-LINEorTelegram.git
cd ConsumablesManage-AutoNoticeBot-LINEorTelegram
python -m venv venv
# Windows PowerShell: venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the application:

```bash
python AppCode/main_app.py
```

The first run creates `AppCode/lab_chemicals.db`, `AppCode/settings.ini`, and the default administrator account. These files are intentionally excluded from Git.

## Setup Guide

### Initial administrator login

1. Start the application.
2. Log in with username `admin` and password `admin`.
3. Change the password immediately through **File > Change Password**.

### Telegram

Open **Admin > Admin Settings / Manual Reports** and enter a bot token such as `123456789:ABCdefGHI...` and a chat ID such as `-1001234567890`. Credentials are stored in the OS keyring. For deployment through environment variables, use `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

### LINE and static Ngrok

1. Create a LINE Messaging API channel in the LINE Developers Console.
2. Set the webhook URL to `https://your-custom-name.ngrok-free.app/webhook/line` and enable webhook delivery
3. Copy the Channel Access Token and Channel Secret into Admin Settings.
4. Enter a permanent Ngrok domain such as `your-custom-name.ngrok-free.app`, without `https://`.
5. Enter the Ngrok authtoken and place the compatible `ngrok.exe` beside the application for the Windows standalone build.
6. Send `/setgroup` inside the LINE group that should receive alerts.

The webhook listens on `0.0.0.0:8080` by default. Environment overrides are `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`, `LINE_GROUP_ID`, `LINE_WEBHOOK_HOST`, `LINE_WEBHOOK_PORT`, `NGROK_DOMAIN`, and `NGROK_AUTHTOKEN`.

## Bot Commands

```text
/help
/log <user> <takeout|fillin> <quantity> <chemical> [quantity] [chemical]...
/checkstock <chemical> | all
/checkuser <user> <chemical> | all
/checkchemical <chemical>
```

Use `Whoknows` when the responsible user is unknown. Quantities must be positive. TakeOut is rejected when available stock is insufficient.

## Excel Import and Export

Administrators can import transaction records through **Admin > Import from Excel**. History supports filtered export, date-range export, and a two-sheet monthly report. Preferred columns are:

```text
Time, Name, Chemical, Type, Number, Notes
```

Supported transaction types are `FillIn`, `TakeOut`, `Adjust`, `Edit`, and `Delete` where applicable.

## Build a Standalone Windows Executable

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name LabConsumableManager AppCode/main_app.py
```

Copy `ngrok.exe` beside the generated executable when static tunneling is enabled. The app keeps the SQLite database and configuration beside the executable in a frozen build. Do not commit generated binaries, databases, settings, or credentials.

## Security Notes

- Never commit bot tokens, Ngrok authtokens, `settings.ini`, or database files.
- Use the OS keyring or environment variables for secrets.
- Keep LINE webhook signature validation enabled.
- Back up the SQLite database before using Restore Database.

## License

This project is licensed under the MIT License.
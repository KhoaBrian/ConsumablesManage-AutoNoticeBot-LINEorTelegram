import calendar
import logging
import os
import shutil
import subprocess
import sys
import threading
import time as time_module
import traceback
from datetime import datetime, timedelta

import pandas as pd
import requests
from PyQt6.QtCore import QDate, QEvent, QSharedMemory, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QDesktopServices,
    QDoubleValidator,
    QFont,
    QStandardItem,
    QStandardItemModel,
)
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStatusBar,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

import database_manager as db
import line_bot
import utils

MAX_TIMER_INTERVAL = 2147483647

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About & Tutorial")
        self.setMinimumSize(550, 450)                        

        layout = QVBoxLayout(self)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)                                      
        self.text_browser.setHtml(self.get_about_content())                   

        layout.addWidget(self.text_browser)

                      
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
                                                            
        close_button = button_box.button(QDialogButtonBox.StandardButton.Close)
        if close_button:
             close_button.setDefault(True)                           
        button_box.accepted.connect(self.accept)                              
        button_box.rejected.connect(self.reject)                                         
        layout.addWidget(button_box)



    def get_about_content(self):
        """Generates the HTML content for the About/Tutorial dialog in English."""
        content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: sans-serif; line-height: 1.4; padding: 5px; }
                h1 { color: #333; margin-bottom: 0px; }
                h2 { color: #555; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 25px; margin-bottom: 10px;}
                h3 { color: #444; margin-top: 15px; margin-bottom: 5px; }
                ul { margin-left: 20px; padding-left: 10px;}
                li { margin-bottom: 8px; }
                code { background-color: #e8e8e8; padding: 2px 5px; border: 1px solid #dcdcdc; border-radius: 3px; font-family: monospace;}
                p { margin-top: 5px; margin-bottom: 10px;}
                b { color: #1a1a1a; } /* Make bold stand out a bit */
                .app-title { font-size: 16pt; font-weight: bold; margin-bottom: 5px;}
                .version-info { font-size: 9pt; color: #666; margin-top: 0px; margin-bottom: 15px;}
            </style>
        </head>
        <body>
            <div class="app-title">Ma Lab - Chemical Manager (Ver 2.0)</div>
            <div class="version-info">Version: 2.0 (September 2026)<br>
                Developed by: [Kay]</div>
            <h3>New in 2.0: Telegram and LINE share the same commands and reports. LINE alerts support automatic group registration, and bot credentials are protected by the application.</h3>
            
            <p>This application tracks chemical usage (TakeOut/FillIn), manages inventory stock levels, and sends notifications and reports to Telegram and LINE. Note: If using LINE, please put this App same folder with Ngrok.exe</p>

            <h2>Tutorial & Usage Rules</h2>

            <h3>1. Logging Chemical Use (Main Window)</h3>
            <ul>
                <li>Use a QR code scanner or type directly into the fields. Press <b>Enter</b> after each field to move to the next.</li>
                <li><b>User Name:</b> Your registered username. HAVE TO create account before logging, or type <code>Whoknows</code> if the user is unknown or forgot to log.</li>
                <li><b>Chemical:</b> The name of the chemical (must exist in the admin-managed list). If that is new chemical, ask admin to add it into admin-manage chemical list </li>
                <li><b>Quantity:</b> The amount used or added (enter numbers only, e.g., <code>1</code>, <code>10.5</code>). Must be > 0.</li>
                <li><b>Type (FillIn/TakeOut):</b> Enter <code>FillIn</code> (case-insensitive) if adding stock. Leave blank or enter <code>TakeOut</code> (case-insensitive) if removing stock.</li>
                <li>Pressing <b>Enter</b> on the 'Type' field (or clicking <b>Submit Entry</b>) saves the record. Fields clear automatically for the next entry.</li>
            </ul>

            <h3>2. Account Management (File Menu)</h3>
            <ul>
                <li>Go to "File" -> "Register New User" to create a new account.</li>
                <li>Go to "File" -> "Login" to log in with your credentials.</li>
                <li>Go to "File" -> "Logout" to log out.</li>
                <li>When logged in, go to "File" -> "Change Password" to update your own password.</li>
            </ul>

            <h3>3. Chat Commands (Telegram and LINE)</h3>
            <p>The same commands work in Telegram and LINE. Use spaces between every value:</p>
            <ul>
                <li><code>/help</code>: Shows all available commands and examples.</li>
                <li><code>/log &lt;user&gt; &lt;takeout|fillin&gt; &lt;quantity&gt; &lt;chemical&gt; ...</code>: Records one or more transactions. Example: <code>/log kay takeout 1 DMEM 2 FBS</code>.</li>
                <li><code>/checkstock &lt;chemical&gt;</code> or <code>/checkstock all</code>: Shows current stock and the latest FillIn.</li>
                <li><code>/checkuser &lt;user&gt; &lt;chemical&gt;</code> or <code>/checkuser &lt;user&gt; all</code>: Shows that user's activity since the latest FillIn.</li>
                <li><code>/checkchemical &lt;chemical&gt;</code>: Shows the chemical's activity since the latest FillIn.</li>
                <li><code>/setgroup</code> in a LINE group: Registers that group for automatic LINE alerts. It must be sent inside the target group, not a private chat.</li>
                <li>Use <code>Whoknows</code> when the responsible user is unknown. Quantities must be positive numbers. Use <code>takeout</code> to remove stock and <code>fillin</code> to add stock.</li>
            </ul>

            <h3>4. Viewing History and Export To Excel (View History Button)</h3>
            <ul>
                <li>Click the "View History" button on the main window.</li>
                <li>Use the filters (date range, user, chemical, type) and click "Apply Filters".</li>
                <li>Click "Reset Filters" to clear filters.</li>
                <li></li>
                <li>For export files:</li>
                <li>After use the filters. Click "Export Current View to Excel" to save the ONLY currently displayed history data to an Excel file.</li>
                <li>After choose date range. Click "Export History for Selected Range" to save the selected date range history data to an Excel file.</li>
                <li>After choose month range. Click "Export Monthly Usage & Summarize (2 Sheets)" to export the Raw Total Used & Filled (Sheet 1) and Summarize Usage (Sheet 2) to an Excel file.</li>
                <li><b>Edit/Delete Logs:</b> Logged-in users can double-click a row or select it and click "Edit Selected" (to edit the <b>Note</b> only) or "Delete Selected" for transactions <b>they originally created</b>. Admins can edit/delete any transaction. You will be asked to re-enter your password and provide a reason for deletion. Deleted entries are marked (gray, strikethrough).</li>
            </ul>
            
            <h3>5. Reports and Automatic Alerts</h3>
            <ul>
                <li>Monthly usage, end-of-month activity, and periodic low-stock reports use the same report generation logic for Telegram and LINE.</li>
                <li>Use Admin &gt; Admin Settings / Manual Reports to enable schedules, configure Telegram, configure LINE, and register the LINE push destination.</li>
                <li>Immediate low-stock alerts are sent when enabled and when a registered Telegram chat or LINE group is available.</li>
            </ul>

            <h3>6. LINE Alerts (Administrator)</h3>
            <ul>
                <li>The lab administrator configures the LINE connection before use. Regular users do not need to install packages or configure the connection.</li>
                <li>In Admin Settings, enter the LINE Channel Access Token, Channel Secret, and permanent Ngrok domain, then save and restart the application if requested.</li>
                <li>To register the destination for automatic alerts, send <code>/setgroup</code> in the target LINE group. The bot confirms the registration and saves the group automatically.</li>
                <li>Do not send <code>/setgroup</code> in a private chat; it must be sent inside the LINE group that should receive alerts.</li>
            </ul>

            <h3>7. Admin Functions (Admin Menu - Requires Admin Login)</h3>
            <ul>
                <li><b>Import from excel:</b> Import all columns (with or w/o notes) from excel to database. Note: Also import Chemicals that not include in Chemical Table (admin-manage list) and automatically add that new Chemicals name into the table (list).</li>
                <li><b>Manage Users:</b> Add/delete users, reset passwords, grant/revoke admin rights.</li>
                <li><b>Manage Chemicals:</b> Add/delete chemicals, edit names, set low stock thresholds.</li>
                <li><b>Admin Settings / Manual Reports:</b> Configure Telegram and LINE settings, Ngrok, enable/disable schedules, and manually trigger reports.</li>
                <li><b>Backup/Restore Database:</b> Create backups and restore the database from a backup file (Use Restore with extreme caution!).</li>
            </ul>

            <h2>Source Code &amp; Contributions</h2>
            <p>This project is open-source. For updates, source code, or to contribute, visit: https://github.com/KhoaBrian/</p>

        </body>
        </html>
        """
        return content


class RuleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lab's Rules")
        self.setMinimumSize(550, 450)

        layout = QVBoxLayout(self)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setHtml(self.get_rule_content())
        layout.addWidget(self.text_browser)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = button_box.button(QDialogButtonBox.StandardButton.Close)
        if close_button:
            close_button.setDefault(True)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_rule_content(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: sans-serif; line-height: 1.4; padding: 5px; }
                h1 { color: #333; margin-bottom: 0px; }
                h2 { color: #555; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 25px; margin-bottom: 10px; }
                h3 { color: #444; margin-top: 15px; margin-bottom: 5px; }
                ul { margin-left: 20px; padding-left: 10px; }
                li { margin-bottom: 8px; }
                b { color: #1a1a1a; }
                p { margin-top: 5px; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <h1>Lab's Rules</h1>
            <h2>Cell Culture Consumables: Request Before Pickup</h2>
            <p>Before picking up cell culture consumables, send a request at least <b>one day in advance</b> and <b>wait for acceptance before pickup</b>.</p>
            <ul>
                <li><b>Kay:</b> NC, RNAimax, Opti-MEM</li>
                <li><b>Sophia:</b> LG, PS, Medium (DMEM, RPMI, ...)</li>
                <li><b>Anna:</b> FBS, Trypsin</li>
            </ul>

            <h2>Daily Lab Rules</h2>
            <ul>
                <li>Keep FBS falcons after use by yourself; the Manager may ask about them.</li>
                <li>Always log entries immediately when taking or adding chemicals.</li>
                <li>If logging is forgotten, inform the Lab Manager or log it as <code>Whoknows</code> with a note using Edit Note later.</li>
                <li>Ensure reasonable thresholds are set for commonly used chemicals.</li>
                <li>Perform periodic stock checks and log corrections as <code>Whoknows</code> TakeOut/FillIn.</li>
                <li>Ask the Lab Manager when a rule or ownership assignment is unclear.</li>
            </ul>
        </body>
        </html>
        """


class ChangePasswordDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"Change Password for {username}")
        self.setModal(True)

        layout = QFormLayout(self)

        self.old_password_edit = QLineEdit(self)
        self.old_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_edit = QLineEdit(self)
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit = QLineEdit(self)
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("Old Password:", self.old_password_edit)
        layout.addRow("New Password:", self.new_password_edit)
        layout.addRow("Confirm New Password:", self.confirm_password_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.old_password_edit.setFocus()

    def validate_and_accept(self):
        """Validate passwords before accepting."""
        old_password = self.old_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not old_password or not new_password:
            QMessageBox.warning(self, "Input Error", "Passwords cannot be empty.")
            return

                                   
        verified_user = db.verify_user(self.username, old_password)
        if not verified_user:
            QMessageBox.critical(self, "Authentication Failed", "Incorrect old password.")
            return

        if new_password == old_password:
             QMessageBox.warning(self, "Input Error", "New password cannot be the same as the old password.")
             return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "New passwords do not match.")
            self.new_password_edit.clear()
            self.confirm_password_edit.clear()
            self.new_password_edit.setFocus()
            return

                           
        self.accept()

    def get_new_password(self):
        """Returns the new password."""
        return self.new_password_edit.text()

class AdminSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent                                      
        self.config = parent.config                               
        self.setWindowTitle("Admin Settings & Manual Reports")
        self.setMinimumWidth(500)
                             
        main_layout = QVBoxLayout(self)

                                                 
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)                                    

                                         
        telegram_group = QGroupBox("Telegram Configuration")
        telegram_layout = QFormLayout(telegram_group)

        self.bot_token_edit = QLineEdit()
        self.bot_token_edit.setPlaceholderText("123456789:ABCdefGHI...")
        self.chat_id_edit = QLineEdit()
        self.chat_id_edit.setPlaceholderText("-1001234567890")
        self.notify_immediately_checkbox = QCheckBox("Send immediate low stock alert?")

        telegram_layout.addRow("Bot Token:", self.bot_token_edit)
        telegram_layout.addRow("Chat ID:", self.chat_id_edit)
        telegram_layout.addRow(self.notify_immediately_checkbox)
        scroll_layout.addWidget(telegram_group)

                                     
        line_group = QGroupBox("LINE Messaging API Configuration")
        line_layout = QFormLayout(line_group)
        self.line_access_token_edit = QLineEdit()
        self.line_access_token_edit.setPlaceholderText("LINE channel access token")
        self.line_access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.line_secret_edit = QLineEdit()
        self.line_secret_edit.setPlaceholderText("LINE channel secret")
        self.line_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.line_group_id_edit = QLineEdit()
        self.line_group_id_edit.setPlaceholderText("LINE group/user/room ID for push alerts")
        line_layout.addRow("Channel Access Token:", self.line_access_token_edit)
        line_layout.addRow("Channel Secret:", self.line_secret_edit)
        line_layout.addRow("Push Destination ID:", self.line_group_id_edit)
        scroll_layout.addWidget(line_group)

                                      
        ngrok_group = QGroupBox("Ngrok Webhook Tunnel")
        ngrok_layout = QFormLayout(ngrok_group)
        self.ngrok_domain_edit = QLineEdit()
        self.ngrok_domain_edit.setPlaceholderText("your-custom-name.ngrok-free.app")
        self.ngrok_authtoken_edit = QLineEdit()
        self.ngrok_authtoken_edit.setPlaceholderText("Ngrok authtoken")
        self.ngrok_authtoken_edit.setEchoMode(QLineEdit.EchoMode.Password)
        ngrok_layout.addRow("Static Domain:", self.ngrok_domain_edit)
        ngrok_layout.addRow("Authtoken:", self.ngrok_authtoken_edit)
        scroll_layout.addWidget(ngrok_group)

                                      
        monthly_group = QGroupBox("Monthly Summary Report (Previous Month)")
        monthly_layout = QFormLayout(monthly_group)
        monthly_buttons_layout = QHBoxLayout()                               

        self.monthly_enabled_checkbox = QCheckBox("Enable Automatic Report")
        self.monthly_day_spinbox = QSpinBox()
        self.monthly_day_spinbox.setRange(1, 28)                                       
        self.monthly_hour_spinbox = QSpinBox()
        self.monthly_hour_spinbox.setRange(0, 23)
        self.last_monthly_label = QLabel("N/A")
        self.run_monthly_button = QPushButton("Run Now (for last month)")

        monthly_layout.addRow(self.monthly_enabled_checkbox)
        monthly_layout.addRow("Day of Month to Run:", self.monthly_day_spinbox)
        monthly_layout.addRow("Hour of Day to Run (0-23):", self.monthly_hour_spinbox)
        monthly_layout.addRow("Last Sent (YYYY-MM):", self.last_monthly_label)
        monthly_buttons_layout.addStretch()
        monthly_buttons_layout.addWidget(self.run_monthly_button)                   
        monthly_buttons_layout.addStretch()
        monthly_layout.addRow(monthly_buttons_layout)                                  

        scroll_layout.addWidget(monthly_group)

                                   
        joke_group = QGroupBox("End-of-Month 'Joke' Report (Current Month)")
        joke_layout = QFormLayout(joke_group)
        joke_buttons_layout = QHBoxLayout()

        self.joke_enabled_checkbox = QCheckBox("Enable Automatic Report")
        self.joke_hour_spinbox = QSpinBox()
        self.joke_hour_spinbox.setRange(0, 23)
        self.last_joke_label = QLabel("N/A")
        self.run_joke_button = QPushButton("Run Now (for this month)")

        joke_layout.addRow(self.joke_enabled_checkbox)
        joke_layout.addRow("Hour to Run (0-23, on last day):", self.joke_hour_spinbox)
        joke_layout.addRow("Last Sent (YYYY-MM):", self.last_joke_label)
        joke_buttons_layout.addStretch()
        joke_buttons_layout.addWidget(self.run_joke_button)
        joke_buttons_layout.addStretch()
        joke_layout.addRow(joke_buttons_layout)

        scroll_layout.addWidget(joke_group)

                                      
        periodic_group = QGroupBox("Periodic Low Stock Check")
        periodic_layout = QFormLayout(periodic_group)
        periodic_buttons_layout = QHBoxLayout()

        self.periodic_enabled_checkbox = QCheckBox("Enable Automatic Check")
        self.periodic_days_spinbox = QSpinBox()
        self.periodic_days_spinbox.setRange(1, 30)                   
        self.periodic_hour_spinbox = QSpinBox()
        self.periodic_hour_spinbox.setRange(0, 23)
        self.last_periodic_label = QLabel("N/A")
        self.run_periodic_button = QPushButton("Run Check Now")

        periodic_layout.addRow(self.periodic_enabled_checkbox)
        periodic_layout.addRow("Run Every (days):", self.periodic_days_spinbox)
        periodic_layout.addRow("Hour of Day to Run (0-23):", self.periodic_hour_spinbox)
        periodic_layout.addRow("Last Sent:", self.last_periodic_label)
        periodic_buttons_layout.addStretch()
        periodic_buttons_layout.addWidget(self.run_periodic_button)
        periodic_buttons_layout.addStretch()
        periodic_layout.addRow(periodic_buttons_layout)

        scroll_layout.addWidget(periodic_group)

                                
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_settings)                       
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)                                               

                                       
        self.load_settings_to_ui()

                                            
        self.run_monthly_button.clicked.connect(self.trigger_monthly_report)
        self.run_joke_button.clicked.connect(self.trigger_joke_report)
        self.run_periodic_button.clicked.connect(self.trigger_periodic_check)

    def get_admin_user_id(self):
        """Return the ID of the authenticated administrator."""
                                                                             
        if self.parent_app and hasattr(self.parent_app, 'current_user_info') and \
           self.parent_app.current_user_info and \
           self.parent_app.current_user_info.get('is_admin'):
            return self.parent_app.current_user_info.get('user_id')
        else:
                                                                                           
            logging.error("get_admin_user_id called but no valid admin session found in parent_app.")
                                                                                       
                                                                                                   
                                                                          
            return None                                          
    
    def load_settings_to_ui(self):
        """Load settings from self.config into the UI widgets."""
        try:
                      
            self.bot_token_edit.setText(utils.get_secret('Telegram', 'BotToken', self.config, fallback=''))
            self.chat_id_edit.setText(utils.get_setting(self.config, 'Telegram', 'ChatID', fallback=''))
            self.notify_immediately_checkbox.setChecked(utils.get_setting(self.config, 'Telegram', 'NotifyImmediately', fallback='True').lower() == 'true')

                  
            self.line_access_token_edit.setText(utils.get_secret('LINE', 'ChannelAccessToken', self.config, fallback=''))
            self.line_secret_edit.setText(utils.get_secret('LINE', 'ChannelSecret', self.config, fallback=''))
            self.line_group_id_edit.setText(utils.get_setting(self.config, 'LINE', 'GroupID', fallback=''))

                   
            self.ngrok_domain_edit.setText(utils.get_setting(self.config, 'Ngrok', 'Domain', fallback=''))
            self.ngrok_authtoken_edit.setText(utils.get_secret('Ngrok', 'Authtoken', self.config, fallback=''))

                            
            self.monthly_enabled_checkbox.setChecked(utils.get_setting(self.config, 'Schedule', 'MonthlyReportEnabled', fallback='True').lower() == 'true')
            self.monthly_day_spinbox.setValue(int(utils.get_setting(self.config, 'Schedule', 'MonthlyReportDay', fallback='1')))
            self.monthly_hour_spinbox.setValue(int(utils.get_setting(self.config, 'Schedule', 'MonthlyReportHour', fallback='8')))
            self.last_monthly_label.setText(utils.get_setting(self.config, 'Schedule', 'LastMonthlyReportSent', fallback='Never'))

                         
            self.joke_enabled_checkbox.setChecked(utils.get_setting(self.config, 'Schedule', 'JokeReportEnabled', fallback='True').lower() == 'true')
            self.joke_hour_spinbox.setValue(int(utils.get_setting(self.config, 'Schedule', 'JokeReportHour', fallback='22')))
            self.last_joke_label.setText(utils.get_setting(self.config, 'Schedule', 'LastJokeReportSent', fallback='Never'))

                            
            self.periodic_enabled_checkbox.setChecked(utils.get_setting(self.config, 'Schedule', 'PeriodicCheckEnabled', fallback='True').lower() == 'true')
            self.periodic_days_spinbox.setValue(int(utils.get_setting(self.config, 'Schedule', 'PeriodicCheckDays', fallback='2')))
            self.periodic_hour_spinbox.setValue(int(utils.get_setting(self.config, 'Schedule', 'PeriodicCheckHour', fallback='22')))
            self.last_periodic_label.setText(utils.get_setting(self.config, 'Schedule', 'LastPeriodicCheckSent', fallback='Never'))

        except Exception as e:
            QMessageBox.critical(self, "Error Loading Settings", f"Could not load settings from config object: {e}")
            logging.error("Error populating admin settings dialog", exc_info=True)

    def save_settings(self):
        """Save UI settings back to the config object and file."""
        admin_id = self.get_admin_user_id()                                    
        if admin_id is None:
             QMessageBox.critical(self, "Error", "Admin authentication required to save settings.")
             return

        try:
                                       
                      
            bot_token = self.bot_token_edit.text().strip()
            chat_id = self.chat_id_edit.text().strip()
            notify_immediately = str(self.notify_immediately_checkbox.isChecked())

                            
            monthly_enabled = str(self.monthly_enabled_checkbox.isChecked())
            monthly_day = str(self.monthly_day_spinbox.value())
            monthly_hour = str(self.monthly_hour_spinbox.value())

                         
            joke_enabled = str(self.joke_enabled_checkbox.isChecked())
            joke_hour = str(self.joke_hour_spinbox.value())

                            
            periodic_enabled = str(self.periodic_enabled_checkbox.isChecked())
            periodic_days = str(self.periodic_days_spinbox.value())
            periodic_hour = str(self.periodic_hour_spinbox.value())

                                                                
                                                             
            config = self.config

                              
            config.set('Telegram', 'ChatID', chat_id)
            config.set('Telegram', 'NotifyImmediately', notify_immediately)

                  
            config.set('LINE', 'GroupID', self.line_group_id_edit.text().strip())
            utils.set_secret('Telegram', 'BotToken', bot_token, config)
            utils.set_secret('LINE', 'ChannelAccessToken', self.line_access_token_edit.text().strip(), config)
            utils.set_secret('LINE', 'ChannelSecret', self.line_secret_edit.text().strip(), config)

                   
            config.set('Ngrok', 'Domain', self.ngrok_domain_edit.text().strip())
            utils.set_secret('Ngrok', 'Authtoken', self.ngrok_authtoken_edit.text().strip(), config)

                              
            config.set('Schedule', 'MonthlyReportEnabled', monthly_enabled)
            config.set('Schedule', 'MonthlyReportDay', monthly_day)
            config.set('Schedule', 'MonthlyReportHour', monthly_hour)

            config.set('Schedule', 'JokeReportEnabled', joke_enabled)
            config.set('Schedule', 'JokeReportHour', joke_hour)

            config.set('Schedule', 'PeriodicCheckEnabled', periodic_enabled)
            config.set('Schedule', 'PeriodicCheckDays', periodic_days)
            config.set('Schedule', 'PeriodicCheckHour', periodic_hour)

                                 
            with open(utils.CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                config.write(configfile)

            logging.info(f"Admin settings saved to '{utils.CONFIG_FILE}' by UserID {admin_id}.")
            QMessageBox.information(self, "Settings Saved", f"Settings have been saved to {utils.CONFIG_FILE}.\nChanges to schedule will take effect after the next check or application restart.")

                                           
            db.log_audit_event(admin_id, 'Update Settings', 'settings.ini', None, "Admin updated application settings.")

            self.parent_app.config = utils.load_config()
            self.accept()                                     

        except Exception as e:
             QMessageBox.critical(self, "Error Saving Settings", f"Could not save settings: {e}")
             logging.error("Error saving admin settings", exc_info=True)

                                      
    def trigger_monthly_report(self):
         admin_id = self.get_admin_user_id()
         if admin_id is None: return
         if self.parent_app:
              reply = QMessageBox.question(self, "Confirm Run", "Run the monthly summary report for the previous month now?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
              if reply == QMessageBox.StandardButton.Yes:
                   logging.info(f"Manual trigger: Monthly Report by UserID {admin_id}")
                                                            
                   QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)              
                   try:
                       self.parent_app.run_monthly_report(force_run=True)
                       QMessageBox.information(self, "Report Triggered", "Monthly report generation initiated (check console/Telegram).")
                                                                                                                                 
                       self.config = utils.load_config()                                                                     
                       self.last_monthly_label.setText(utils.get_setting(self.config,'Schedule', 'LastMonthlyReportSent',fallback='N/A'))
                   except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to run report: {e}")
                        logging.error("Error during manual monthly report run", exc_info=True)
                   finally:
                        QApplication.restoreOverrideCursor()                  

    def trigger_joke_report(self):
         admin_id = self.get_admin_user_id()
         if admin_id is None: return
         if self.parent_app:
              reply = QMessageBox.question(self, "Confirm Run", "Run the end-of-month joke report for the current month now?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
              if reply == QMessageBox.StandardButton.Yes:
                   logging.info(f"Manual trigger: Joke Report by UserID {admin_id}")
                   QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                   try:
                       self.parent_app.run_joke_report(force_run=True)
                       QMessageBox.information(self, "Report Triggered", "Joke report generation initiated (check console/Telegram).")
                       self.config = utils.load_config()
                       self.last_joke_label.setText(utils.get_setting(self.config,'Schedule', 'LastJokeReportSent',fallback='N/A'))
                   except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to run report: {e}")
                        logging.error("Error during manual joke report run", exc_info=True)
                   finally:
                        QApplication.restoreOverrideCursor()

    def trigger_periodic_check(self):
         admin_id = self.get_admin_user_id()
         if admin_id is None: return
         if self.parent_app:
              reply = QMessageBox.question(self, "Confirm Run", "Run the periodic check (e.g., low stock) now?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
              if reply == QMessageBox.StandardButton.Yes:
                   logging.info(f"Manual trigger: Periodic Check by UserID {admin_id}")
                   QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                   try:
                       self.parent_app.run_periodic_check(force_run=True)
                       QMessageBox.information(self, "Check Triggered", "Periodic check initiated (check console/Telegram).")
                       self.config = utils.load_config()
                       self.last_periodic_label.setText(utils.get_setting(self.config,'Schedule', 'LastPeriodicCheckSent',fallback='N/A'))
                   except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to run check: {e}")
                        logging.error("Error during manual periodic check run", exc_info=True)
                   finally:
                        QApplication.restoreOverrideCursor()
                                              
class UserManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent                              
        self.setWindowTitle("Manage Users (Admin)")
        self.setMinimumSize(600, 450)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        table_group_layout = QVBoxLayout()
        form_group_layout = QFormLayout()
        button_layout = QHBoxLayout()

                            
        table_label = QLabel("Existing Users:")
        self.user_table = QTableWidget()                                 
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Is Admin?"])
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.user_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.user_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)                          
        self.user_table.verticalHeader().setVisible(False)                     
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)                       

        table_group_layout.addWidget(table_label)
        table_group_layout.addWidget(self.user_table)

                                              
        form_label = QLabel("Add / Manage User:")
        self.user_id_label = QLabel("N/A (Adding New)")                                
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("e.g. alex")
        self.is_admin_checkbox = QCheckBox("Grant Admin Rights")
        self.add_user_button = QPushButton("Add New User")

        form_group_layout.addRow(form_label)
        form_group_layout.addRow("Selected User ID:", self.user_id_label)
        form_group_layout.addRow("Username:", self.username_edit)
        form_group_layout.addRow(self.is_admin_checkbox)
        form_group_layout.addWidget(self.add_user_button)


                                
        self.reset_password_button = QPushButton("Reset Password")
        self.toggle_admin_button = QPushButton("Toggle Admin Status")
        self.delete_user_button = QPushButton("Delete Selected User")
        self.clear_selection_button = QPushButton("Clear Selection / New")
        self.close_button = QPushButton("Close")

        button_layout.addWidget(self.reset_password_button)
        button_layout.addWidget(self.toggle_admin_button)
        button_layout.addWidget(self.delete_user_button)
        button_layout.addWidget(self.clear_selection_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

                                 
        main_layout.addLayout(table_group_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(form_group_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(button_layout)

                                 
        self.user_table.itemSelectionChanged.connect(self.on_user_selected)
        self.add_user_button.clicked.connect(self.add_new_user)
        self.reset_password_button.clicked.connect(self.reset_password)
        self.toggle_admin_button.clicked.connect(self.toggle_admin_status)
        self.delete_user_button.clicked.connect(self.delete_selected_user)
        self.clear_selection_button.clicked.connect(self.clear_form)
        self.close_button.clicked.connect(self.accept)

                               
        self.load_users()
        self.clear_form()                                                

    
    def load_users(self):
        """Loads user data into the table."""
        try:
            users = db.get_all_users_details()
            self.user_table.setRowCount(len(users))
            self.user_table.setSortingEnabled(False)                         

            for row_idx, user in enumerate(users):
                user_id_item = QTableWidgetItem(str(user['user_id']))
                username_item = QTableWidgetItem(user['username'])
                is_admin_item = QTableWidgetItem("Yes" if user['is_admin'] else "No")

                                                     
                user_id_item.setFlags(user_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                username_item.setFlags(username_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                is_admin_item.setFlags(is_admin_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                is_admin_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.user_table.setItem(row_idx, 0, user_id_item)
                self.user_table.setItem(row_idx, 1, username_item)
                self.user_table.setItem(row_idx, 2, is_admin_item)

            self.user_table.resizeColumnsToContents()
            self.user_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.user_table.setSortingEnabled(True)               

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load users: {e}")
            logging.error("Failed to load users", exc_info=True)

    def on_user_selected(self):
        """Populates the form when a user row is selected."""
        selected_rows = self.user_table.selectedItems()                                    
        if selected_rows:
            selected_row_index = self.user_table.row(selected_rows[0])                 
            user_id = self.user_table.item(selected_row_index, 0).text()
            username = self.user_table.item(selected_row_index, 1).text()
            is_admin_text = self.user_table.item(selected_row_index, 2).text()

            self.user_id_label.setText(user_id)
            self.username_edit.setText(username)
            self.username_edit.setEnabled(False)                                             
            self.is_admin_checkbox.setChecked(is_admin_text == "Yes")
            self.is_admin_checkbox.setEnabled(False)                                           

            self.add_user_button.setEnabled(False)                     
                                   
            self.reset_password_button.setEnabled(True)
            self.toggle_admin_button.setEnabled(True)
            self.delete_user_button.setEnabled(True)
        else:
            self.clear_form()

    def clear_form(self):
        """Clears the form and resets button states."""
        self.user_table.clearSelection()
        self.user_id_label.setText("N/A (Adding New)")
        self.username_edit.clear()
        self.username_edit.setEnabled(True)                    
        self.is_admin_checkbox.setChecked(False)
        self.is_admin_checkbox.setEnabled(True)                    

        self.add_user_button.setEnabled(True)                    
                                
        self.reset_password_button.setEnabled(False)
        self.toggle_admin_button.setEnabled(False)
        self.delete_user_button.setEnabled(False)
        self.username_edit.setFocus()

    def add_new_user(self):
        """Handles adding a new user."""
        admin_id = self.get_admin_user_id()
        if admin_id is None: return                                     

        username = self.username_edit.text().strip()
        is_admin = 1 if self.is_admin_checkbox.isChecked() else 0

        if not username:
            QMessageBox.warning(self, "Input Error", "Username cannot be empty.")
            return

                                      
        if db.get_user(username):
             QMessageBox.warning(self, "Username Taken", f"The username '{username}' is already taken.")
             return

                             
        password, ok1 = QInputDialog.getText(self, "Set Password", f"Enter password for {username}:", QLineEdit.EchoMode.Password)
        if not ok1 or not password:
            QMessageBox.warning(self, "Cancelled", "Password cannot be empty. User not added.")
            return

        confirm_password, ok2 = QInputDialog.getText(self, "Confirm Password", "Confirm password:", QLineEdit.EchoMode.Password)
        if not ok2:
            return                 

        if password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match. User not added.")
            return

                                
        success, message = db.add_user(username, password, is_admin)
        if success:
                             
            new_user_data = db.get_user(username)                        
            if new_user_data:
                db.log_audit_event(admin_id, 'Add User', 'Users', new_user_data[0], f"Added user '{username}', Admin={bool(is_admin)}")
            QMessageBox.information(self, "Success", message)
            self.load_users()                
            self.clear_form()
            self.parent_app.load_combobox_data()                               
        else:
            QMessageBox.critical(self, "Error", f"Failed to add user: {message}")


    def get_admin_user_id(self):
        """Return the ID of the authenticated administrator."""
        if self.parent_app and hasattr(self.parent_app, 'current_user_info') and \
           self.parent_app.current_user_info and \
           self.parent_app.current_user_info.get('is_admin'):
            return self.parent_app.current_user_info.get('user_id')
        else:
            logging.error("get_admin_user_id called from UserManagementDialog but no valid admin session found in parent_app.")
                                             
                          
            return None

    def reset_password(self):
        """Handles resetting password for the selected user."""
        admin_id = self.get_admin_user_id()
        if admin_id is None: return

        user_id_str = self.user_id_label.text()
        username = self.username_edit.text()                           
        if user_id_str == "N/A (Adding New)":
            QMessageBox.warning(self, "Selection Error", "Please select a user from the table first.")
            return

        try:
            user_id = int(user_id_str)
        except ValueError:
             QMessageBox.critical(self, "Error", "Invalid User ID selected.")
             return

        new_password, ok1 = QInputDialog.getText(self, "Reset Password", f"Enter NEW password for {username}:", QLineEdit.EchoMode.Password)
        if not ok1 or not new_password:
             QMessageBox.warning(self, "Cancelled", "Password cannot be empty. Password not reset.")
             return

        confirm_password, ok2 = QInputDialog.getText(self, "Confirm New Password", "Confirm new password:", QLineEdit.EchoMode.Password)
        if not ok2:
             return

        if new_password != confirm_password:
             QMessageBox.warning(self, "Password Mismatch", "Passwords do not match. Password not reset.")
             return

                                
        success, message = db.reset_user_password(user_id, new_password, admin_id)                              
        if success:
            QMessageBox.information(self, "Success", message)
                                                                  
            self.clear_form()
        else:
            QMessageBox.critical(self, "Error", f"Failed to reset password: {message}")

    def toggle_admin_status(self):
        """Toggles the admin status for the selected user."""
        admin_id = self.get_admin_user_id()
        if admin_id is None: return

        user_id_str = self.user_id_label.text()
        username = self.username_edit.text()
        if user_id_str == "N/A (Adding New)":
            QMessageBox.warning(self, "Selection Error", "Please select a user from the table first.")
            return

        try:
            user_id = int(user_id_str)
        except ValueError:
             QMessageBox.critical(self, "Error", "Invalid User ID selected.")
             return

                                                          
        user_details = db.get_user(username)                                          
        if not user_details:
             QMessageBox.critical(self, "Error", f"Could not retrieve current status for user '{username}'.")
             return

        current_is_admin = bool(user_details[3])                                        
        new_admin_status = not current_is_admin

                      
        action_verb = "Grant" if new_admin_status else "Revoke"
        reply = QMessageBox.question(self, f"Confirm {action_verb} Admin",
                                     f"Are you sure you want to {action_verb.lower()} admin rights for user '{username}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, message = db.set_admin_status(user_id, new_admin_status, admin_id)                
            if success:
                QMessageBox.information(self, "Success", message)
                self.load_users()                                   
                self.clear_form()
            else:
                QMessageBox.critical(self, "Error", f"Failed to update admin status: {message}")


    def delete_selected_user(self):
        """Handles deleting the selected user."""
        admin_id = self.get_admin_user_id()
        if admin_id is None: return

        user_id_str = self.user_id_label.text()
        username = self.username_edit.text()
        if user_id_str == "N/A (Adding New)":
            QMessageBox.warning(self, "Selection Error", "Please select a user from the table first.")
            return

        try:
            user_id_to_delete = int(user_id_str)
        except ValueError:
             QMessageBox.critical(self, "Error", "Invalid User ID selected.")
             return

                             
        reply = QMessageBox.warning(self, 'Confirm Delete User',
                                     f"WARNING: Are you absolutely sure you want to delete the user '{username}' (ID: {user_id_to_delete})?\n\n"
                                     f"Their past transaction logs will remain but will show 'User ID: {user_id_to_delete} (Deleted)' or similar upon edit/delete attempt later if user_id becomes NULL.\n"
                                     f"THIS ACTION CANNOT BE UNDONE.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
             success, message = db.delete_user(user_id_to_delete, admin_id)                
             if success:
                 QMessageBox.information(self, "Success", message)
                 self.load_users()                
                 self.clear_form()
                 self.parent_app.load_combobox_data()                               
             else:
                 QMessageBox.critical(self, "Error", f"Failed to delete user: {message}")


class ChemicalManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent                                                   
        self.setWindowTitle("Manage Chemicals (Admin)")
        self.setMinimumSize(600, 400)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        table_layout = QVBoxLayout()
        form_layout = QFormLayout()
        button_layout = QHBoxLayout()

                            
        self.chem_table = QTableView()
        self.chem_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.chem_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.chem_table.setSortingEnabled(True)
        self.chem_table.setAlternatingRowColors(True)
        table_layout.addWidget(QLabel("Existing Chemicals:"))
        table_layout.addWidget(self.chem_table)

        self.model = QStandardItemModel(self)
        self.chem_table.setModel(self.model)
        self.chem_table.selectionModel().selectionChanged.connect(self.on_chemical_selected)
        
        

                                         
        self.chem_id_label = QLabel("")                         
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. DMEM")
        self.stock_edit = QLineEdit()
        self.stock_edit.setPlaceholderText("e.g. 0 or 100.5")
        self.stock_edit.setValidator(QDoubleValidator(-999999.99, 999999.99, 2))                               
        self.stock_edit.setPlaceholderText("Use 'Adjust' transaction for normal changes")
        self.threshold_edit = QLineEdit()
        self.threshold_edit.setPlaceholderText("e.g. 10.0")
        self.threshold_edit.setValidator(QDoubleValidator(0.0, 999999.99, 2))

        form_layout.addRow("ID:", self.chem_id_label)
        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Low Stock Threshold:", self.threshold_edit)

                         
        self.add_button = QPushButton("Add New Chemical")
        self.save_button = QPushButton("Save Changes")
        self.delete_button = QPushButton("Delete Selected Chemical")
        self.clear_button = QPushButton("Clear Form")
        self.close_button = QPushButton("Close")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

                                 
        main_layout.addLayout(table_layout)
        main_layout.addSpacing(15)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

                                 
        self.add_button.clicked.connect(self.add_new_chemical)
        self.save_button.clicked.connect(self.save_chemical_changes)
        self.delete_button.clicked.connect(self.delete_selected_chemical)
        self.clear_button.clicked.connect(self.clear_form)
        self.close_button.clicked.connect(self.accept)               

                              
        self.load_chemicals()
        self.clear_form()                         

    def load_chemicals(self):
        """Loads chemical data into the table."""
        self.model.clear()
        try:
            chem_data = db.get_all_chemicals_details()
            headers = ["ID", "Name", "Current Stock", "Threshold"]
            self.model.setHorizontalHeaderLabels(headers)

            for row_idx, chem in enumerate(chem_data):
                self.model.setItem(row_idx, 0, QStandardItem(str(chem['chemical_id'])))
                self.model.setItem(row_idx, 1, QStandardItem(chem['name']))
                self.model.setItem(row_idx, 2, QStandardItem(str(chem['current_stock'])))
                self.model.setItem(row_idx, 3, QStandardItem(str(chem['threshold'])))

            self.chem_table.resizeColumnsToContents()
            self.chem_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)            
            self.chem_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)              
            self.chem_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.chem_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load chemicals: {e}")
            logging.error("Failed to load chemicals", exc_info=True)

    def on_chemical_selected(self, selected, deselected):
        """Populates the form when a row is selected."""
        indexes = self.chem_table.selectionModel().selectedRows()
        if indexes:
            selected_row = indexes[0].row()
            chem_id = self.model.item(selected_row, 0).text()
            name = self.model.item(selected_row, 1).text()
            stock = self.model.item(selected_row, 2).text()
            threshold = self.model.item(selected_row, 3).text()

            self.chem_id_label.setText(chem_id)
            self.name_edit.setText(name)
            self.stock_edit.setText(stock)
            self.threshold_edit.setText(threshold)
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.add_button.setEnabled(False)                           
        else:
            self.clear_form()                             

    def clear_form(self):
        """Clears the input form fields."""
        self.chem_id_label.setText("")
        self.name_edit.clear()
        self.stock_edit.clear()
        self.threshold_edit.clear()
        self.chem_table.clearSelection()
        self.save_button.setEnabled(False)                                         
        self.delete_button.setEnabled(False)
        self.add_button.setEnabled(True)             
        self.name_edit.setFocus()

    
    def add_new_chemical(self):
        """Adds a new chemical based on form input."""
        admin_id = self.get_admin_user_id()
        if admin_id is None:
             QMessageBox.critical(self, "Error", "Admin not logged in.")
             return

        name = self.name_edit.text().strip()
        stock_str = self.stock_edit.text().strip() or "0"                        
        threshold_str = self.threshold_edit.text().strip() or "0"                        

        if not name:
            QMessageBox.warning(self, "Input Error", "Chemical Name cannot be empty.")
            return

        try:
            stock = float(stock_str)
            threshold = float(threshold_str)
            if threshold < 0: threshold = 0                               
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Stock and Threshold must be valid numbers.")
            return

        success, message = db.add_chemical(name, stock, threshold)
        if success:
                              
             db.log_audit_event(admin_id, 'Add Chemical', 'Chemicals', db.get_chemical(name)['chemical_id'], f"Added: {name}, Stock: {stock}, Threshold: {threshold}")
             QMessageBox.information(self, "Success", message)
             self.load_chemicals()               
             self.clear_form()                 
             self.parent_app.load_combobox_data()                                  
        else:
             QMessageBox.critical(self, "Error", message)

    def save_chemical_changes(self):
        """Saves changes to the selected chemical's Name and Threshold."""
        admin_id = self.get_admin_user_id()
        if admin_id is None: return

        chem_id_str = self.chem_id_label.text()
        if not chem_id_str or chem_id_str == "N/A":
            QMessageBox.warning(self, "Selection Error", "No chemical selected to save changes.")
            return

        name = self.name_edit.text().strip()
        threshold_str = self.threshold_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Chemical Name cannot be empty.")
            return

        try:
            chem_id = int(chem_id_str)
            threshold = float(threshold_str) if threshold_str else 0.0
            if threshold < 0: threshold = 0

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Threshold must be a valid number.")
            return
        except Exception as e:
             QMessageBox.critical(self, "Error", f"Error processing input: {e}")
             return

                                                     
        success, message = db.update_chemical_details(chem_id, name, threshold, admin_id)

        if success:
                                                 
             QMessageBox.information(self, "Success", message)
             self.load_chemicals()               
             self.clear_form()               
             if self.parent_app: self.parent_app.load_combobox_data()                                   
        else:
             QMessageBox.critical(self, "Error", message)                         

    def get_admin_user_id(self):
        """Return the ID of the authenticated administrator."""
        if self.parent_app and hasattr(self.parent_app, 'current_user_info') and \
           self.parent_app.current_user_info and \
           self.parent_app.current_user_info.get('is_admin'):
            return self.parent_app.current_user_info.get('user_id')
        else:
            logging.error("get_admin_user_id called from UserManagementDialog but no valid admin session found in parent_app.")
                                             
                          
            return None
    
    def delete_selected_chemical(self):
        """Deletes the selected chemical if possible."""
        admin_id = self.get_admin_user_id()
        if admin_id is None:
             QMessageBox.critical(self, "Error", "Admin not logged in.")
             return

        chem_id_str = self.chem_id_label.text()
        name = self.name_edit.text()                                    
        if not chem_id_str:
            QMessageBox.warning(self, "Selection Error", "No chemical selected to delete.")
            return

        reply = QMessageBox.question(self, 'Confirm Delete',
                                     f"Are you sure you want to delete the chemical '{name}' (ID: {chem_id_str})?\n"
                                     f"This is only possible if there are no transactions associated with it.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
             try:
                chem_id = int(chem_id_str)
                success, message = db.delete_chemical(chem_id, admin_id)                                 
                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_chemicals()
                    self.clear_form()
                    self.parent_app.load_combobox_data()                     
                else:
                    QMessageBox.critical(self, "Error", message)
             except ValueError:
                  QMessageBox.critical(self, "Error", "Invalid Chemical ID.")
             except Exception as e:
                  QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
                  logging.error(f"Error deleting chemical {chem_id_str}", exc_info=True)

                              
class HistoryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction History")
        self.setGeometry(300, 100, 950, 800)                        
        self.parent_app = parent                                                

                         
        main_layout = QVBoxLayout(self)
        filter_layout = QGridLayout()                             
                                      
        button_layout = QVBoxLayout()                                        
        

                                
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))                           
        filter_layout.addWidget(QLabel("From:"), 0, 0)
        filter_layout.addWidget(self.start_date_edit, 0, 1)

        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())                   
        filter_layout.addWidget(QLabel("To:"), 0, 2)
        filter_layout.addWidget(self.end_date_edit, 0, 3)

        self.user_filter_edit = QLineEdit()
        self.user_filter_edit.setPlaceholderText("Any user")
        filter_layout.addWidget(QLabel("User:"), 1, 0)
        filter_layout.addWidget(self.user_filter_edit, 1, 1)

        self.chemical_filter_edit = QLineEdit()
        self.chemical_filter_edit.setPlaceholderText("Any chemical")
        filter_layout.addWidget(QLabel("Chemical:"), 1, 2)
        filter_layout.addWidget(self.chemical_filter_edit, 1, 3)

        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems(["All", "TakeOut", "FillIn", "Adjust", "Edit", "Delete"])                     
        filter_layout.addWidget(QLabel("Type:"), 2, 0)
        filter_layout.addWidget(self.type_filter_combo, 2, 1)

        self.filter_button = QPushButton("Apply Filters View")
        self.reset_button = QPushButton("Reset Filters")
        filter_layout.addWidget(self.filter_button, 2, 2)
        filter_layout.addWidget(self.reset_button, 2, 3)

        main_layout.addLayout(filter_layout)

                            
        self.history_table = QTableView()
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)            
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setSortingEnabled(True)                       
                                                                                                
        main_layout.addWidget(self.history_table)
        
        

                                     
        self.model = QStandardItemModel(self)
        self.history_table.setModel(self.model)
        
        self.export_button = QPushButton("Export Current View to Excel")
        temp_h_layout = QHBoxLayout()
        temp_h_layout.addStretch()                    
        temp_h_layout.addWidget(self.export_button)
        temp_h_layout.addStretch()                                  
        main_layout.addLayout(temp_h_layout)                                       
                                                  
                                                   
        
                                              
                                                
        export_range_group = QGroupBox("Direct Export by Date Range")
        export_range_layout = QFormLayout(export_range_group)                           

        self.export_start_date = QDateEdit(calendarPopup=True)
        self.export_start_date.setDate(QDate.currentDate().addMonths(-1))                         
        self.export_end_date = QDateEdit(calendarPopup=True)
        self.export_end_date.setDate(QDate.currentDate())                   

        self.export_by_range_button = QPushButton("Export History for Selected Range")

        export_range_layout.addRow("Export From:", self.export_start_date)
        export_range_layout.addRow("Export To:", self.export_end_date)
                                                                   
        export_range_layout.addWidget(self.export_by_range_button)

        main_layout.addWidget(export_range_group)                                  

        
                                        
        report_groupbox = QGroupBox("Advanced Reports")                 
        report_form_layout = QFormLayout(report_groupbox)

        report_date_layout = QHBoxLayout()                                     
        current_year = QDate.currentDate().year()
        self.report_start_month = QComboBox()
        self.report_start_month.addItems([f"{m:02d}" for m in range(1, 13)])
        self.report_start_year = QSpinBox()
        self.report_start_year.setRange(2020, current_year + 5)
        self.report_start_year.setValue(current_year)

        self.report_end_month = QComboBox()
        self.report_end_month.addItems([f"{m:02d}" for m in range(1, 13)])
        self.report_end_month.setCurrentIndex(QDate.currentDate().month()-1)                 
        self.report_end_year = QSpinBox()
        self.report_end_year.setRange(2020, current_year + 5)
        self.report_end_year.setValue(current_year)

        report_date_layout.addWidget(QLabel("From:"))
        report_date_layout.addWidget(self.report_start_month)
        report_date_layout.addWidget(self.report_start_year)
        report_date_layout.addWidget(QLabel("To:"))
        report_date_layout.addWidget(self.report_end_month)
        report_date_layout.addWidget(self.report_end_year)
        report_date_layout.addStretch()

        self.export_monthly_button = QPushButton("Export Monthly Usage and Summarize (2 Sheets)")

        report_form_layout.addRow("Report Period:", report_date_layout)
        report_form_layout.addWidget(self.export_monthly_button)

        main_layout.addWidget(report_groupbox)
                                
                                                                         
                               
        self.edit_button = QPushButton("Edit Selected")
        self.delete_button = QPushButton("Delete Selected")
        self.edit_button.setVisible(False)             
        self.delete_button.setVisible(False)             
                                 
                                                                 
                                                                     
                                 
                                   

        button_layout_h = QHBoxLayout()                                         
        button_layout_h.addStretch()
                                                                                               
        button_layout_h.addWidget(self.edit_button)
        button_layout_h.addWidget(self.delete_button)
        button_layout_h.addStretch()

        main_layout.addLayout(button_layout_h)


                                 
        self.filter_button.clicked.connect(self.load_history)
        self.reset_button.clicked.connect(self.reset_filters_and_load)
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_monthly_button.clicked.connect(self.export_monthly_usage_report)
                                 
        self.export_by_range_button.clicked.connect(self.export_history_by_date_range)
        
                                   
        self.edit_button.clicked.connect(self.edit_selected_entry)
        self.delete_button.clicked.connect(self.delete_selected_entry)
        
        QTimer.singleShot(0, self.connect_selection_signal)

                                   
        self.load_history()
    
    
    def export_history_by_date_range(self):
        """Exports transaction history for a selected date range directly from DB."""
        start_date = self.export_start_date.date()
        end_date = self.export_end_date.date()

                                
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Date Range", "Start date cannot be after end date.")
            return

                                  
        options = QFileDialog.Option(0)
        default_filename = f"history_export_{start_date.toString('yyyyMMdd')}_{end_date.toString('yyyyMMdd')}.xlsx"
        file_name, _ = QFileDialog.getSaveFileName(self,
                                                  "Save History Export As...",
                                                  default_filename,
                                                  "Excel Files (*.xlsx);;All Files (*)",
                                                  options=options)

        if not file_name:
            return                 

                                         
        if not file_name.lower().endswith('.xlsx'):
            file_name += '.xlsx'

                                         
        filters = {}
                                                      
        filters['start_date'] = start_date.toString("yyyy-MM-dd") + " 00:00:00"
        filters['end_date'] = end_date.toString("yyyy-MM-dd") + " 23:59:59"

                                                             
        user_filter = self.user_filter_edit.text().strip()
        if user_filter:
            filters['username'] = user_filter                                   

        chemical_filter = self.chemical_filter_edit.text().strip()
        if chemical_filter:
            filters['chemical_name'] = chemical_filter                          

        type_filter = self.type_filter_combo.currentText()
        if type_filter != "All":
            filters['transaction_type'] = type_filter
                                      

        logging.info(f"Initiating direct export with filters: {filters}")
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))                  

        try:
                                                  
            history_data = db.get_transaction_history(filters)                               

            if not history_data:
                QMessageBox.information(self, "No Data", "No transaction records found for the selected criteria.")
                return                  

                                     
            df = pd.DataFrame(history_data)
            
            rename_map = {
                "timestamp": "Time",
                "username_logged": "Name",
                "chemical_name_logged": "Chemical",
                "transaction_type": "Type",
                "quantity": "Number",
                "notes": "Notes"
            }
            df.rename(columns=rename_map, inplace=True)
            
                                                                    
            final_columns = ["Time", "Name", "Chemical", "Type", "Number", "Notes"]
                                                       
            df_export = df[[col for col in final_columns if col in df.columns]]
            
                                          
            df_export.to_excel(file_name, index=False, engine='openpyxl')

            QMessageBox.information(self, "Export Successful",
                                    f"History data successfully exported to:\n{os.path.basename(file_name)}")
            logging.info(f"Direct history export successful to {file_name}")

        except Exception as e:
            logging.error(f"Error during direct history export to {file_name}: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Could not export history data:\n{e}")

        finally:
            QApplication.restoreOverrideCursor()                       
    
    def _get_column_index(self, header_name):
        """Helper method to get column index by header name."""
        for i in range(self.model.columnCount()):
                                                             
            header_item = self.model.horizontalHeaderItem(i)
            if header_item and header_item.text() == header_name:
                return i
        logging.warning(f"Column header '{header_name}' not found.")
        return None                                 

    def export_monthly_usage_report(self):
        """Exports monthly chemical usage summary to Excel."""
        start_month = int(self.report_start_month.currentText())
        start_year = self.report_start_year.value()
        end_month = int(self.report_end_month.currentText())
        end_year = self.report_end_year.value()

                           
        if datetime(start_year, start_month, 1) > datetime(end_year, end_month, 1):
            QMessageBox.warning(self, "Invalid Date Range", "Start date cannot be after end date.")
            return

        logging.info(f"Exporting monthly usage from {start_year}-{start_month:02d} to {end_year}-{end_month:02d}")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
                                                
            summary_data = db.get_monthly_chemical_summary(start_year, start_month, end_year, end_month)

            if summary_data is None:                             
                QMessageBox.critical(self, "Database Error", "Could not retrieve summary data from database.")
                return
            if not summary_data:                                          
                QMessageBox.information(self, "No Data", "No FillIn or TakeOut data found for the selected period.")
                return

                                                                         
            df_raw = pd.DataFrame(summary_data)

                                                   
                                                                                               
            try:
                df_raw['YearMonth'] = df_raw['Year'].astype(str) + '-' + df_raw['Month'].astype(str)
                                                                  
                df_raw['YearMonth'] = pd.to_datetime(df_raw['YearMonth'], format='%Y-%m').dt.to_period('M')
                df_raw = df_raw.sort_values('YearMonth')
                df_raw['YearMonth'] = df_raw['YearMonth'].astype(str)                                        

                pivot_df = pd.pivot_table(df_raw,
                                        index='Chemical',
                                        columns=['YearMonth', 'Type'],             
                                        values='TotalQuantity',
                                        fill_value=0)                                    

                                                    
                pivot_df['Total FillIn'] = pivot_df.xs('FillIn', level='Type', axis=1).sum(axis=1)
                pivot_df['Total TakeOut'] = pivot_df.xs('TakeOut', level='Type', axis=1).sum(axis=1)
                pivot_df['Net Change'] = pivot_df['Total FillIn'] - pivot_df['Total TakeOut']

            except Exception as pivot_err:
                logging.error(f"Error creating pivot table: {pivot_err}", exc_info=True)
                QMessageBox.warning(self, "Pivot Error", "Could not create summary pivot table. Exporting raw data only.")
                pivot_df = None                                    

                                      
            options = QFileDialog.Option(0)
            default_filename = f"Monthly_Usage_{start_year}{start_month:02d}_{end_year}{end_month:02d}.xlsx"
            file_name, _ = QFileDialog.getSaveFileName(self,
                                                    "Save Monthly Usage Report As...",
                                                    default_filename,
                                                    "Excel Files (*.xlsx);;All Files (*)",
                                                    options=options)

            if file_name:
                if not file_name.lower().endswith('.xlsx'):
                    file_name += '.xlsx'

                                                       
                try:
                    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                        df_raw[['Year', 'Month', 'Chemical', 'Type', 'TotalQuantity']].to_excel(writer, sheet_name='Raw Data', index=False)
                        if pivot_df is not None:
                            pivot_df.to_excel(writer, sheet_name='Summary Pivot')

                                                               
                                                                                                   
                                                                                 
                                                                                             
                                                 
                                                    
                                                                          
                                                                            
                                                                                     
                                                                                            
                                                                                              

                    QMessageBox.information(self, "Export Successful", f"Monthly usage report exported to:\n{file_name}")
                except Exception as write_err:
                    QMessageBox.critical(self, "Export Error", f"Could not write Excel file:\n{write_err}")
                    logging.error(f"Error writing Excel file {file_name}", exc_info=True)

        finally:
            QApplication.restoreOverrideCursor()                             

    def connect_selection_signal(self):
        """Connects the selection changed signal after initialization."""
        selection_model = self.history_table.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.on_selection_changed)
            logging.info("History table selection signal connected.")                             
        else:
            logging.error("Error: History table selection model is still None after timer.")
        self.history_table.doubleClicked.connect(self.handle_double_click)
        logging.info("History table double-click signal connected.")
    
    def handle_double_click(self, index):
        """Handles double-clicking on a row, triggering edit note function."""
                                                      
        logging.info(f"Double click detected on row {index.row()}, column {index.column()}")
                                              
        self.history_table.selectRow(index.row())
                            
        self.edit_selected_entry()

    def update_admin_controls(self, is_logged_in, is_admin):
        """Shows or hides/enables/disables controls based on login status and selection."""
        has_selection = bool(self.history_table.selectionModel() and self.history_table.selectionModel().hasSelection())
        can_modify = is_logged_in and has_selection

        self.edit_button.setEnabled(can_modify)
        self.delete_button.setEnabled(can_modify)

        self.edit_button.setVisible(is_logged_in)                            
        self.delete_button.setVisible(is_logged_in)                            

        tooltip = ""
        if not is_logged_in:
            tooltip = "Please log in to modify history."
        elif not has_selection:
             tooltip = "Select a transaction row to modify."

        self.edit_button.setToolTip(tooltip)
        self.delete_button.setToolTip(tooltip)
    
        
    def get_selected_transaction_id(self):
        """Gets the transaction_id from the selected row's hidden ID column."""
        selected_indexes = self.history_table.selectedIndexes()
        if not selected_indexes:
            return None

        selected_row = selected_indexes[0].row()
                                                                                
        header_labels = [self.model.horizontalHeaderItem(i).text() for i in range(self.model.columnCount())]
        try:
            id_col_index = header_labels.index("ID")
            id_item = self.model.item(selected_row, id_col_index)
            if id_item:
                return int(id_item.text())
        except (ValueError, IndexError, TypeError):
            logging.error("Error finding or converting transaction ID column.")
            return None
        return None
    
    def edit_selected_entry(self):
        """Handles editing the notes of the selected transaction log entry."""
                                            
        if not self.parent_app or not self.parent_app.current_user_info:
            QMessageBox.warning(self, "Authentication Required", "You must be logged in to edit entries.")
            return

        logged_in_user = self.parent_app.current_user_info
        logged_in_user_id = logged_in_user['user_id']
        is_admin = logged_in_user['is_admin']

                                                                      
        selected_indexes = self.history_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        selected_row = selected_indexes[0].row()                                    
        transaction_id = self.get_selected_transaction_id()

        if transaction_id is None:
             QMessageBox.critical(self, "Error", "Could not retrieve Transaction ID for the selected row.")
             return

                                       
                                                                                                       
             
                                                     
                                                                               
                                                                                 
                                         
                                                                               
                                                                                             


                                                            
        transaction_details = db.get_transaction_details(transaction_id)
        current_note = transaction_details.get('notes', "")
        if not transaction_details:
             QMessageBox.critical(self, "Error", f"Could not find details for transaction ID {transaction_id}.")
             return

        owner_user_id = transaction_details.get('user_id')                             

                              
        can_edit = False
        if is_admin:
            can_edit = True                          
        elif owner_user_id is not None and owner_user_id == logged_in_user_id:
            can_edit = True                                
        elif owner_user_id is None and not is_admin:
             QMessageBox.warning(self, "Permission Denied", "Only admins can edit 'Whoknows' entries.")
             return
        else:                                            
             QMessageBox.warning(self, "Permission Denied", "You can only edit your own entries.")
             return

        if not can_edit:
             QMessageBox.warning(self, "Permission Denied", "You do not have permission to edit this entry.")
             return

                                                    
        accepted, (username, password) = LoginDialog.getLoginCredentials(self)
        if not accepted:
            return                                
        verified_user = db.verify_user(logged_in_user['username'], password)
        if not verified_user or verified_user['user_id'] != logged_in_user_id:
            QMessageBox.critical(self, "Authentication Failed", "Incorrect password.")
            return

                                                                            
        new_note, ok = QInputDialog.getMultiLineText(self, "Edit Note",
                                                    f"Enter new note for Transaction ID {transaction_id}:"
                                                    f"\n(User: {transaction_details['username_logged']}, Chemical: {transaction_details['chemical_name_logged']}, Qty: {transaction_details['quantity']})",
                                                    current_note)                    

        if ok:                                                              
            new_note = new_note.strip()                                     

                                                                                          
                                          
                                                                                      
                        

                                                    
                                                          
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            success, message = db.update_transaction_note(transaction_id, new_note, logged_in_user_id)
            QApplication.restoreOverrideCursor()                  

            if success:
                                                            
                try:
                    notes_col_idx = self._get_column_index("Notes")
                    if notes_col_idx is not None and selected_row >= 0:
                        note_item = self.model.item(selected_row, notes_col_idx)
                        if note_item:
                            note_item.setText(new_note)                         
                            logging.info(f"UI Updated: Row {selected_row}, Column 'Notes' set for transaction {transaction_id}")
                        else:
                             logging.warning(f"Could not find item at row {selected_row}, col {notes_col_idx} to update note.")
                    else:
                         logging.warning(f"Could not find 'Notes' column index or invalid row index ({selected_row}) for UI update.")
                except Exception as ui_update_err:
                    logging.error(f"Error updating UI model after note edit: {ui_update_err}", exc_info=True)
                                                                                  
                                           

                QMessageBox.information(self, "Success", message)
                                                               
            else:
                QMessageBox.critical(self, "Update Failed", message)
                                                    
        
    def delete_selected_entry(self):
        """Handles deleting the selected transaction log entry."""
                                       
        if not self.parent_app or not self.parent_app.current_user_info:
            QMessageBox.warning(self, "Authentication Required", "You must be logged in to delete entries.")
                                                                                  
            return

        logged_in_user = self.parent_app.current_user_info
        logged_in_user_id = logged_in_user['user_id']
        is_admin = logged_in_user['is_admin']

                                        
        selected_indexes = self.history_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Selection Error", "Please select a row to delete.")
            return

        selected_row = selected_indexes[0].row()
        transaction_id = self.get_selected_transaction_id()                          

        if transaction_id is None:
            QMessageBox.critical(self, "Error", "Could not retrieve Transaction ID for the selected row.")
            return

                                                       
        transaction_details = db.get_transaction_details(transaction_id)
        if not transaction_details:
            QMessageBox.critical(self, "Error", f"Could not find details for transaction ID {transaction_id}.")
            return

        owner_user_id = transaction_details.get('user_id')                                  

                              
        can_delete = False
        if is_admin:
            can_delete = True                            
        elif owner_user_id is not None and owner_user_id == logged_in_user_id:
            can_delete = True                                  
        elif owner_user_id is None and not is_admin:
            QMessageBox.warning(self, "Permission Denied", "Only admins can delete 'Whoknows' entries.")
            return
        else:                                            
            QMessageBox.warning(self, "Permission Denied", "You can only delete your own entries.")
            return

        if not can_delete:                                                           
            QMessageBox.warning(self, "Permission Denied", "You do not have permission to delete this entry.")
            return

                             
        reply = QMessageBox.question(self, 'Confirm Deletion',
                                    f"Are you sure you want to mark transaction ID {transaction_id} as deleted?\n"
                                    f"(User: {transaction_details['username_logged']}, Chemical: {transaction_details['chemical_name_logged']}, Qty: {transaction_details['quantity']}, Type: {transaction_details['transaction_type']})\n"
                                    f"Stock will be adjusted accordingly.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                    QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
                                                                                   
                                                    
            accepted, (username, password) = LoginDialog.getLoginCredentials(self)
            if not accepted:
                return                                
            verified_user = db.verify_user(logged_in_user['username'], password)                                       
            if not verified_user or verified_user['user_id'] != logged_in_user_id:
                QMessageBox.critical(self, "Authentication Failed", "Incorrect password.")
                return

                           
            reason, ok = QInputDialog.getText(self, "Reason for Deletion", "Please provide a brief reason for deleting this entry:")
            if ok and reason.strip():
                                                        
                reason_text = reason.strip()
                                      
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                success, message = db.mark_transaction_deleted(transaction_id, logged_in_user_id, reason_text)
                QApplication.restoreOverrideCursor()                  

                if success:
                                                                
                    try:
                                                                                   
                        updated_details = db.get_transaction_details(transaction_id)
                        final_note = updated_details['notes'] if updated_details else f"DELETED by {logged_in_user['username']}. Reason: {reason_text}"

                        type_col_idx = self._get_column_index("Type")
                        notes_col_idx = self._get_column_index("Notes")

                                                    
                        if type_col_idx is not None and selected_row >= 0:
                            type_item = self.model.item(selected_row, type_col_idx)
                            if type_item: type_item.setText("Delete")

                        if notes_col_idx is not None and selected_row >= 0:
                            note_item = self.model.item(selected_row, notes_col_idx)
                            if note_item: note_item.setText(final_note)

                                                                
                        deleted_color = QColor('gray')
                        deleted_font = QFont()
                        deleted_font.setStrikeOut(True)

                        if selected_row >= 0:
                            for col in range(self.model.columnCount()):
                                item = self.model.item(selected_row, col)
                                if item:
                                    item.setForeground(deleted_color)
                                    item.setFont(deleted_font)
                            logging.info(f"UI Updated: Row {selected_row} formatted as deleted for transaction {transaction_id}")
                        else:
                            logging.warning(f"Invalid row index ({selected_row}) for UI formatting update.")

                    except Exception as ui_update_err:
                         logging.error(f"Error updating UI model after delete: {ui_update_err}", exc_info=True)
                                                            
                                               

                    QMessageBox.information(self, "Success", message)
                                                                   
                else:
                    QMessageBox.critical(self, "Deletion Failed", message)
            elif ok:
                QMessageBox.warning(self, "Deletion Cancelled", "A reason is required for deletion.")
                                                          
    
    
    def load_history(self):
        """Load transaction data based on current filters."""
        filters = {}
                                                                         
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd") + " 00:00:00"
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd") + " 23:59:59"
        filters['start_date'] = start_date
        filters['end_date'] = end_date

        user_filter = self.user_filter_edit.text().strip()
        if user_filter:
            filters['username'] = user_filter

        chemical_filter = self.chemical_filter_edit.text().strip()
        if chemical_filter:
            filters['chemical_name'] = chemical_filter

        type_filter = self.type_filter_combo.currentText()
        if type_filter != "All":
            filters['transaction_type'] = type_filter

        logging.info("Loading history with filters: %s", filters)

        try:
            history_data = db.get_transaction_history(filters)
            self.populate_table(history_data)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load history: {e}")
            logging.error("Failed to load history", exc_info=True)

    def populate_table(self, data):
        """Populate the table model and mark deleted transactions visually."""
        self.model.clear()                            

                                                                 
        headers = ["Timestamp", "User", "Chemical", "Type", "Quantity", "Notes", "ID"]
        self.model.setHorizontalHeaderLabels(headers)
        self.model.setColumnCount(len(headers))             

                                                                          
        try:
            id_col_index = headers.index("ID")
            self.history_table.setColumnHidden(id_col_index, True)
        except ValueError:
            logging.warning("Could not find 'ID' column header to hide (setting headers).")

                                   
        if not data:
            logging.info("No history data to populate.")
            return

                               
        self.model.setRowCount(len(data))

                                                                                                          
        key_map = {
            "Timestamp": "timestamp",
            "User": "username_logged",
            "Chemical": "chemical_name_logged",
            "Type": "transaction_type",
            "Quantity": "quantity",
            "Notes": "notes",
            "ID": "transaction_id"
        }

                                                
        deleted_color = QColor('gray')
        deleted_font = QFont()
        deleted_font.setStrikeOut(True)

                                                
        for row_idx, row_data in enumerate(data):
                                                                                       
            transaction_type_value = row_data.get(key_map["Type"])                                   
            is_deleted_row = (transaction_type_value == 'Delete')
                                         

                                                               
            for col_idx, header in enumerate(headers):
                db_key = key_map.get(header)                               
                item = None                

                if db_key:
                    value = row_data.get(db_key)              
                    display_value = str(value) if value is not None else ""                     
                    item = QStandardItem(display_value)                    

                                                                            
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                                                                             
                                                                             
                    if is_deleted_row:
                        item.setForeground(deleted_color)
                        item.setFont(deleted_font)
                                                        
                else:
                                                                          
                    logging.warning(f"Header '{header}' not found in key_map for row {row_idx}")
                    item = QStandardItem("")                

                                                               
                if item is not None:
                     self.model.setItem(row_idx, col_idx, item)

                                                                   
        self.history_table.resizeColumnsToContents()
        try:
                                                      
            chemical_col_index = headers.index("Chemical")
            notes_col_index = headers.index("Notes")
            self.history_table.horizontalHeader().setSectionResizeMode(chemical_col_index, QHeaderView.ResizeMode.Stretch)
            self.history_table.horizontalHeader().setSectionResizeMode(notes_col_index, QHeaderView.ResizeMode.Stretch)
                                        
            for i, header in enumerate(headers):
                if header not in ["Chemical", "Notes", "ID"]:                                              
                    self.history_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        except ValueError:
            logging.warning("Could not find 'Chemical' or 'Notes' column for resizing.")
        except Exception as resize_err:
             logging.error(f"Error resizing columns: {resize_err}")
    
    
    def reset_filters_and_load(self):
        """Reset filter fields to defaults and reload data."""
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_edit.setDate(QDate.currentDate())
        self.user_filter_edit.clear()
        self.chemical_filter_edit.clear()
        self.type_filter_combo.setCurrentIndex(0)                   
        self.load_history()

    def export_to_excel(self):
            """Export the currently displayed table data to an Excel file."""
                                             
            data_to_export = []
                                                              
            headers = []
            visible_col_indices = []
            for i in range(self.model.columnCount()):
                 if not self.history_table.isColumnHidden(i):
                      header_text = self.model.horizontalHeaderItem(i).text()
                                                                                          
                                               
                      headers.append(header_text)
                      visible_col_indices.append(i)


            for row in range(self.model.rowCount()):
                row_data = {}
                for i, header in enumerate(headers):
                    model_index = self.model.index(row, visible_col_indices[i])
                                                                            
                    row_data[header] = self.model.data(model_index, Qt.ItemDataRole.DisplayRole)                    
                data_to_export.append(row_data)

            if not data_to_export:
                                                                       
                QMessageBox.information(self, "Export", "No data to export.")
                                           
                return

                                        
            options = QFileDialog.Option(0)
            default_filename = f"chemical_history_{QDate.currentDate().toString('yyyyMMdd')}.xlsx"
            file_name, _ = QFileDialog.getSaveFileName(self,
                                                      "Save History As...",
                                                      default_filename,
                                                      "Excel Files (*.xlsx);;All Files (*)",
                                                      options=options)

            if file_name:
                                                 
                if not file_name.lower().endswith('.xlsx'):
                    file_name += '.xlsx'
                try:
                    df = pd.DataFrame(data_to_export)
                                                                   
                    rename_map = {
                        "Timestamp": "Time",
                        "User": "Name",
                        "Chemical": "Chemical",
                        "Type": "Type",
                        "Quantity": "Number",
                        "Notes": "Notes"
                    }
                    df.rename(columns=rename_map, inplace=True)
                                      
                                  
                    df.to_excel(file_name, index=False, engine='openpyxl')                          
                                                           
                    QMessageBox.information(self, "Export Successful", f"Data exported successfully to:\n{file_name}")
                                      
                except Exception as e:
                                                           
                    QMessageBox.critical(self, "Export Error", f"Could not save the file:\n{e}")
                                      
                    logging.error(f"Error exporting data to {file_name}", exc_info=True)              
                
    def on_selection_changed(self, selected=None, deselected=None):                        
        """Update button states when table selection changes."""
                                                                             
        is_logged_in = False
        is_admin = False
                                                             
        if self.parent_app and hasattr(self.parent_app, 'current_user_info') and self.parent_app.current_user_info:
             is_logged_in = True
             is_admin = self.parent_app.current_user_info.get('is_admin', False)

        self.update_admin_controls(is_logged_in, is_admin)

   

                                    

class RegisterUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New User")
        self.setModal(True)

        layout = QFormLayout(self)

        self.username_edit = QLineEdit(self)
        self.username_edit.setPlaceholderText("e.g. alex")
        self.password_edit = QLineEdit(self)
        self.password_edit.setPlaceholderText("Enter a password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit = QLineEdit(self)
        self.confirm_password_edit.setPlaceholderText("Repeat the password")
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("New Username:", self.username_edit)
        layout.addRow("Password:", self.password_edit)
        layout.addRow("Confirm Password:", self.confirm_password_edit)

                                        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)                                  
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.username_edit.setFocus()

    def validate_and_accept(self):
        """Validate input before accepting the dialog."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password cannot be empty.")
            return                     

        if password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            self.password_edit.clear()
            self.confirm_password_edit.clear()
            self.password_edit.setFocus()
            return                     

                                                             
        existing_user = db.get_user(username)
        if existing_user:
             QMessageBox.warning(self, "Username Taken", f"The username '{username}' is already taken. Please choose another.")
             self.username_edit.setFocus()
             self.username_edit.selectAll()
             return                     

                                               
        self.accept()

    def get_credentials(self):
        """Returns the validated username and password."""
                                                                                  
        return self.username_edit.text().strip(), self.password_edit.text()

                                   
    @staticmethod
    def getNewUserCredentials(parent=None):
        dialog = RegisterUserDialog(parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return True, dialog.get_credentials()
        return False, (None, None)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setModal(True)                                           

        layout = QFormLayout(self)

        self.username_edit = QLineEdit(self)
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)                      

        layout.addRow("Username:", self.username_edit)
        layout.addRow("Password:", self.password_edit)

                                        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)                         
        button_box.rejected.connect(self.reject)                             

        layout.addWidget(button_box)

        self.username_edit.setFocus()

    def get_credentials(self):
        """Returns the entered username and password."""
        return self.username_edit.text().strip(), self.password_edit.text()

                                                             
    @staticmethod
    def getLoginCredentials(parent=None):
        dialog = LoginDialog(parent)
        result = dialog.exec()                          
        if result == QDialog.DialogCode.Accepted:
            return True, dialog.get_credentials()                                       
        return False, (None, None)                 

class ChemicalApp(QMainWindow):
    line_group_captured = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lab Chemical Management (Ver 2.0)")
        self.setGeometry(200, 200, 400, 300)                           
        self.history_window = None                                              
        self.ngrok_process = None
        self.admin_settings_dialog = None
        self.config = utils.load_config()
        self.line_group_id = utils.get_setting(self.config, 'LINE', 'GroupID', fallback='')
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self.change_password_action = None
        
                                                                  
        db.initialize_database()

                                 
        self.monthly_report_timer = QTimer(self)
        self.monthly_report_timer.setSingleShot(True)
        self.monthly_report_timer.timeout.connect(self.run_monthly_report)

        self.periodic_check_timer = QTimer(self)
        self.periodic_check_timer.setSingleShot(True)
        self.periodic_check_timer.timeout.connect(self.run_periodic_check)

                                            
        self.joke_report_timer = QTimer(self)
        self.joke_report_timer.setSingleShot(True)
        self.joke_report_timer.timeout.connect(self.run_joke_report)
        
                                      
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)                                       
        self.inactivity_timer.setInterval(600 * 1000)                                 
        self.inactivity_timer.timeout.connect(self.auto_logout)                              
                                   

                            
        self.setup_ui()
        self.setup_menu()
        self.line_group_captured.connect(self.update_line_group_ui)
        

                                                   
        self.connect_signals()

                                                    
                                                                         
                                                                            
        central_widget = self.centralWidget()
        if central_widget:                                               
                                                    
            QApplication.instance().installEventFilter(self)
                                                                                            
            central_widget.setMouseTracking(True)
            self.setMouseTracking(True)                        
        
                                           
                                  
        self.name_input.setFocus()
                                            
        self.logout()                                  
                                         
        self.name_input.setFocus()
        
        self.start_ngrok()
        self.initialize_bot_integrations()
        
        self.schedule_next_reports()
        QTimer.singleShot(0, self.check_default_admin_password)
    
    def process_telegram_message(self, message):
        """
        Dispatch an incoming message to the matching command handler.
        """
        text = message.get('text', '').strip()
        chat_id = message['chat']['id']
        parts = text.split()

        if not parts:
            return

        command_start_index = -1
        if parts[0].lower().startswith('/'):
            command_start_index = 0
        elif len(parts) > 1 and parts[1].lower().startswith('/'):
            command_start_index = 1
        
        if command_start_index == -1:
            return

        command_parts = parts[command_start_index:]
        command = command_parts[0].lower()

                           
        if command == '/log':
            self.handle_log_command(command_parts, chat_id)
        elif command == '/checkstock':
            self.handle_checkstock_command(command_parts, chat_id)
        elif command == '/checkuser':
            self.handle_checkuser_command(command_parts, chat_id)
        elif command == '/checkchemical':
            self.handle_checkchemical_command(command_parts, chat_id)
        elif command == '/help':
            self.handle_help_command(chat_id)
        else:
            bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
            utils.send_telegram_message(bot_token, chat_id, f"Unknown command: `{command}`. Type `/help` to see available commands.", parse_mode="Markdown")

    def _command_response(self, message, chat_id=None, parse_mode="Markdown", transport="telegram"):
        """Send a shared command response or return it to another transport."""
        if transport == "line":
            return str(message)
        bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
        utils.send_telegram_message(bot_token, chat_id, message, parse_mode=parse_mode)
        return str(message)

    def process_shared_command(self, text, transport="line", chat_id=None):
        """Dispatch bot commands through the same handlers for every provider."""
        parts = text.strip().split()
        if not parts:
            return ""
        command = parts[0].lower().split('@', 1)[0]
        if command == '/log':
            return self.handle_log_command(parts, chat_id, transport)
        if command == '/checkstock':
            return self.handle_checkstock_command(parts, chat_id, transport)
        if command == '/checkuser':
            return self.handle_checkuser_command(parts, chat_id, transport)
        if command == '/checkchemical':
            return self.handle_checkchemical_command(parts, chat_id, transport)
        if command == '/help':
            return self.handle_help_command(chat_id, transport)
        if not command.startswith('/'):
            return ""
        return self._command_response(
            f"Unknown command: {command}. Type `/help` to see available commands.",
            chat_id, transport=transport)

    def initialize_bot_integrations(self):
        """Start only the bot providers whose credentials are configured."""
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN") or utils.get_setting(
            self.config, 'Telegram', 'BotToken', fallback='')
        telegram_token_from_env = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat_id_from_env = os.getenv("TELEGRAM_CHAT_ID")
        if telegram_token_from_env:
            self.config.set('Telegram', 'BotToken', telegram_token_from_env)
        if telegram_chat_id_from_env:
            self.config.set('Telegram', 'ChatID', telegram_chat_id_from_env)
        line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or utils.get_setting(
            self.config, 'LINE', 'ChannelAccessToken', fallback='')
        line_secret = os.getenv("LINE_CHANNEL_SECRET") or utils.get_setting(
            self.config, 'LINE', 'ChannelSecret', fallback='')

        telegram_configured = bool(
            telegram_token and 'YOUR_BOT_TOKEN_HERE' not in telegram_token
        )
        line_configured = bool(line_token and line_secret)

        if telegram_configured:
            logging.info("Starting Telegram bot integration.")
            threading.Thread(
                target=self.telegram_listener_thread,
                daemon=True,
                name="telegram-listener",
            ).start()

        if line_configured:
            try:
                self.line_server = line_bot.LineBotServer(
                    line_token,
                    line_secret,
                    self.process_line_command,
                    group_command_handler=self.register_line_group,
                    host=os.getenv("LINE_WEBHOOK_HOST", "0.0.0.0"),
                    port=int(os.getenv("LINE_WEBHOOK_PORT", "8080")),
                )
                self.line_server.start()
            except Exception:
                logging.exception("LINE bot initialization failed.")
        elif telegram_configured:
            logging.info("LINE credentials not found; Telegram-only mode enabled.")

        if not telegram_configured and not line_configured:
            logging.warning(
                "WARNING: No bot configurations found. Please set Telegram or LINE credentials."
            )

    def start_ngrok(self):
        """Start the bundled static-domain tunnel and retain its process handle."""
        executable = os.path.join(utils.get_base_path(__file__), 'ngrok.exe')
        if not os.path.isfile(executable):
            logging.info("Ngrok executable not found at %s; skipping tunnel startup.", executable)
            return

        domain = os.getenv('NGROK_DOMAIN') or utils.get_setting(
            self.config, 'Ngrok', 'Domain', fallback='').strip()
        authtoken = os.getenv('NGROK_AUTHTOKEN') or utils.get_secret(
            'Ngrok', 'Authtoken', self.config, fallback='').strip()
        if not domain or not authtoken:
            logging.warning("Ngrok executable found, but NGROK_DOMAIN or NGROK_AUTHTOKEN is missing.")
            return

        command = [
            executable,
            'http',
            '8080',
            f'--domain={domain}',
            f'--authtoken={authtoken}',
        ]
        creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        try:
            self.ngrok_process = subprocess.Popen(
                command,
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logging.info("Ngrok static tunnel started for domain %s.", domain)
        except OSError:
            logging.exception("Could not start Ngrok from %s.", executable)

    def register_line_group(self, group_id):
        """Persist a LINE group ID captured by the /setgroup webhook command."""
        if not group_id:
            return "Could not identify the LINE group."
        try:
            self.config.set('LINE', 'GroupID', group_id)
            with open(utils.CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            self.line_group_id = group_id
            self.line_group_captured.emit(group_id)
            logging.info("LINE group ID registered for automatic alerts.")
            return "Group successfully registered for automatic alerts!"
        except Exception:
            logging.exception("Could not save captured LINE group ID.")
            return "Could not save the LINE group registration."

    def update_line_group_ui(self, group_id):
        """Update an open settings dialog after a webhook captures a group ID."""
        if self.admin_settings_dialog and self.admin_settings_dialog.isVisible():
            self.admin_settings_dialog.line_group_id_edit.setText(group_id)

    def send_line_report(self, message):
        """Push the same report text used by Telegram to the registered LINE group."""
        group_id = os.getenv("LINE_GROUP_ID") or utils.get_setting(
            self.config, 'LINE', 'GroupID', fallback='')
        token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or utils.get_setting(
            self.config, 'LINE', 'ChannelAccessToken', fallback='')
        if group_id and token:
            return line_bot.sendLineAlert(group_id, message, token)
        logging.info("LINE report delivery skipped: no group ID or channel token configured.")
        return False

    def process_line_command(self, text):
        """Process LINE text through the shared Telegram command handlers."""
        response = self.process_shared_command(text, transport="line")
        return line_bot.strip_markdown(response) if response else response
    
    
    def telegram_listener_thread(self):
        """
        Listen continuously for Telegram messages in a dedicated thread.
        """
        logging.info("Telegram listener thread is running.")
        bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
        if not bot_token or 'YOUR_BOT_TOKEN_HERE' in bot_token:
            logging.error("Telegram listener stopped: Bot Token is not configured.")
            return

        url = f"https://api.telegram.org/bot{bot_token}/"
        last_update_id = 0

                                                                       
        try:
            logging.info("Clearing old message queue on startup...")
            params = {'limit': 1, 'offset': -1, 'timeout': 0}
            response = requests.get(url + "getUpdates", params=params, timeout=5)
            if response.status_code == 200:
                updates = response.json().get('result', [])
                if updates:
                    last_update_id = updates[0]['update_id']
                    logging.info(f"Queue cleared. Starting to listen from update_id: {last_update_id + 1}")
        except Exception as e:
            logging.warning(f"Could not clear message queue on startup: {e}")

        while True:
            try:
                params = {'timeout': 30, 'offset': last_update_id + 1, 'allowed_updates': ['message']}
                response = requests.get(url + "getUpdates", params=params, timeout=35)
                response.raise_for_status()

                updates = response.json().get('result', [])
                
                if updates:
                    for update in updates:
                        last_update_id = update['update_id']
                        if 'message' in update and 'text' in update['message']:
                            msg_process_thread = threading.Thread(
                                target=self.process_telegram_message,
                                args=(update['message'],),
                                daemon=True
                            )
                            msg_process_thread.start()

            except requests.exceptions.Timeout:
                                                                                  
                continue
            except requests.exceptions.RequestException as e:
                logging.error(f"Telegram listener network error: {e}. Retrying in 20 seconds...")
                time_module.sleep(20)
            except Exception as e:
                logging.error(f"An unexpected error in Telegram listener: {e}", exc_info=True)
                time_module.sleep(20)
                


    def handle_log_command(self, command_parts, chat_id=None, transport="telegram"):
        """
        Handle the /log command and report low-stock warnings.
        """
        bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')

                                          
        if len(command_parts) < 5 or len(command_parts) % 2 != 1:
            error_msg = ("Invalid syntax. Correct format is:\n"
                         "`/log <User> <Type> <Qty1> <Chem1> [Qty2] [Chem2]...`\n"
                         "Example:\n"
                         "`/log kay takeout 1 DMEM 2 FBS`")
            return self._command_response(error_msg, chat_id, transport=transport)

                                                       
        username_logged = command_parts[1]
        transaction_type_raw = command_parts[2].lower()
        
        if transaction_type_raw not in ['takeout', 'fillin']:
            return self._command_response(f"Error: Invalid type '{command_parts[2]}'. Must be 'takeout' or 'fillin'.", chat_id, transport=transport)

        transaction_type = "TakeOut" if transaction_type_raw == 'takeout' else "FillIn"
            
        user_id = None
        db_user_name = username_logged
        if username_logged.lower() != 'whoknows':
            user_data = db.get_user(username_logged)
            if not user_data:
                return self._command_response(f"Error: User '{username_logged}' not found in the system.", chat_id, transport=transport)
            user_id = user_data[0]
            db_user_name = user_data[1]                     

                                                                  
        entries_to_log = []
        item_parts = command_parts[3:]
        i = 0
        while i < len(item_parts):
            try:
                quantity_str = item_parts[i]
                chem_name = item_parts[i+1]
                
                quantity = float(quantity_str)
                if quantity <= 0:
                    raise ValueError("Quantity must be a positive number.")
                
                chemical_data = db.get_chemical(chem_name)
                if not chemical_data:
                    return self._command_response(f"Error: Chemical '{chem_name}' not found.", chat_id, transport=transport)
                
                if transaction_type == "TakeOut" and chemical_data['current_stock'] < quantity:
                    return self._command_response(f"Error: Insufficient stock for '{chemical_data['name']}'. Remaining: {chemical_data['current_stock']:.2f}, Requested: {quantity}.", chat_id, transport=transport)

                entries_to_log.append({
                    'quantity': quantity,
                    'chemical_id': chemical_data['chemical_id'],
                    'chemical_name_logged': chemical_data['name']
                })
                i += 2
            except (ValueError, IndexError):
                return self._command_response(f"Syntax error in quantity-chemical pair: '{' '.join(item_parts[i:i+2])}'. Please ensure <Quantity> comes before <Chemical>.", chat_id, transport=transport)

                                                  
        if not entries_to_log:
            return self._command_response("Error: No valid items to log.", chat_id, transport=transport)

                                                                 
        logged_items_summary = []
        low_stock_warnings = []                                                   

        for entry in entries_to_log:
            result = db.add_transaction(
                user_id=user_id,
                username_logged=db_user_name,
                chemical_id=entry['chemical_id'],
                chemical_name_logged=entry['chemical_name_logged'],
                transaction_type=transaction_type,
                quantity=entry['quantity'],
                notes=f"Logged via {transport.title()}"
            )
            
            if 'error' in result:
                logging.error(f"Failed to log transaction from {transport} due to DB error: {result['error']}")
                return self._command_response(f"System Error while logging '{entry['chemical_name_logged']}'. Please contact admin. Error: {result['error']}", chat_id, transport=transport)

                                                                       
            if result.get('low_stock'):
                warning_text = (f"  - *{result['chemical_name']}*: "
                                f"Remaining `{result['current_stock']:.2f}`")
                low_stock_warnings.append(warning_text)

            logged_items_summary.append(f"- {entry['quantity']} {entry['chemical_name_logged']}")

                                                               
        confirmation_msg = (f"✅ **Log successful!**\n"
                            f"**User:** {db_user_name}\n"
                            f"**Type:** {transaction_type}\n"
                            f"**Items:**\n" +
                            "\n".join(logged_items_summary))
        
                                                         
        if low_stock_warnings:
            confirmation_msg += "\n\n⚠️ **IMMEDIATE LOW STOCK WARNING!** ⚠️\n"
            confirmation_msg += "\n".join(low_stock_warnings)

        return self._command_response(confirmation_msg, chat_id, transport=transport)
    
    def handle_checkchemical_command(self, command_parts, chat_id=None, transport="telegram"):
        """Handles the /checkchemical command."""
        bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
        if len(command_parts) < 2:
            return self._command_response("Invalid syntax. Usage: `/checkchemical <chemical1> [chemical2]...`", chat_id, transport=transport)

        chemicals_to_check = command_parts[1:]
        response_lines = ["*Chemical Log Report*"]

        for chem_name in chemicals_to_check:
            header, transactions = db.get_chemical_log_since_last_fillin(chem_name)
            
            if not header:
                response_lines.append(f"\n--- 🧪 *{chem_name}* ---\n- Error: Chemical not found.")
                continue

            response_lines.append(f"\n--- 🧪 *{header['name']}* ---")
            
            if header['last_fillin']:
                date_obj = datetime.strptime(header['last_fillin']['timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                response_lines.append(f"- *Cycle started from last fill-in on {formatted_date} by {header['last_fillin']['username_logged']} (Qty: {header['last_fillin']['quantity']})*")
            else:
                response_lines.append("- *No fill-in record found for this chemical. Showing all-time log.*")

            if transactions:
                for t in transactions:
                    ts = datetime.strptime(t['timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')
                                                                                  
                    if t['timestamp'] == (header['last_fillin']['timestamp'] if header['last_fillin'] else None):
                       continue
                    response_lines.append(f"  - `{ts}`: *{t['username_logged']}* {t['transaction_type']} *{t['quantity']}*")
            else:
                 response_lines.append("  - No other activities found since last fill-in.")
        
        full_response = "\n".join(response_lines)
        return self._command_response(full_response, chat_id, transport=transport)

    def handle_checkuser_command(self, command_parts, chat_id=None, transport="telegram"):
        """Handles the /checkuser command."""
        bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
        if len(command_parts) < 3:
            return self._command_response("Invalid syntax. Usage: `/checkuser <user> <chemical1> [chemical2]...` or `/checkuser <user> all`", chat_id, transport=transport)

        target_user = command_parts[1]
        chemicals_to_check_str = command_parts[2:]
        chemicals_to_check = []

        if chemicals_to_check_str[0].lower() == 'all':
            all_chem_details = db.get_all_chemicals_details()
            chemicals_to_check = [chem['name'] for chem in all_chem_details]
        else:
            chemicals_to_check = chemicals_to_check_str

        response_lines = [f"*User Activity Report for '{target_user}'*"]

        for chem_name in chemicals_to_check:
            header, transactions = db.get_user_activity_since_last_fillin(target_user, chem_name)
            
            if not header:
                response_lines.append(f"\n--- 🧪 *{chem_name}* ---\n- Error: Chemical not found.")
                continue
            if 'error' in header and header['error'] == 'User not found':
                 response_lines.append(f"\n- Error: User '{target_user}' not found in database.")
                                                  
                 break

            response_lines.append(f"\n--- 🧪 *{header['name']}* ---")

            if header['last_fillin']:
                date_obj = datetime.strptime(header['last_fillin']['timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                response_lines.append(f"- *Cycle started from last fill-in on {formatted_date} by {header['last_fillin']['username_logged']}*")
            else:
                response_lines.append("- *No fill-in record found for this chemical.*")

            if transactions:
                response_lines.append(f"  *Activities by '{target_user}' since then:*")
                for t in transactions:
                                                                                                     
                    if t['timestamp'] == (header['last_fillin']['timestamp'] if header['last_fillin'] else None):
                       continue
                    ts = datetime.strptime(t['timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')
                    response_lines.append(f"    - `{ts}`: {t['transaction_type']} *{t['quantity']}*")
            else:
                response_lines.append(f"  - No activities found for '{target_user}' in this cycle.")

        full_response = "\n".join(response_lines)
        return self._command_response(full_response, chat_id, transport=transport)
    
    def handle_help_command(self, chat_id=None, transport="telegram"):
        """Sends a help message with all command structures."""
        bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
        help_text = (
            "--- Lab Chemical Bot Commands ---\n\n"
            "**1. Log a transaction:**\n"
            "`/log <user> <type> <qty1> <chem1> [qty2] [chem2]...`\n"
            "- `<user>`: Your registered username or `whoknows`.\n"
            "- `<type>`: `takeout` or `fillin`.\n"
            "- Example: `/log kay takeout 1 DMEM 2 FBS`\n\n"
            
            "**2. Check stock levels:**\n"
            "`/checkstock <chemical1> [chemical2]...` or `/checkstock all`\n"
            "- Example 1: `/checkstock DMEM FBS`\n"
            "- Example 2: `/checkstock all`\n\n"
            
            "**3. Check a user's activity:**\n"
            "`/checkuser <user> <chemical1> [chemical2]...` or `/checkuser <user> all`\n"
            "- Shows user's log since the last fill-in of the chemical.\n"
            "- Example: `/checkuser kay DMEM`\n\n"
            
            "**4. Check a chemical's log:**\n"
            "`/checkchemical <chemical1> [chemical2]...`\n"
            "- Shows all logs for a chemical since its last fill-in.\n"
            "- Example: `/checkchemical FBS`\n\n"
            
            "**5. Get this help message:**\n"
            "`/help`"
        )
        return self._command_response(help_text, chat_id, transport=transport)

    def handle_checkstock_command(self, command_parts, chat_id=None, transport="telegram"):
        """Handles the /checkstock command."""
        bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
        
        if len(command_parts) < 2:
            return self._command_response("Invalid syntax. Usage: `/checkstock <chemical_name>` or `/checkstock all`", chat_id, transport=transport)

        chemicals_to_check = []
        if command_parts[1].lower() == 'all':
            all_chem_details = db.get_all_chemicals_details()                    
            chemicals_to_check = [chem['name'] for chem in all_chem_details]
        else:
            chemicals_to_check = command_parts[1:]

        if not chemicals_to_check:
             return self._command_response("Please specify which chemical to check or use 'all'.", chat_id, transport=transport)

        response_lines = ["*Stock Level & Last Fill-in Report*"]
        for chem_name in chemicals_to_check:
            chem_info = db.get_stock_and_last_fillin(chem_name)
            
            if not chem_info:
                response_lines.append(f"\n--- 🧪 {chem_name} ---\n- Error: Chemical not found.")
                continue

            line = f"\n--- 🧪 *{chem_info['name']}* ---"
            
                                                          
            if chem_info['last_fillin_date']:
                                             
                date_obj = datetime.strptime(chem_info['last_fillin_date'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%Y-%m-%d')
                line += (f"\n- *Last Fill-in:* {formatted_date} by *{chem_info['last_fillin_by']}* "
                         f"(Qty: *{chem_info['last_fillin_qty']}*)")
            else:
                line += "\n- *Last Fill-in:* No fill-in record found."

            line += f"\n- *Current Stock:* {chem_info['current_stock']:.2f}"
            response_lines.append(line)
        
        full_response = "\n".join(response_lines)
        return self._command_response(full_response, chat_id, transport=transport)
    
    def reset_inactivity_timer(self):
        """Restart the inactivity timer."""
        if self.current_user_info:                            
            self.inactivity_timer.start()

    def stop_inactivity_timer(self):
        """Stop the inactivity timer."""
        self.inactivity_timer.stop()

    def auto_logout(self):
        """Log out the user and notify them when inactivity expires."""
        logging.info("User inactive for 2 minutes. Auto-logging out.")
        self.statusBar.showMessage("Tự động đăng xuất do không hoạt động.", 5000)
        self.logout()
                                       
        QMessageBox.information(self, "Đã đăng xuất", "Bạn đã được tự động đăng xuất do không hoạt động trong 2 phút.")
    
    def eventFilter(self, source, event):
        """
        Reset inactivity tracking and restore input focus for application events.
        """
                                            
                                              
        if event.type() in [QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel]:
            self.reset_inactivity_timer()                                  

                                            
        if event.type() == QEvent.Type.MouseButtonPress:
            widget_at_click = QApplication.widgetAt(event.globalPosition().toPoint())
            if widget_at_click == self.centralWidget() or isinstance(widget_at_click, QLabel):
                self.name_input.setFocus()
        elif event.type() == QEvent.Type.ActivationChange:
             if self.isActiveWindow():
                  QTimer.singleShot(50, lambda: self.name_input.setFocus())

                                                                           
        return super().eventFilter(source, event)
    
    
    def run_monthly_report(self, force_run=False):
        """Generates and sends the monthly chemical usage summary report."""
        logging.info(f"Attempting to run monthly report generation... (Forced: {force_run})")
        now = datetime.now()

                                                            
        report_dt = now - timedelta(days=now.day)                                   
        target_year = report_dt.year
        target_month = report_dt.month
        report_month_str = f"{target_year}-{target_month:02d}"                 

        last_sent_str = utils.get_setting(self.config, 'Schedule', 'LastMonthlyReportSent', fallback='2000-01')

                                                                                      
        if not force_run and last_sent_str == report_month_str:
             logging.info(f"Monthly report for {report_month_str} already sent. Skipping.")
                                             
             QTimer.singleShot(5000, self.schedule_next_reports)
             return

        try:
            logging.info(f"Generating monthly summary for {target_year}-{target_month:02d}")
            summary_data = db.get_monthly_usage_summary(target_year, target_month)             

                                     
            month_name_en = calendar.month_name[target_month]
            report_message = f"📊 <b>Monthly Chemical Usage Summary</b> 📊\n"
            report_message += f"<b>Period: {month_name_en} {target_year}</b>\n"
            report_message += "------------------------------------\n\n"

            if not summary_data:
                report_message += "<i>No recorded 'FillIn' or 'TakeOut' activity for this month.</i>"
            else:
                for item in summary_data:
                     chem_name = item['chemical_name_logged']
                     fillin = item['total_fillin']
                     takeout = item['total_takeout']
                     report_message += f"🧪 <b>{chem_name}</b>:\n"
                     if fillin > 0:
                         report_message += f"    - Filled in: <code>{fillin:.2f}</code> 📈\n"
                     if takeout > 0:
                         report_message += f"    - Taken out: <code>{takeout:.2f}</code> 📉\n"
                     if fillin == 0 and takeout == 0:
                         report_message += f"    - <i>No FillIn/TakeOut activity recorded.</i>\n"
                                                        
                     report_message += "\n"
                                     

                                          
            if report_message:
                bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
                chat_id = utils.get_setting(self.config, 'Telegram', 'ChatID')
                if bot_token and chat_id and 'YOUR_BOT_TOKEN_HERE' not in bot_token:
                    send_success = utils.send_telegram_message(bot_token, chat_id, report_message.strip())
                    if send_success:
                         logging.info(f"Sent monthly report for {report_month_str} to Telegram.")
                                                                                       
                         if not force_run:
                              utils.save_setting(self.config, 'Schedule', 'LastMonthlyReportSent', report_month_str)
                    else:
                         logging.error("Failed to send monthly report to Telegram.")
                else:
                     logging.warning("Telegram not configured. Monthly report generated but not sent.")
                                                                                      
                     if not force_run:
                          utils.save_setting(self.config, 'Schedule', 'LastMonthlyReportSent', report_month_str)
                self.send_line_report(report_message.strip())
            else:
                 logging.info("Monthly report generated but was empty, not sending.")
                                                                  
                 if not force_run:
                      utils.save_setting(self.config, 'Schedule', 'LastMonthlyReportSent', report_month_str)

        except Exception as e:
            logging.error(f"Error generating/sending monthly report for {report_month_str}: {e}", exc_info=True)

        finally:
                                                           
             if not force_run:
                                                                                             
                 QTimer.singleShot(15000, self.schedule_next_reports)          

                                                                                
                                   
                                                                                
    def run_joke_report(self, force_run=False):
        """Generates and sends the end-of-month user activity ('joke') report."""
        logging.info(f"Attempting to run joke report generation... (Forced: {force_run})")
        now = datetime.now()
        target_month = now.month
        target_year = now.year
        current_month_str = now.strftime('%Y-%m')                 

        last_sent_str = utils.get_setting(self.config, 'Schedule', 'LastJokeReportSent', fallback='2000-01')

                                                                                 
        if not force_run and last_sent_str == current_month_str:
             logging.info(f"Joke report for {current_month_str} already sent. Skipping.")
             QTimer.singleShot(5000, self.schedule_next_reports)               
             return

        try:
            logging.info(f"Generating joke report for {target_year}-{target_month:02d}")
            activity_data = db.get_user_activity_summary(target_year, target_month)             
            users = activity_data.get('users', {})
            whoknows = activity_data.get('whoknows', {})
            stats = activity_data.get('stats', {})

                                                                     
            month_name_en = calendar.month_name[target_month]
            report_message = f"🏆 <b>Lab Performance Report - {month_name_en} {target_year}</b> 🏆\n"
            report_message += "------------------------------------\n\n"

            if not users:
                 report_message += "👻 It seems everyone was on vacation... No user activity recorded this month (excluding Whoknows).\n"
            else:
                                                  
                max_take_name, max_take_val = stats.get('max_takeout', ('N/A', 0.0))
                if max_take_val > 0:
                    report_message += f"🥇 <b>'Chemical-Destroyer' Award</b> 🥇\nGoes to: <b>{max_take_name}</b> ({max_take_val:.2f} units taken out)\n\n"
                else:
                     report_message += "💨 Everyone kept their hands off the chemicals this month! (No takeouts recorded)\n\n"

                                               
                min_take_name, min_take_val = stats.get('min_takeout', ('N/A', 0.0))
                                                                                                             
                if min_take_val > 0 and (min_take_name != max_take_name or len(users) == 1) :
                    report_message += f"🐢 <b>'Lab-Laziest' Award</b> 🐢\nTo: <b>{min_take_name}</b> (only {min_take_val:.2f} units taken out)\n\n"
                elif len(users) == 1 and max_take_val > 0:                                  
                     report_message += "*(Only one active user, so they get all the awards!)*\n\n"

                                              
                max_fill_name, max_fill_val = stats.get('max_fillin', ('N/A', 0.0))
                if max_fill_val > 0:
                     report_message += f"✨ <b>'Stock Guardian' Award</b> ✨\nBig thanks to: <b>{max_fill_name}</b> ({max_fill_val:.2f} units filled in)\n\n"
                else:
                     report_message += "📦 The stock fairies must be on strike... No refills recorded this month.\n\n"

                                                 
                min_fill_name, min_fill_val = stats.get('min_fillin', ('N/A', 0.0))
                if min_fill_val > 0 and (min_fill_name != max_fill_name or len(users) == 1):
                     report_message += f"💧 <b>'Just Enough' Refiller</b> 💧\nTo: <b>{min_fill_name}</b> ({min_fill_val:.2f} units filled in)\n\n"
                elif len(users) == 1 and max_fill_val > 0:
                      pass                                      

                              
            whoknows_takeout = whoknows.get('takeout', 0.0)
            whoknows_fillin = whoknows.get('fillin', 0.0)
            if whoknows_takeout > 0 or whoknows_fillin > 0:
                report_message += f"❓ <b>The 'Whoknows' Zone</b> ❓\n"
                if whoknows_takeout > 0:
                    report_message += f"   - Takeout: <code>{whoknows_takeout:.2f}</code> units mysteriously vanished...\n"
                if whoknows_fillin > 0:
                    report_message += f"   - Fillin: <code>{whoknows_fillin:.2f}</code> units magically appeared...\n"
                report_message += "\n"
            elif users:                                            
                report_message += "✅ Excellent accountability! No 'Whoknows' activity found!\n\n"

            report_message += "------------------------------------"
                                     

                          
            bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
            chat_id = utils.get_setting(self.config, 'Telegram', 'ChatID')
            if bot_token and chat_id and 'YOUR_BOT_TOKEN_HERE' not in bot_token:
                send_success = utils.send_telegram_message(bot_token, chat_id, report_message.strip())
                if send_success:
                    logging.info(f"Sent joke report for {current_month_str} to Telegram.")
                    if not force_run:
                        utils.save_setting(self.config, 'Schedule', 'LastJokeReportSent', current_month_str)
                else:
                    logging.error("Failed to send joke report to Telegram.")
            else:
                 logging.warning("Telegram not configured. Joke report generated but not sent.")
                 if not force_run:
                      utils.save_setting(self.config, 'Schedule', 'LastJokeReportSent', current_month_str)                             
            self.send_line_report(report_message.strip())

        except Exception as e:
            logging.error(f"Error generating/sending joke report for {current_month_str}: {e}", exc_info=True)

        finally:
                                                           
             if not force_run:
                  QTimer.singleShot(15000, self.schedule_next_reports)          

                                                                                
                                       
                                                                                
    def run_periodic_check(self, force_run=False):
        """Runs the periodic check (e.g., for low stock) and sends report if needed."""
        logging.info(f"Attempting to run periodic check... (Forced: {force_run})")
        now = datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        last_sent_str = utils.get_setting(self.config, 'Schedule', 'LastPeriodicCheckSent', fallback='2000-01-01 00:00:00')

                                                         
        if not force_run:
            try:
                 last_sent_dt = datetime.strptime(last_sent_str, '%Y-%m-%d %H:%M:%S')
                                                                              
                 if (now - last_sent_dt) < timedelta(minutes=10):
                      logging.info(f"Periodic check ran too recently ({last_sent_dt}). Skipping.")
                      QTimer.singleShot(60000, self.schedule_next_reports)                     
                      return
            except ValueError:
                 logging.warning(f"Could not parse LastPeriodicCheckSent: {last_sent_str}")
                                               

        report_message = None                  
        try:
                                                           
            logging.info("Performing low stock check for periodic report.")
            low_stock_list = db.get_low_stock_chemicals()             

            if low_stock_list:
                report_message = "🚨 <b>Low Stock Report</b> 🚨\n"
                report_message += f"<i>Checked at: {now.strftime('%Y-%m-%d %H:%M')}</i>\n\n"
                for item in low_stock_list:
                     report_message += f"- <b>{item['name']}</b>: Remaining <code>{item['current_stock']:.2f}</code> (Threshold: {item['threshold']:.2f})\n"
                report_message += "\nPlease check and refill. Hurry Up!!!"
                logging.info(f"Found {len(low_stock_list)} chemicals below threshold.")
            else:
                logging.info("Periodic check: No chemicals below threshold.")
                                                               
                                                                                                                                             

                                         
            if report_message:
                bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
                chat_id = utils.get_setting(self.config, 'Telegram', 'ChatID')
                if bot_token and chat_id and 'YOUR_BOT_TOKEN_HERE' not in bot_token:
                                                                        
                    utils.send_telegram_in_thread(bot_token, chat_id, report_message)
                    logging.info("Attempting to send periodic report to Telegram.")
                                                                                     
                    if not force_run:
                        utils.save_setting(self.config, 'Schedule', 'LastPeriodicCheckSent', now_str)
                else:
                    logging.warning("Telegram not configured. Periodic report generated but not sent.")
                                                                         
                    if not force_run:
                       utils.save_setting(self.config, 'Schedule', 'LastPeriodicCheckSent', now_str)
                self.send_line_report(report_message)
            else:
                                                                                     
                 if not force_run:
                      utils.save_setting(self.config, 'Schedule', 'LastPeriodicCheckSent', now_str)

        except Exception as e:
             logging.error(f"Error running/sending periodic check: {e}", exc_info=True)

        finally:
                                                           
             if not force_run:
                  QTimer.singleShot(15000, self.schedule_next_reports)          
    
    def schedule_next_reports(self):
        """Calculates next run times and sets single-shot timers."""
        now = datetime.now()
        logging.info(f"Scheduling checks starting at: {now}")

                                             
        self.monthly_report_timer.stop()
        self.joke_report_timer.stop()
        self.periodic_check_timer.stop()

                                         
        try:
            monthly_enabled = utils.get_setting(self.config, 'Schedule', 'MonthlyReportEnabled', fallback='True').lower() == 'true'
            if monthly_enabled:
                day_to_run_m = int(utils.get_setting(self.config, 'Schedule', 'MonthlyReportDay', fallback='1'))
                hour_to_run_m = int(utils.get_setting(self.config, 'Schedule', 'MonthlyReportHour', fallback='8'))
                last_sent_str_m = utils.get_setting(self.config, 'Schedule', 'LastMonthlyReportSent', fallback='2000-01')          

                                                              
                report_month_dt = now - timedelta(days=now.day)                      
                report_month_str = report_month_dt.strftime('%Y-%m')

                                                                                 
                                     
                day_to_run_m = min(day_to_run_m, calendar.monthrange(now.year, now.month)[1])
                target_run_time_m = datetime(now.year, now.month, day_to_run_m, hour_to_run_m, 0, 0)
                try:                                                     
                    day_to_run_m_this_month = min(day_to_run_m, calendar.monthrange(now.year, now.month)[1])
                    target_run_time_m = datetime(now.year, now.month, day_to_run_m_this_month, hour_to_run_m, 0, 0)
                except ValueError:
                    logging.error(f"Invalid day '{day_to_run_m}' for current month. Skipping monthly schedule.")
                    target_run_time_m = None
                
                if target_run_time_m:
                                                                        
                    if last_sent_str_m == report_month_str:
                        next_schedule_month = now.replace(day=1) + timedelta(days=32)                         
                        day_to_run_m = min(day_to_run_m, calendar.monthrange(next_schedule_month.year, next_schedule_month.month)[1])
                        target_run_time_m = datetime(next_schedule_month.year, next_schedule_month.month, day_to_run_m, hour_to_run_m, 0, 0)

                                                                 
                    if now >= target_run_time_m and last_sent_str_m != report_month_str:
                        logging.info(f"Monthly report for {report_month_str} is due (Last sent: {last_sent_str_m}). Triggering run.")
                        QTimer.singleShot(100, self.run_monthly_report)
                    else:
                        delay_seconds_m = (target_run_time_m - now).total_seconds()
                        if delay_seconds_m > 0:
                                                                
                            delay_ms = max(1000, int(delay_seconds_m * 1000))
                            capped_delay_ms_m = min(delay_ms, MAX_TIMER_INTERVAL)                   
                            self.monthly_report_timer.setInterval(capped_delay_ms_m)                           
                            self.monthly_report_timer.start()
                            logging.info(f"Next monthly report target: {target_run_time_m}. Timer set for {capped_delay_ms_m / 1000.0:.0f} seconds (may be capped).")
                                                                  
                        elif delay_seconds_m <= 0 and last_sent_str_m == report_month_str:
                            logging.info(f"Monthly report for {report_month_str} already sent. Next schedule calculated for {target_run_time_m}.")


        except Exception as e:
            logging.error(f"Error scheduling monthly report: {e}", exc_info=True)


                                      
        try:
            joke_enabled = utils.get_setting(self.config, 'Schedule', 'JokeReportEnabled', fallback='True').lower() == 'true'
            if joke_enabled:
                hour_to_run_j = int(utils.get_setting(self.config, 'Schedule', 'JokeReportHour', fallback='22'))
                last_sent_str_j = utils.get_setting(self.config, 'Schedule', 'LastJokeReportSent', fallback='2000-01')          
                current_month_str = now.strftime('%Y-%m')

                                               
                last_day_of_current_month = calendar.monthrange(now.year, now.month)[1]
                target_run_time_j = datetime(now.year, now.month, last_day_of_current_month, hour_to_run_j, 0, 0)

                                                                                          
                next_month_dt = now.replace(day=1) + timedelta(days=32)                         
                last_day_next_month = calendar.monthrange(next_month_dt.year, next_month_dt.month)[1]
                next_schedule_time_j = datetime(next_month_dt.year, next_month_dt.month, last_day_next_month, hour_to_run_j, 0, 0)

                                                        
                if last_sent_str_j == current_month_str:
                                                              
                    final_target_time_j = next_schedule_time_j
                    logging.info(f"Joke report for {current_month_str} already sent.")
                elif now >= target_run_time_j:
                                                                              
                     logging.info(f"Joke report for {current_month_str} is due (Last sent: {last_sent_str_j}). Triggering run.")
                     QTimer.singleShot(200, self.run_joke_report)            
                                                                                             
                else:
                                                                                     
                    final_target_time_j = target_run_time_j

                if final_target_time_j:
                    delay_seconds_j = (final_target_time_j - now).total_seconds()
                    if delay_seconds_j > 0:
                                                            
                        delay_ms = max(1000, int(delay_seconds_j * 1000))
                        capped_delay_ms_j = min(delay_ms, MAX_TIMER_INTERVAL)                   
                        self.joke_report_timer.setInterval(capped_delay_ms_j)                           
                        self.joke_report_timer.start()
                        logging.info(f"Next joke report target: {final_target_time_j}. Timer set for {capped_delay_ms_j / 1000.0:.0f} seconds (may be capped).")

        except Exception as e:
             logging.error(f"Error scheduling joke report: {e}", exc_info=True)


                                         
        try:
            periodic_enabled = utils.get_setting(self.config, 'Schedule', 'PeriodicCheckEnabled', fallback='True').lower() == 'true'
            if periodic_enabled:
                days_interval_p = int(utils.get_setting(self.config, 'Schedule', 'PeriodicCheckDays', fallback='2'))
                hour_to_run_p = int(utils.get_setting(self.config, 'Schedule', 'PeriodicCheckHour', fallback='22'))
                last_sent_str_p = utils.get_setting(self.config, 'Schedule', 'LastPeriodicCheckSent', fallback='2000-01-01 00:00:00')

                try:
                    last_sent_dt = datetime.strptime(last_sent_str_p, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                     logging.warning(f"Invalid LastPeriodicCheckSent format '{last_sent_str_p}', using default.")
                     last_sent_dt = datetime(2000, 1, 1)

                                               
                next_run_time_p = last_sent_dt + timedelta(days=days_interval_p)
                                                    
                next_run_time_p = next_run_time_p.replace(hour=hour_to_run_p, minute=0, second=0, microsecond=0)

                                                                               
                if now >= next_run_time_p:
                    logging.info(f"Periodic check due (Last sent: {last_sent_dt}). Triggering run.")
                    QTimer.singleShot(300, self.run_periodic_check)            
                else:
                    delay_seconds_p = (next_run_time_p - now).total_seconds()
                    if delay_seconds_p > 0:
                        delay_ms_p = max(1000, int(delay_seconds_p * 1000))
                        self.periodic_check_timer.setInterval(delay_ms_p)
                        self.periodic_check_timer.start()
                        logging.info(f"Next periodic check scheduled at {next_run_time_p} (in {delay_seconds_p:.0f} seconds)")

        except Exception as e:
             logging.error(f"Error scheduling periodic check: {e}", exc_info=True)
    
    def check_default_admin_password(self):
        """Checks if the default admin password needs changing."""
        try:
            default_changed = utils.get_setting(self.config, 'Admin', 'DefaultPasswordChanged', fallback='False').lower() == 'true'
            if not default_changed:
                                                                                       
                admin_user = db.get_user('admin')
                if admin_user and db.check_password(admin_user[2], 'admin'):
                     QMessageBox.warning(self, "Security Warning",
                                         "The default admin password ('admin') is still in use.\n"
                                         "Please log in as admin and use 'Manage Users' to change the password immediately.")
        except Exception as e:
             logging.error(f"Error checking default admin password status: {e}", exc_info=True)
    
    def setup_menu(self):
        """Sets up the main menu bar."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")            

        self.login_action = QAction("&Login", self)
        self.logout_action = QAction("&Logout", self)
        self.register_action = QAction("&Register New User", self)
        self.change_password_action = QAction("&Change Password", self)
        self.logout_action.setEnabled(False)                     
        exit_action = QAction("&Exit", self)

        file_menu.addAction(self.register_action)
        file_menu.addSeparator()
        file_menu.addAction(self.login_action)
        file_menu.addAction(self.logout_action)
        file_menu.addAction(self.change_password_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        admin_menu = menu_bar.addMenu("&Admin")                  
        self.manage_users_action = QAction("Manage &Users", self)
        self.manage_chemicals_action = QAction("Manage &Chemicals", self)
        self.admin_settings_action = QAction("Admin &Settings / Manual Reports", self) 
        self.import_action = QAction("&Import from Excel", self)
        self.backup_db_action = QAction("&Backup Database", self) 
        self.restore_db_action = QAction("&Restore Database...", self)
        
        admin_menu.addSeparator()
        admin_menu.addAction(self.backup_db_action)
        admin_menu.addAction(self.restore_db_action)
        admin_menu.addSeparator()
        admin_menu.addAction(self.import_action)
        admin_menu.addSeparator()
        admin_menu.addAction(self.manage_users_action)
        admin_menu.addAction(self.manage_chemicals_action)
        admin_menu.addAction(self.admin_settings_action)

                                                                    
        admin_menu.setEnabled(False)                         

                                       
        self.admin_menu = admin_menu
        self.admin_menu.setEnabled(False)
        
                                
        help_menu = menu_bar.addMenu("&Help")
        self.about_action = QAction("&About / Tutorial", self)
        self.rules_action = QAction("Lab's &Rules", self)
        help_menu.addAction(self.about_action)
        help_menu.addAction(self.rules_action)
                               
        

                         
        exit_action.triggered.connect(self.close)
        self.login_action.triggered.connect(self.show_login_dialog)
        self.logout_action.triggered.connect(self.logout)
        self.register_action.triggered.connect(self.show_register_dialog)
        self.change_password_action.triggered.connect(self.show_change_password_dialog)
        self.about_action.triggered.connect(self.show_about_dialog)                         
        self.rules_action.triggered.connect(self.show_rules_dialog)
        
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

                         
        self.title_label = QLabel("Ma Lab - Chemical Manager")
        title_font = QFont("Brush Script MT", 28)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)
        main_layout.addSpacing(10)

                                   
        form_layout = QFormLayout()

                              
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Scan or type user name")
        form_layout.addRow("User Name:", self.name_input)

        self.chemical_input = QLineEdit()
        self.chemical_input.setPlaceholderText("Scan or type chemical name")
        form_layout.addRow("Chemical:", self.chemical_input)

        self.number_input = QLineEdit()
        self.number_input.setValidator(QDoubleValidator(0.01, 999999.99, 2))
        self.number_input.setPlaceholderText("Enter quantity")
        form_layout.addRow("Quantity:", self.number_input)

        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Blank = TakeOut, type 'FillIn'")
        form_layout.addRow("Type (FillIn/TakeOut):", self.type_input)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()                     

                                                        
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit Entry")
        self.history_button = QPushButton("View History")
                                                                                                
                                                               
                                                                                 

        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.history_button)
        main_layout.addLayout(button_layout)

                            
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready", 3000)
    
    def show_about_dialog(self):
        """Shows the About/Tutorial dialog."""
                                       
        dialog = AboutDialog(self)
        dialog.exec()                  

    def show_rules_dialog(self):
        """Shows the dedicated lab rules dialog."""
        dialog = RuleDialog(self)
        dialog.exec()
    
    def show_register_dialog(self):
        """Shows the registration dialog and handles user creation."""
        accepted, (username, password) = RegisterUserDialog.getNewUserCredentials(self)

        if accepted:                                            
            success, message = db.add_user(username, password, is_admin=0)                               
            if success:
                self.show_info_message("Registration Successful", f"User '{username}' created successfully.")
                                                                                   
                self.load_combobox_data()                                     
            else:
                self.show_error_message("Registration Failed", f"Could not create user: {message}")
    
    def show_change_password_dialog(self):
        """Shows the dialog for the logged-in user to change their password."""
        if not self.current_user_info:
             QMessageBox.warning(self, "Not Logged In", "You must be logged in to change your password.")
             return

        username = self.current_user_info['username']
        user_id = self.current_user_info['user_id']

        dialog = ChangePasswordDialog(username, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            new_password = dialog.get_new_password()
            success, message = db.update_user_password(user_id, new_password)
            if success:
                 QMessageBox.information(self, "Success", message)
                                                                     
                 if username.lower() == 'admin' and new_password != 'admin':
                      try:
                                                    
                          utils.save_setting(self.config, 'Admin', 'DefaultPasswordChanged', 'True')
                          logging.info("Admin has changed the default password. Flag updated in settings.ini.")
                      except Exception as e:
                           logging.error(f"Failed to update DefaultPasswordChanged flag in settings: {e}")
                                                                             
                                
            else:
                 QMessageBox.critical(self, "Error", f"Failed to update password: {message}")
    
    
    def update_admin_ui(self):
        """Shows or hides/enables/disables controls based on login status and admin rights."""
                                                      
        is_logged_in = bool(self.current_user_info)
        is_admin = False
        if is_logged_in:
            is_admin = bool(self.current_user_info.get('is_admin', False))

        logging.info(f"Updating UI: Logged In={is_logged_in}, Is Admin={is_admin}")        

                                                        
                                                     
        if hasattr(self, 'manage_users_button'):                       
             self.manage_users_button.setVisible(is_admin)
        if hasattr(self, 'manage_chemicals_button'):
             self.manage_chemicals_button.setVisible(is_admin)
        if hasattr(self, 'import_button'):
                                                                              
             self.import_button.setVisible(is_admin)

                                                              
                           
        if hasattr(self, 'login_action'):
            self.login_action.setEnabled(not is_logged_in)
        if hasattr(self, 'logout_action'):
            self.logout_action.setEnabled(is_logged_in)
        if hasattr(self, 'change_password_action'):
            self.change_password_action.setEnabled(is_logged_in)                       

                                                     
        if hasattr(self, 'admin_menu'):
            self.admin_menu.setEnabled(is_admin)

                                     
        if is_logged_in:
            username = self.current_user_info.get('username', 'Unknown')
            status_text = f"Logged in as: {username}"
            if is_admin:
                status_text += " (Admin)"
            self.statusBar.showMessage(status_text)
        else:
                                                                      
            self.statusBar.clearMessage()
            self.statusBar.showMessage("Ready", 3000)                       


                                                                                
                                                                       
        if hasattr(self, 'history_window') and self.history_window and self.history_window.isVisible():
                                                                 
             self.history_window.update_admin_controls(is_logged_in, is_admin)
    
    def connect_signals(self):
        """Connect signals to their corresponding slots."""
                              
        self.name_input.returnPressed.connect(self.chemical_input.setFocus)
        self.chemical_input.returnPressed.connect(self.number_input.setFocus)
        self.number_input.returnPressed.connect(self.type_input.setFocus)
                                                 
        self.type_input.returnPressed.connect(self.submit_data)

                       
        self.submit_button.clicked.connect(self.submit_data)
        self.history_button.clicked.connect(self.show_history)
                                                             
        
                                                                            
                                                                                    
                               
        if hasattr(self, 'import_action'): self.import_action.triggered.connect(self.import_data)                               
        if hasattr(self, 'manage_users_action'): self.manage_users_action.triggered.connect(self.show_user_management)
        if hasattr(self, 'manage_chemicals_action'): self.manage_chemicals_action.triggered.connect(self.show_chemical_management)
        if hasattr(self, 'admin_settings_action'): self.admin_settings_action.triggered.connect(self.show_admin_settings)
        if hasattr(self, 'backup_db_action'): self.backup_db_action.triggered.connect(self.backup_database)
                                        
        if hasattr(self, 'restore_db_action'): self.restore_db_action.triggered.connect(self.restore_database)
    
    def restore_database(self):
        """Restores the database from a backup file."""
                            
        if not self.current_user_info:
            self.show_error_message("Permission Denied", "Please log in as an administrator before restoring the database.")
            return
        if not self.current_user_info.get('is_admin'):
            self.show_error_message("Permission Denied", "The logged-in account is not an administrator.")
            return

        target_db_path = db.DATABASE_FILE

                                 
        reply1 = QMessageBox.critical(self, 'Confirm Restore',
                                    f"<b>EXTREME WARNING!</b><br><br>"
                                    f"This will <b>COMPLETELY OVERWRITE</b> the current database ({os.path.basename(target_db_path)}) "
                                    f"with the selected backup file.<br><br>"
                                    f"<b>ALL CURRENT DATA WILL BE LOST AND CANNOT BE RECOVERED.</b><br><br>"
                                    f"Are you absolutely sure you want to proceed?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)

        if reply1 == QMessageBox.StandardButton.No:
            return

                                     
        options = QFileDialog.Option.ReadOnly                                                    
        backup_path, _ = QFileDialog.getOpenFileName(self,
                                                    "Select Database Backup File to Restore From",
                                                    "",                  
                                                    "Backup Files (*.bak *.db);;All Files (*)",
                                                    options=options)

        if not backup_path or not os.path.exists(backup_path):
            if backup_path:
                self.show_error_message("Error", f"Backup file not found: {backup_path}")
            return

                                             
        reply2 = QMessageBox.warning(self, 'Final Confirmation',
                                    f"You are about to replace the current database with:<br>"
                                    f"<i>{os.path.basename(backup_path)}</i><br><br>"
                                    f"<b>This action CANNOT BE UNDONE.</b><br><br>Continue with Restore?",
                                                           
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                                                               
                                    QMessageBox.StandardButton.Cancel)

                                                   
        if reply2 == QMessageBox.StandardButton.Yes:
                                  
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                                                                     

                                                       
                shutil.copy2(backup_path, target_db_path)
                logging.info(f"Database restored from '{backup_path}' by UserID {self.current_user_info['user_id']}")
                              
                db.log_audit_event(self.current_user_info['user_id'], 'Restore Database', target_db_path, None, f"Database restored from {os.path.basename(backup_path)}")

                                                    
                QMessageBox.information(self, "Restore Successful",
                                        "Database successfully restored.\n\n"
                                        "The application MUST be restarted now for changes to take effect.")
                self.close()                

            except Exception as e:
                logging.error(f"Database restore failed: {e}", exc_info=True)
                self.show_error_message("Restore Failed", f"Could not restore database:\n{e}")
            finally:
                QApplication.restoreOverrideCursor()
        else:
            logging.info("Database restore cancelled by user at final confirmation.")
    
    
    def backup_database(self):
        """Performs a backup of the SQLite database file."""
                            
        if not self.current_user_info or not self.current_user_info.get('is_admin'):
            self.show_error_message("Permission Denied", "Admin privileges required for database backup.")
            return

        source_db_path = db.DATABASE_FILE                                    
        if not os.path.exists(source_db_path):
            self.show_error_message("Error", f"Database file not found at: {source_db_path}")
            return

                                                   
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_backup_name = f"lab_chemicals_backup_{timestamp}.db.bak"

                                 
        options = QFileDialog.Option(0)
        backup_path, _ = QFileDialog.getSaveFileName(self,
                                                    "Save Database Backup As...",
                                                    default_backup_name,
                                                    "Backup Files (*.bak);;All Files (*)",
                                                    options=options)

        if backup_path:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                shutil.copy2(source_db_path, backup_path)                         
                logging.info(f"Database backed up to '{backup_path}' by UserID {self.current_user_info['user_id']}")
                                  
                db.log_audit_event(self.current_user_info['user_id'], 'Backup Database', source_db_path, None, f"Database backed up to {os.path.basename(backup_path)}")
                self.show_info_message("Backup Successful", f"Database successfully backed up to:\n{backup_path}")
            except Exception as e:
                logging.error(f"Database backup failed: {e}", exc_info=True)
                self.show_error_message("Backup Failed", f"Could not create backup:\n{e}")
            finally:
                QApplication.restoreOverrideCursor()
    
    def show_user_management(self):
        """Shows the user management dialog (admin only)."""
        if self.current_user_info and self.current_user_info.get('is_admin'):
            dialog = UserManagementDialog(self)
            dialog.exec()
                                                                             
            self.load_combobox_data()
        else:
            self.show_error_message("Permission Denied", "You need admin privileges to manage users.")
            
    def show_admin_settings(self):
        """Shows the admin settings dialog."""
        if self.current_user_info and self.current_user_info.get('is_admin'):
            self.admin_settings_dialog = AdminSettingsDialog(self)
            result = self.admin_settings_dialog.exec()            
            self.admin_settings_dialog = None

            if result == QDialog.DialogCode.Accepted:                             
                logging.info("Admin settings potentially changed. Reloading config and rescheduling reports.")
                                                 
                self.config = utils.load_config()
                                                                  
                self.monthly_report_timer.stop()
                self.joke_report_timer.stop()
                self.periodic_check_timer.stop()
                self.schedule_next_reports()                                   
        else:
                                                     
            logging.info("Admin settings dialog closed without saving.")
            
    def show_chemical_management(self):
        """Shows the chemical management dialog (admin only)."""
        if self.current_user_info and self.current_user_info.get('is_admin'):
                                    
            dialog = ChemicalManagementDialog(self)
            dialog.exec()               
                                                                              
            self.load_combobox_data()
        else:
            self.show_error_message("Permission Denied", "You need admin privileges to manage chemicals.")
    
    def show_login_dialog(self):
        """Shows the login dialog and handles authentication."""
        accepted, (username, password) = LoginDialog.getLoginCredentials(self)

        if accepted and username and password:
            verified_user = db.verify_user(username, password)
            if verified_user:
                self.current_user_info = verified_user
                self.show_info_message("Login Successful", f"Welcome, {verified_user['username']}!")
                self.update_admin_ui()
                
                self.reset_inactivity_timer()                                             
                                                                   
                                                                                       
                                                                       
                                                   
            else:
                self.show_error_message("Login Failed", "Invalid username or password.")
                self.current_user_info = None                          
                self.update_admin_ui()
        elif accepted:
            self.show_error_message("Login Failed", "Username and password cannot be empty.")
            self.current_user_info = None                          
            self.update_admin_ui()
        else:
                            
            pass
        
    def logout(self):
        """Logs out the current user."""
        self.stop_inactivity_timer()                               
        self.current_user_info = None
        self.update_admin_ui()
        self.statusBar.showMessage("Logged out.", 3000)
        self.name_input.setFocus()              


    def load_combobox_data(self):
        """Load data into ComboBoxes from the database."""
        pass
                    
        

    def show_error_message(self, title, message):
        """Display a critical error message box."""
        QMessageBox.critical(self, title, message)

    def show_info_message(self, title, message):
        """Display an informational message box."""
        QMessageBox.information(self, title, message)

    def clear_inputs(self):
        """Clear all input fields and reset focus."""
        self.name_input.clear()
        self.chemical_input.clear()
        self.number_input.clear()
        self.type_input.clear()
                                            
        self.name_input.setFocus()                                

    def submit_data(self):
        """Process and save the entered chemical transaction, sending immediate alert if configured."""
        username_logged = self.name_input.text().strip()
        chemical_name_logged = self.chemical_input.text().strip()
        number_str = self.number_input.text().strip()
        type_str = self.type_input.text().strip().lower()
                                           

                            
        if not username_logged:
            self.show_error_message("Input Error", "User Name cannot be empty.")
            self.name_input.setFocus()
            return
        if not chemical_name_logged:
            self.show_error_message("Input Error", "Chemical cannot be empty.")
            self.chemical_input.setFocus()
            return
        if not number_str:
            self.show_error_message("Input Error", "Quantity cannot be empty.")
            self.number_input.setFocus()
            return

        try:
            quantity = float(number_str)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            self.show_error_message("Invalid Input", "Quantity must be a positive number.")
            self.number_input.setFocus()
            self.number_input.selectAll()
            return

                                    
        if type_str == "fillin":
            transaction_type = "FillIn"
        elif type_str == "takeout" or type_str == "":
            transaction_type = "TakeOut"
        else:
            self.show_error_message("Invalid Input", "Type must be 'FillIn', 'TakeOut', or blank (defaults to TakeOut).")
            self.type_input.setFocus()
            self.type_input.selectAll()
            return

                                         
        user_id = None
        user_data = None
        db_user_name = username_logged                        
        is_whoknows = username_logged.lower() == 'whoknows'

        if not is_whoknows:
            user_data = db.get_user(username_logged)
            if user_data:
                user_id = user_data[0]
                db_user_name = user_data[1]                                   
            else:
                self.show_error_message("User Not Found", f"User '{username_logged}' not found. Please use a registered name or 'Whoknows'.")
                self.name_input.setFocus()
                return
                                                                     

        chemical_data = db.get_chemical(chemical_name_logged)
        if chemical_data:
            chemical_id = chemical_data['chemical_id']
            current_stock = chemical_data['current_stock']
            threshold = chemical_data['threshold']
            db_chemical_name = chemical_data['name']                                   

                                                               
            if transaction_type == 'TakeOut' and current_stock < quantity:
                self.show_error_message("Insufficient Stock", f"Only {current_stock:.2f} units of '{db_chemical_name}' remaining. Cannot take out {quantity:.2f}.")
                self.number_input.setFocus()
                return
        else:
            self.show_error_message("Chemical Not Found", f"Chemical '{chemical_name_logged}' not found in the database. Please contact an admin to add it.")
            self.chemical_input.setFocus()
            return

                                                                             
                                                                   

                                 
        try:
                                                                                
            result = db.add_transaction(
                user_id=user_id,
                username_logged=db_user_name,
                chemical_id=chemical_id,
                chemical_name_logged=db_chemical_name,
                transaction_type=transaction_type,
                quantity=quantity,
                notes=None                                    
            )

            if 'error' in result:
                 self.show_error_message("Database Error", f"Could not log transaction: {result['error']}")
            else:
                                     
                self.statusBar.showMessage(f"Logged: {db_user_name} {transaction_type} {quantity:.2f} {db_chemical_name}", 5000)
                self.clear_inputs()

                                                                   
                if result.get('low_stock'):
                                                                            
                    current_stock_alert = result.get('current_stock', 'N/A')                            
                    self.show_info_message("Low Stock Warning",
                                           f"Chemical '{db_chemical_name}' is running low! Remaining: {current_stock_alert:.2f} (Threshold: {threshold:.2f})")

                                                                          
                    notify_now = utils.get_setting(self.config, 'Telegram', 'NotifyImmediately', fallback='True').lower() == 'true'

                    if notify_now:
                        bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
                        chat_id = utils.get_setting(self.config, 'Telegram', 'ChatID')

                                                                                 
                        if bot_token and chat_id and 'YOUR_BOT_TOKEN_HERE' not in bot_token and 'YOUR_CHAT_ID_HERE' not in chat_id:
                            warning_message = (
                                f"⚠️ <b>IMMEDIATE Low Stock Warning</b> ⚠️\n\n"
                                f"Chemical: <b>{db_chemical_name}</b>\n"
                                f"Remaining: <b>{current_stock_alert:.2f}</b>\n"                    
                                f"Threshold: {threshold:.2f}\n\n"
                                f"Triggered by: {db_user_name} ({transaction_type} {quantity:.2f}). How Dare You?"
                            )
                                                     
                            utils.send_telegram_in_thread(bot_token, chat_id, warning_message)
                            logging.info(f"Low stock alert for {db_chemical_name}. NotifyImmediately=True. Attempting Telegram send.")

                            line_group_id = os.getenv("LINE_GROUP_ID") or utils.get_setting(
                                self.config, 'LINE', 'GroupID', fallback='')
                            line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or utils.get_setting(
                                self.config, 'LINE', 'ChannelAccessToken', fallback='')
                            if line_group_id and line_token:
                                line_bot.sendLineAlert(line_group_id, warning_message, line_token)
                        else:
                            logging.warning(f"Low stock alert for {db_chemical_name}, but Telegram is not configured correctly in settings.ini.")
                            line_group_id = os.getenv("LINE_GROUP_ID") or utils.get_setting(
                                self.config, 'LINE', 'GroupID', fallback='')
                            line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or utils.get_setting(
                                self.config, 'LINE', 'ChannelAccessToken', fallback='')
                            if line_group_id and line_token:
                                line_message = (
                                    f"IMMEDIATE Low Stock Warning\n\n"
                                    f"Chemical: {db_chemical_name}\n"
                                    f"Remaining: {current_stock_alert:.2f}\n"
                                    f"Threshold: {threshold:.2f}\n"
                                    f"Triggered by: {db_user_name} ({transaction_type} {quantity:.2f})"
                                )
                                line_bot.sendLineAlert(line_group_id, line_message, line_token)
                    else:
                                                                
                        logging.info(f"Low stock alert for {db_chemical_name}. NotifyImmediately=False. Immediate Telegram message suppressed.")
                                                            

        except Exception as e:
            self.show_error_message("Unexpected Error", f"An error occurred while saving data: {e}")
            logging.error(f"Error in submit_data after DB call: {e}", exc_info=True)

    def show_history(self):
        """Creates and shows the History Window."""
        if self.history_window is None or not self.history_window.isVisible():
            self.history_window = HistoryWindow(self)

                                                         
            is_logged_in = False
            is_admin = False
            if self.current_user_info:
                is_logged_in = True
                is_admin = bool(self.current_user_info.get('is_admin', False))
                                     

                                                   
            self.history_window.update_admin_controls(is_logged_in, is_admin)
            self.history_window.show()
        else:
                                                                                
            is_logged_in = bool(self.current_user_info)
            is_admin = bool(self.current_user_info and self.current_user_info.get('is_admin', False))
            self.history_window.update_admin_controls(is_logged_in, is_admin)
            self.history_window.activateWindow()
            self.history_window.raise_()
    def closeEvent(self, event):
        """
        Require confirmation before closing the application.
        """
                                           
        user_name, ok = QInputDialog.getText(self, "Confirm Exit", "Type Your Name To Confirm to Quit Application:")

        if ok and user_name.strip():
                                                   
            user_name = user_name.strip()
            logging.info(f"Application is being closed by '{user_name}'.")
            
                                                          
                                     
            bot_token = utils.get_setting(self.config, 'Telegram', 'BotToken')
            chat_id = utils.get_setting(self.config, 'Telegram', 'ChatID')
                                                           
            if bot_token and chat_id and 'YOUR_BOT_TOKEN_HERE' not in bot_token and 'YOUR_CHAT_ID_HERE' not in str(chat_id):
                message = f"🛑 **Application Shutdown** 🛑\nThe Manager Application Already Quit by: **{user_name}**."
                                                                           
                utils.send_telegram_message(bot_token, chat_id, message, parse_mode="HTML")
                                       

            if self.ngrok_process and self.ngrok_process.poll() is None:
                logging.info("Stopping Ngrok tunnel.")
                self.ngrok_process.terminate()
                try:
                    self.ngrok_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.ngrok_process.kill()
                    self.ngrok_process.wait(timeout=2)
                self.ngrok_process = None

            event.accept()                         
        else:
                                                           
            event.ignore()                                              

    def import_data(self):
        """Imports data from the specified Excel file."""
                                                   
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self,
                                                   "Select Excel File to Import",
                                                   "",                  
                                                   "Excel Files (*.xlsx *.xls);;All Files (*)",
                                                   options=options)
        if file_name:
            reply = QMessageBox.question(self, 'Confirm Import',
                                         f"Are you sure you want to import data from '{os.path.basename(file_name)}'?\nThis will read data and update the database. Stock levels will be recalculated.",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.statusBar.showMessage(f"Importing data from {os.path.basename(file_name)}...", 0)                     
                QApplication.processEvents()            
                try:
                    success = db.import_from_excel(file_name)
                    if success:
                        self.statusBar.showMessage("Import successful! Reloading data...", 5000)
                        self.load_combobox_data()               
                    else:
                        self.statusBar.showMessage("Import failed. Check console log.", 5000)
                        self.show_error_message("Import Error", "Import failed. Please check the console for details.")
                except Exception as import_err:
                     self.statusBar.showMessage(f"Import error: {import_err}", 10000)
                     self.show_error_message("Import Error", f"An unexpected error occurred during import: {import_err}\n\n{traceback.format_exc()}")

                              
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')                
    app = QApplication(sys.argv)

    lock_key = "MaLab_ChemicalManager_LockKey"
    shared_memory = QSharedMemory(lock_key)

    if not shared_memory.create(1):
                                 
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Application Already Running")
        
                                    
        countdown = [5] 
        msg_box.setText(f"One version of Ma Lab Chemical Manager Still running.\nThis window will close in {countdown[0]} seconds.")
        
        
        timer = QTimer()
        
                            
        def update_countdown():
            countdown[0] -= 1
            if countdown[0] > 0:
                msg_box.setText(f"One version of Ma Lab Chemical Manager Still running.\nThis window will close in {countdown[0]} seconds.")
            else:
                timer.stop()
                msg_box.accept() 

        timer.timeout.connect(update_countdown)
        timer.start(1000)                 
        msg_box.exec() 
        sys.exit(1) 
   

    window = ChemicalApp()
    window.show()
    sys.exit(app.exec())
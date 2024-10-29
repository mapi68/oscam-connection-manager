import configparser
import ftplib
import os
import sys
from datetime import datetime
import requests
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit,
                           QVBoxLayout, QWidget, QLabel, QLineEdit, QComboBox,
                           QHBoxLayout, QDialog, QGridLayout, QMessageBox,
                           QStyle, QInputDialog, QDialogButtonBox)

class AddHostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Add New Host")
        layout = QGridLayout(self)

        layout.addWidget(QLabel("Display Name:"), 0, 0)
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input, 0, 1)

        layout.addWidget(QLabel("Hostname/IP:"), 1, 0)
        self.host_input = QLineEdit()
        layout.addWidget(self.host_input, 1, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, 2, 0, 1, 2)

        self.setStyleSheet("""
            QWidget {background-color: #2b2b2b; color: #ffffff;}
            QLineEdit {background-color: #3a3a3a; border: 1px solid #646464; border-radius: 3px; padding: 2px;}
            QPushButton {background-color: #4a4a4a; border: 1px solid #646464; border-radius: 5px; padding: 5px; min-width: 60px;}
            QPushButton:hover {background-color: #5a5a5a;}
        """)

    def get_data(self):
        return {'name': self.name_input.text().strip(), 'host': self.host_input.text().strip()}

    def accept(self):
        if not self.name_input.text().strip() or not self.host_input.text().strip():
            QMessageBox.warning(self, "Warning", "Both fields are required!")
            return
        super().accept()

class OscamServerViewer(QDialog):
    def __init__(self, content):
        super().__init__()
        self.setup_ui(content)

    def setup_ui(self, content):
        self.setWindowTitle("oscam.server Viewer")
        self.resize(500, 650)

        layout = QVBoxLayout()

        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setPlainText("\n".join(content))
        layout.addWidget(self.viewer)

        button = QPushButton("Close")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {background-color: #2b2b2b; color: #ffffff;}
            QTextEdit {background-color: #3a3a3a; border: 1px solid #646464; border-radius: 3px; padding: 2px; font-family: monospace;}
            QPushButton {background-color: #4a4a4a; border: 1px solid #646464; border-radius: 5px; padding: 5px; min-width: 80px;}
            QPushButton:hover {background-color: #5a5a5a;}
        """)

class OscamServerEditor(QDialog):
    def __init__(self, content="", parent=None):
        super().__init__(parent)
        self.setup_ui(content)

    def setup_ui(self, content):
        self.setWindowTitle("OSCam Server Editor")
        self.resize(800, 600)

        layout = QVBoxLayout()

        self.editor = QTextEdit()
        self.editor.setPlainText(content)
        layout.addWidget(self.editor)

        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {background-color: #2b2b2b; color: #ffffff;}
            QTextEdit {background-color: #3a3a3a; border: 1px solid #646464; border-radius: 3px; padding: 2px; font-family: monospace;}
            QPushButton {background-color: #4a4a4a; border: 1px solid #646464; border-radius: 5px; padding: 5px; min-width: 80px;}
            QPushButton:hover {background-color: #5a5a5a;}
        """)

    def get_content(self):
        return self.editor.toPlainText()

class HostConfig:
    def __init__(self, name="", host="", username="root", password="", directory="/etc/tuxbox/config/"):
        self.name = name
        self.host = host
        self.username = username
        self.password = password
        self.directory = directory

    @staticmethod
    def from_dict(name, data):
        return HostConfig(
            name=name,
            host=data.get("host", ""),
            username=data.get("username", "root"),
            password=data.get("password", ""),
            directory=data.get("directory", "/etc/tuxbox/config/")
        )

    def to_dict(self):
        return {
            "host": self.host,
            "username": self.username,
            "password": self.password,
            "directory": self.directory
        }

class OSCamConnection(QMainWindow):
    def __init__(self):
        super().__init__()
        self.hosts = {}
        self.current_host = None
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        self.setWindowTitle("OSCam Connection Manager by mapi68")
        self.setup_window_properties()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.setup_host_selector(main_layout)
        self.setup_connection_form(main_layout)
        self.setup_console(main_layout)
        self.setup_action_buttons(main_layout)

        self.apply_style()

    def setup_window_properties(self):
        self.resize(410, 500)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def setup_host_selector(self, parent_layout):
        host_layout = QVBoxLayout()
        host_selection = QHBoxLayout()

        self.host_combo = QComboBox()
        self.host_combo.currentTextChanged.connect(self.on_host_changed)

        add_btn = QPushButton("Add Host")
        add_btn.clicked.connect(self.add_host)
        remove_btn = QPushButton("Remove Host")
        remove_btn.clicked.connect(self.remove_host)

        host_selection.addWidget(QLabel("Host:"))
        host_selection.addWidget(self.host_combo, stretch=1)
        host_selection.addWidget(add_btn)
        host_selection.addWidget(remove_btn)

        self.host_info = QLabel()
        self.host_info.setStyleSheet("color: #aaaaaa;")

        host_layout.addLayout(host_selection)
        host_layout.addWidget(self.host_info)

        parent_layout.addLayout(host_layout)

    def setup_connection_form(self, parent_layout):
        form = QGridLayout()

        self.username_input = QLineEdit("root")
        form.addWidget(QLabel("Username:"), 0, 0)
        form.addWidget(self.username_input, 0, 1)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addWidget(QLabel("Password:"), 1, 0)
        form.addWidget(self.password_input, 1, 1)

        self.dir_combo = QComboBox()
        self.dir_combo.addItems([
            "/etc/tuxbox/config/",
            "/etc/tuxbox/config/oscam/",
            "/etc/tuxbox/config/oscam-emu/",
            "/hdd/oscam/",
            "/hdd/oscam-emu/",
            "/home/oscam/",
            "/home/oscam-emu/",
            "/media/hdd/oscam/",
            "/media/hdd/oscam-emu/",
            "/media/usb/oscam/",
            "/media/usb/oscam-emu/",
            "/usr/local/etc/",
            "/usr/local/oscam/config/",
            "/usr/share/oscam/config/",
            "/var/tuxbox/config/",
            "/var/etc/",
            "/var/oscam/config/"
        ])
        self.dir_combo.setEditable(True)
        form.addWidget(QLabel("Directory:"), 2, 0)
        form.addWidget(self.dir_combo, 2, 1)

        parent_layout.addLayout(form)

    def setup_console(self, parent_layout):
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(100)
        parent_layout.addWidget(self.console)

    def setup_action_buttons(self, parent_layout):
        base_style = """
            QPushButton {
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px;
                min-height: 30px;
                %s
            }
            QPushButton:hover {
                %s
            }
        """
        
        conn_layout = QHBoxLayout()
        test_btn = QPushButton("Test Connection")
        test_btn.setStyleSheet(base_style % ("background-color: #4CAF50;", "background-color: #45a049;"))
        test_btn.clicked.connect(self.test_connection)
        
        save_btn = QPushButton("Save Configuration")
        save_btn.setStyleSheet(base_style % ("background-color: #2196F3;", "background-color: #1e88e5;"))
        save_btn.clicked.connect(self.save_config)
        
        backup_btn = QPushButton("Backup all OSCam")
        backup_btn.setStyleSheet(base_style % ("background-color: #607D8B;", "background-color: #546E7A;"))
        backup_btn.clicked.connect(self.backup_config)
        
        conn_layout.addWidget(test_btn)
        conn_layout.addWidget(save_btn)
        conn_layout.addWidget(backup_btn)
        parent_layout.addLayout(conn_layout)

        view_edit_layout = QHBoxLayout()
        view_btn = QPushButton("View remote oscam.server")
        view_btn.setStyleSheet(base_style % ("background-color: #9C27B0;", "background-color: #8E24AA;"))
        view_btn.clicked.connect(self.view_remote_server)
        
        edit_remote_btn = QPushButton("Edit remote oscam.server")
        edit_remote_btn.setStyleSheet(base_style % ("background-color: #FF9800;", "background-color: #F57C00;"))
        edit_remote_btn.clicked.connect(self.edit_remote_server)
        
        edit_local_btn = QPushButton("Edit local oscam.server")
        edit_local_btn.setStyleSheet(base_style % ("background-color: #FF5722;", "background-color: #F4511E;"))
        edit_local_btn.clicked.connect(self.edit_local_server)
        
        view_edit_layout.addWidget(view_btn)
        view_edit_layout.addWidget(edit_remote_btn)
        view_edit_layout.addWidget(edit_local_btn)
        parent_layout.addLayout(view_edit_layout)

        transfer_layout = QHBoxLayout()
        upload_btn = QPushButton("Upload local oscam.server")
        upload_btn.setStyleSheet(base_style % ("background-color: #00BCD4;", "background-color: #00ACC1;"))
        upload_btn.clicked.connect(self.upload_server)
        
        download_btn = QPushButton("Download remote oscam.server")
        download_btn.setStyleSheet(base_style % ("background-color: #3F51B5;", "background-color: #3949AB;"))
        download_btn.clicked.connect(self.download_server)
        
        restart_btn = QPushButton("Restart OSCam")
        restart_btn.setStyleSheet(base_style % ("background-color: #E91E63;", "background-color: #D81B60;"))
        restart_btn.clicked.connect(self.restart_oscam)
        
        transfer_layout.addWidget(upload_btn)
        transfer_layout.addWidget(download_btn)
        transfer_layout.addWidget(restart_btn)
        parent_layout.addLayout(transfer_layout)

    def apply_style(self):
        self.setStyleSheet("""
            QWidget {background-color: #2b2b2b; color: #ffffff;}
            QPushButton {background-color: #4a4a4a; border: 1px solid #646464; border-radius: 5px; padding: 5px; min-height: 30px;}
            QPushButton:hover {background-color: #5a5a5a;}
            QTextEdit, QLineEdit, QComboBox {background-color: #3a3a3a; border: 1px solid #646464; border-radius: 3px; padding: 2px;}
            QLabel {color: #d4d4d4;}
        """)

    def view_remote_server(self):
        ftp = self.get_ftp_connection()
        if not ftp:
            return

        try:
            remote_files = ftp.nlst()
            if "oscam.server" not in remote_files:
                self.show_error("Remote oscam.server file not found")
                return

            content = []
            ftp.retrlines("RETR oscam.server", content.append)
            viewer = OscamServerViewer(content)
            viewer.exec()
        except Exception as e:
            self.show_error(f"Failed to view server file: {e}")
        finally:
            ftp.quit()

    def download_server(self):
        if not self.current_host:
            self.show_error("No host selected")
            return
            
        ftp = self.get_ftp_connection()
        if not ftp:
            return
            
        try:
            remote_files = ftp.nlst()
            if "oscam.server" not in remote_files:
                self.show_error("Remote oscam.server file not found")
                return
                
            # Create filename with host name
            local_filename = f"oscam.server_{self.current_host}"
            
            # Se esiste già un file locale, semplicemente lo sovrascriviamo
            with open(local_filename, "wb") as f:
                ftp.retrbinary("RETR oscam.server", f.write)
            self.log(f"oscam.server file downloaded successfully as {local_filename}")
            
        except Exception as e:
            self.show_error(f"Download failed: {e}")
        finally:
            ftp.quit()

    def edit_local_server(self):
        if not self.current_host:
            self.show_error("No host selected")
            return
            
        try:
            local_filename = f"oscam.server_{self.current_host}"
            content = ""
            if os.path.exists(local_filename):
                with open(local_filename, "r") as f:
                    content = f.read()
            
            editor = OscamServerEditor(content, self)
            if editor.exec():
                with open(local_filename, "w") as f:
                    f.write(editor.get_content())
                self.log(f"Local {local_filename} file saved successfully")
        except Exception as e:
            self.show_error(f"Error editing local server file: {e}")

    def edit_remote_server(self):
        ftp = self.get_ftp_connection()
        if not ftp:
            return
        
        try:
            remote_files = ftp.nlst()
            if "oscam.server" not in remote_files:
                self.show_error("Remote oscam.server file not found")
                return
                
            content = []
            ftp.retrlines("RETR oscam.server", content.append)
            
            editor = OscamServerEditor("\n".join(content), self)
            if editor.exec():
                content = editor.get_content()
                with open("temp_oscam.server", "w") as f:
                    f.write(content)
                
                with open("temp_oscam.server", "rb") as f:
                    ftp.storbinary("STOR oscam.server", f)
                
                os.remove("temp_oscam.server")
                self.log("Remote oscam.server file saved successfully")
                
        except Exception as e:
            self.show_error(f"Error editing remote server file: {e}")
        finally:
            ftp.quit()
            if os.path.exists("temp_oscam.server"):
                try:
                    os.remove("temp_oscam.server")
                except:
                    pass

    def upload_server(self):
        if not self.current_host:
            self.show_error("No host selected")
            return
            
        local_filename = f"oscam.server_{self.current_host}"
        if not os.path.exists(local_filename):
            self.show_error(f"Local {local_filename} file not found")
            return
            
        ftp = self.get_ftp_connection()
        if not ftp:
            return
            
        try:
            backup_path, timestamp = self.create_backup_dirs()
            try:
                remote_files = ftp.nlst()
                if "oscam.server" in remote_files:
                    backup_name = f"oscam.server.backup_{self.current_host}_{timestamp}"
                    ftp.rename("oscam.server", backup_name)
                    self.log(f"Created remote backup: {backup_name}")
            except:
                pass
                
            with open(local_filename, "rb") as f:
                ftp.storbinary("STOR oscam.server", f)
            self.log(f"File {local_filename} uploaded successfully as oscam.server")
            
        except Exception as e:
            self.show_error(f"Upload failed: {e}")
        finally:
            ftp.quit()
    
    def create_backup_dirs(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "oscam_backups"
        
        if not self.current_host:
            backup_path = os.path.join(backup_dir, "no_host", f"backup_{timestamp}")
        else:
            backup_path = os.path.join(backup_dir, self.current_host, f"backup_{timestamp}")
            
        os.makedirs(backup_path, exist_ok=True)
        return backup_path, timestamp

    def backup_config(self):
        ftp = self.get_ftp_connection()
        if not ftp:
            return
            
        try:
            backup_path, timestamp = self.create_backup_dirs()
            remote_files = ftp.nlst()
            
            successful_backups = 0
            total_files = len(remote_files)
            
            for filename in remote_files:
                try:
                    backup_file = os.path.join(backup_path, filename)
                    with open(backup_file, "wb") as f:
                        ftp.retrbinary(f"RETR {filename}", f.write)
                    successful_backups += 1
                    self.log(f"Backed up: {filename}")
                except Exception as e:
                    self.log(f"Failed to backup {filename}: {str(e)}")
                    
            self.log(f"Backup completed: {backup_path}")
            self.log(f"Successfully backed up {successful_backups} of {total_files} files")
            
            if successful_backups == 0:
                self.show_error("No files were backed up")
            elif successful_backups < total_files:
                self.show_error("Some files failed to backup")
            
        except Exception as e:
            self.show_error(f"Backup failed: {e}")
        finally:
            ftp.quit()

    def on_host_changed(self, host_name):
        if not host_name:
            self.clear_form()
            self.host_info.clear()
            return
            
        self.current_host = host_name
        host = self.hosts[host_name]
        
        self.host_info.setText(f"Hostname/IP: {host.host}")
        self.username_input.setText(host.username)
        self.password_input.setText(host.password)
        self.dir_combo.setCurrentText(host.directory)
    
    def clear_form(self):
        self.username_input.setText("root")
        self.password_input.clear()
        self.dir_combo.setCurrentText("/etc/tuxbox/config/")
        self.host_info.clear()
    
    def add_host(self):
        dialog = AddHostDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            name = data['name']
            host = data['host']
            
            if name in self.hosts:
                self.show_error("Host already exists")
                return
                
            self.hosts[name] = HostConfig(name=name, host=host)
            self.host_combo.addItem(name)
            self.host_combo.setCurrentText(name)
            self.log(f"Added new host: {name} ({host})")
    
    def remove_host(self):
        if not self.current_host:
            return
            
        reply = QMessageBox.question(
            self, 
            "Confirm Remove", 
            f"Remove host {self.current_host}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
                                   
        if reply == QMessageBox.StandardButton.Yes:
            del self.hosts[self.current_host]
            self.host_combo.removeItem(self.host_combo.currentIndex())
            self.clear_form()
            self.log(f"Removed host: {self.current_host}")
            self.current_host = None

    def test_connection(self):
        ftp = self.get_ftp_connection()
        if ftp:
            try:
                self.log("Connection successful!")
                self.log(ftp.getwelcome())
            finally:
                ftp.quit()

    def get_ftp_connection(self):
        if not self.validate_connection():
            return None
            
        try:
            host = self.hosts[self.current_host]
            ftp = ftplib.FTP(host.host, timeout=10)
            ftp.login(self.username_input.text(), self.password_input.text())
            ftp.cwd(self.dir_combo.currentText())
            return ftp
        except Exception as e:
            self.show_error(f"FTP connection failed: {e}")
            return None

    def validate_connection(self):
        if not self.current_host:
            self.show_error("No host selected")
            return False
            
        if not all([
            self.hosts[self.current_host].host,
            self.username_input.text(),
            self.password_input.text()
        ]):
            self.show_error("Please fill in all connection details")
            return False
            
        return True

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{timestamp}] {message}")
    
    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.log(f"ERROR: {message}")
    
    def show_info(self, message):
        QMessageBox.information(self, "Info", message)
        self.log(message)

    def load_config(self):
        config = configparser.ConfigParser()
        try:
            if not os.path.exists("oscam_connection_manager.conf"):
                return
                
            config.read("oscam_connection_manager.conf")
            for section in config.sections():
                if section.startswith("Host_"):
                    name = section[5:]
                    self.hosts[name] = HostConfig.from_dict(name, dict(config[section]))
                    self.host_combo.addItem(name)
                    
            if self.hosts:
                first_host = next(iter(self.hosts))
                self.host_combo.setCurrentText(first_host)
                
        except Exception as e:
            self.log(f"Error loading config: {e}")
    
    def save_config(self):
        if self.current_host:
            self.update_current_host()
            
        config = configparser.ConfigParser()
        for name, host in self.hosts.items():
            config[f"Host_{name}"] = host.to_dict()
            
        try:
            with open("oscam_connection_manager.conf", "w") as f:
                config.write(f)
            self.log("Configuration saved")
        except Exception as e:
            self.show_error(f"Error saving config: {e}")
    
    def update_current_host(self):
        if not self.current_host:
            return
            
        host = self.hosts[self.current_host]
        host.username = self.username_input.text()
        host.password = self.password_input.text()
        host.directory = self.dir_combo.currentText()

    def restart_oscam(self):
        if not self.current_host:
            self.show_error("No host selected")
            return
            
        host = self.hosts[self.current_host]
        ftp = self.get_ftp_connection()
        if not ftp:
            return
            
        try:
            remote_files = ftp.nlst()
            if "oscam.conf" not in remote_files:
                self.show_error("Remote oscam.conf file not found")
                return
                
            # Read remote oscam.conf
            conf_data = []
            ftp.retrlines('RETR oscam.conf', conf_data.append)
            ftp.quit()
            
            # Extract httpport
            http_port = None
            for line in conf_data:
                if line.strip().startswith('httpport'):
                    try:
                        # Handle both space and = separator
                        parts = line.strip().replace('=', ' ').split()
                        http_port = parts[1]
                        break
                    except IndexError:
                        continue
                        
            if not http_port:
                raise Exception("Could not find httpport in remote oscam.conf")
                
            # Send restart command
            self.log(f"Using httpport: {http_port} from remote oscam.conf")
            restart_url = f"http://{host.host}:{http_port}/shutdown.html?action=Restart"
            response = requests.get(restart_url, timeout=5)
            
            if response.status_code == 200:
                self.log("OSCam restart command sent successfully")
            else:
                self.show_error(f"Restart failed with status code: {response.status_code}")
                
        except Exception as e:
            self.show_error(f"Restart failed: {e}")
            if 'ftp' in locals():
                try:
                    ftp.quit()
                except:
                    pass

def main():
    app = QApplication(sys.argv)
    app.setStyle(QApplication.style())
    
    window = OSCamConnection()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

import sys
import time
import hashlib
import os
import csv
import webbrowser
from PyQt5 import QtWidgets, QtCore, QtGui

TIMEOUT_SECONDS = 60
PASSWORT_DATEI = "passwort.hash"
EINTRAG_DATEI = "entries.csv"

def hash_passwort(passwort):
    return hashlib.sha256(passwort.encode()).hexdigest()

def passwort_speichern(hashwert):
    with open(PASSWORT_DATEI, "w") as f:
        f.write(hashwert)

def passwort_laden():
    if not os.path.exists(PASSWORT_DATEI):
        return None
    with open(PASSWORT_DATEI, "r") as f:
        return f.read().strip()

def eintraege_laden():
    if not os.path.exists(EINTRAG_DATEI):
        return []
    with open(EINTRAG_DATEI, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        return [tuple(row) for row in reader]

def eintraege_speichern(eintraege):
    with open(EINTRAG_DATEI, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(eintraege)

MODERN_STYLE = """
QWidget {
    background-color: #23272e;
    color: #f8f8f2;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 15px;
}
QPushButton {
    background-color: #44475a;
    color: #f8f8f2;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
}
QPushButton:hover {
    background-color: #6272a4;
}
QPushButton:pressed {
    background-color: #44475a;
}
QLineEdit, QTableWidget, QDialog {
    background-color: #282a36;
    color: #f8f8f2;
    border-radius: 6px;
    border: 1px solid #44475a;
    padding: 4px;
}
QHeaderView::section {
    background-color: #44475a;
    color: #f8f8f2;
    border: none;
    font-weight: bold;
    font-size: 15px;
}
QTableWidget {
    gridline-color: #44475a;
}
QLabel {
    color: #f8f8f2;
    font-size: 15px;
}
QMessageBox {
    background-color: #23272e;
    color: #f8f8f2;
}
"""

class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setFixedSize(340, 140)
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("Login-Passwort:")
        self.pw_edit = QtWidgets.QLineEdit()
        self.pw_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.button = QtWidgets.QPushButton("Login")
        self.button.setMinimumHeight(36)
        layout.addWidget(self.label)
        layout.addWidget(self.pw_edit)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.accept)
        self.pw_edit.returnPressed.connect(self.accept)

    def get_password(self):
        return self.pw_edit.text()

class SetPasswordDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neues Passwort setzen")
        self.setFixedSize(340, 200)
        layout = QtWidgets.QVBoxLayout(self)
        self.label1 = QtWidgets.QLabel("Neues Passwort:")
        self.pw1_edit = QtWidgets.QLineEdit()
        self.pw1_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.label2 = QtWidgets.QLabel("Passwort wiederholen:")
        self.pw2_edit = QtWidgets.QLineEdit()
        self.pw2_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.button = QtWidgets.QPushButton("Setzen")
        self.button.setMinimumHeight(36)
        layout.addWidget(self.label1)
        layout.addWidget(self.pw1_edit)
        layout.addWidget(self.label2)
        layout.addWidget(self.pw2_edit)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.accept)

    def get_passwords(self):
        return self.pw1_edit.text(), self.pw2_edit.text()

class AddEntryDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eintrag hinzufügen")
        self.setFixedSize(380, 270)
        layout = QtWidgets.QFormLayout(self)
        self.dienst_edit = QtWidgets.QLineEdit()
        self.benutzer_edit = QtWidgets.QLineEdit()
        self.pw_edit = QtWidgets.QLineEdit()
        self.pw_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.link_edit = QtWidgets.QLineEdit()
        self.button = QtWidgets.QPushButton("Speichern")
        self.button.setMinimumHeight(36)
        layout.addRow("Dienst:", self.dienst_edit)
        layout.addRow("Benutzername:", self.benutzer_edit)
        layout.addRow("Passwort:", self.pw_edit)
        layout.addRow("Link (optional):", self.link_edit)
        layout.addRow(self.button)
        self.button.clicked.connect(self.accept)

    def get_entry(self):
        return (
            self.dienst_edit.text(),
            self.benutzer_edit.text(),
            self.pw_edit.text(),
            self.link_edit.text()
        )

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Passwortmanager")
        self.setMinimumSize(700, 450)
        self.eintraege = [tuple(row) if len(row) == 4 else (row[0], row[1], row[2], "") for row in eintraege_laden()]
        self.last_action = time.time()
        self.logged_in = False
        self.init_ui()
        self.show_login()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.check_timeout)
        self.timer.start(1000)

    def init_ui(self):
        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.layout = QtWidgets.QVBoxLayout(self.central)
        self.layout.setSpacing(18)
        self.layout.setContentsMargins(40, 40, 40, 40)

        self.title = QtWidgets.QLabel("🔐 Passwortmanager")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 20px;")
        self.layout.addWidget(self.title)

        self.button_add = QtWidgets.QPushButton("➕ Eintrag hinzufügen")
        self.button_show = QtWidgets.QPushButton("📋 Einträge anzeigen")
        self.button_logout = QtWidgets.QPushButton("🚪 Logout")
        for btn in (self.button_add, self.button_show, self.button_logout):
            btn.setMinimumHeight(44)
            btn.setMaximumWidth(260)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            btn.setStyleSheet("font-size: 17px;")
            self.layout.addWidget(btn, alignment=QtCore.Qt.AlignCenter)

        self.button_add.clicked.connect(self.add_entry)
        self.button_show.clicked.connect(self.show_entries)
        self.button_logout.clicked.connect(self.show_login)

    def reset_timeout(self):
        self.last_action = time.time()

    def check_timeout(self):
        if self.logged_in and (time.time() - self.last_action > TIMEOUT_SECONDS):
            QtWidgets.QMessageBox.information(self, "Timeout", "Automatischer Logout wegen Inaktivität.")
            self.show_login()

    def show_login(self):
        self.logged_in = False
        self.reset_timeout()
        gespeicherter_hash = passwort_laden()
        if gespeicherter_hash is None:
            self.show_set_password()
            return
        while True:
            dlg = LoginDialog(self)
            if dlg.exec_() == QtWidgets.QDialog.Accepted:
                pw = dlg.get_password()
                if hash_passwort(pw) == gespeicherter_hash:
                    self.logged_in = True
                    self.reset_timeout()
                    break
                else:
                    QtWidgets.QMessageBox.warning(self, "Fehler", "Falsches Passwort.")
            else:
                sys.exit(0)

    def show_set_password(self):
        while True:
            dlg = SetPasswordDialog(self)
            if dlg.exec_() == QtWidgets.QDialog.Accepted:
                pw1, pw2 = dlg.get_passwords()
                if pw1 == pw2 and pw1:
                    passwort_speichern(hash_passwort(pw1))
                    QtWidgets.QMessageBox.information(self, "Erfolg", "Passwort gesetzt.")
                    break
                else:
                    QtWidgets.QMessageBox.warning(self, "Fehler", "Passwörter stimmen nicht überein oder sind leer.")
            else:
                sys.exit(0)
        self.show_login()

    def add_entry(self):
        self.reset_timeout()
        dlg = AddEntryDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            dienst, benutzer, pw, link = dlg.get_entry()
            if dienst and benutzer and pw:
                self.eintraege.append((dienst, benutzer, pw, link))
                eintraege_speichern(self.eintraege)
                QtWidgets.QMessageBox.information(self, "Gespeichert", "Eintrag gespeichert.")
            else:
                QtWidgets.QMessageBox.warning(self, "Fehler", "Bitte alle Felder ausfüllen.")

    def show_entries(self):
        self.reset_timeout()
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Einträge")
        dlg.setMinimumSize(700, 370)
        layout = QtWidgets.QVBoxLayout(dlg)
        table = QtWidgets.QTableWidget(dlg)

        # Jetzt 6 Spalten: Dienst, Benutzername, Passwort, Link, Link-Button, Copy-Button
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Dienst", "Benutzername", "Passwort", "Link", "🌐 Link öffnen", "📋 Kopieren"])
        table.setRowCount(len(self.eintraege))
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("alternate-background-color: #282a36; background-color: #23272e;")

        for i, (dienst, benutzer, pw, link) in enumerate(self.eintraege):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(dienst))
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(benutzer))
            table.setItem(i, 2, QtWidgets.QTableWidgetItem(pw))
            table.setItem(i, 3, QtWidgets.QTableWidgetItem(link))

            # Link-Button
            btn_link = QtWidgets.QPushButton("🌐Link öffnen")
            btn_link.setToolTip("Link öffnen")
            btn_link.setStyleSheet("font-size: 18px;")
            if link:
                btn_link.clicked.connect(lambda _, l=link: webbrowser.open(l))
            else:
                btn_link.clicked.connect(lambda _, dlg=dlg: QtWidgets.QMessageBox.information(dlg, "Hinweis", "Kein Link vorhanden."))

            table.setCellWidget(i, 4, btn_link)

            # Copy-Button
            btn_copy = QtWidgets.QPushButton("📋 Benutzername & Passwort kopieren")
            btn_copy.setToolTip("Benutzername & Passwort kopieren")
            btn_copy.setStyleSheet("font-size: 18px;")
            btn_copy.clicked.connect(lambda _, b=benutzer, p=pw: self.copy_to_clipboard(b, p))
            table.setCellWidget(i, 5, btn_copy)

        table.resizeColumnsToContents()
        layout.addWidget(table)

        btn_close = QtWidgets.QPushButton("Schließen")
        btn_close.setMinimumHeight(36)
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close, alignment=QtCore.Qt.AlignRight)

        dlg.exec_()

    def copy_to_clipboard(self, benutzer, pw):
        self.reset_timeout()
        text = f"Benutzername: {benutzer}\nPasswort: {pw}"
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(text)
        QtWidgets.QMessageBox.information(self, "Kopiert", "Benutzername und Passwort wurden in die Zwischenablage kopiert.")

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
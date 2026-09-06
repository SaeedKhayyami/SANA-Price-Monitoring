import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QIcon
from app.main_window import MainWindow,Splash,LoginDialog

BASE = Path(sys.executable).resolve().parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent

def main():
    app=QApplication(sys.argv)
    app.setApplicationName("سانا")
    app.setLayoutDirection(Qt.RightToLeft)
    app.setWindowIcon(QIcon(str(BASE/"resources"/"app.ico")))

    login=LoginDialog()
    if login.exec()!=QDialog.Accepted:
        return

    splash=Splash(BASE);splash.show();app.processEvents()
    win=MainWindow(BASE)
    QTimer.singleShot(900,lambda:(win.show(),splash.finish(win)))
    sys.exit(app.exec())

if __name__=="__main__":main()

def make_style(font_family="B Nazanin", font_size=13):
    ff = str(font_family).replace('"', '')
    fs = max(8, min(28, int(font_size)))
    return f"""
* {{ font-family: "{ff}","Vazirmatn","Tahoma"; font-size: {fs}px; }}
QMainWindow, QWidget {{ background:#f4f8fc; color:#18344f; }}
QLabel {{ background: transparent; }}
QFrame#sidebar {{ background:#07519a; border:0; }}
QFrame#topbar {{ background:#073f79; border:0; }}
QLabel#brand {{ background:transparent; color:white; font-size:{fs+5}px; font-weight:700; }}
QLabel#topTitle {{ background:transparent; color:white; font-size:{fs+4}px; font-weight:700; }}
QLabel#clockLabel {{ background:transparent; color:#d9edff; }}
QLabel#pageTitle {{ background:transparent; color:#0a4f8e; font-size:{fs+11}px; font-weight:800; }}
QPushButton#nav {{ color:white; background:transparent; border:0; border-radius:8px; padding:11px 15px; text-align:right; }}
QPushButton#nav:hover {{ background:#176fc0; }}
QPushButton#nav:checked {{ background:#2682d8; }}
QFrame#card {{ background:white; border:1px solid #d8e6f2; border-radius:12px; }}
QLabel#metricTitle {{ background:transparent; color:#6c8398; }}
QLabel#metricValue {{ background:transparent; color:#0b5cab; font-size:{fs+10}px; font-weight:800; }}
QPushButton#primary {{ background:#0b68c9; color:white; border:0; border-radius:8px; padding:9px 15px; font-weight:700; }}
QPushButton#primary:hover {{ background:#0757ab; }}
QPushButton#secondary {{ background:white; color:#0b5cab; border:1px solid #bcd3e8; border-radius:8px; padding:8px 13px; }}
QLineEdit,QComboBox,QSpinBox {{ background:white; border:1px solid #c9dceb; border-radius:7px; padding:7px; min-height:22px; }}
QTableWidget {{ background:white; border:1px solid #d8e6f2; border-radius:10px; gridline-color:#e8f0f6; }}
QHeaderView::section {{ background:#eaf3fb; color:#174a76; border:0; padding:9px; font-weight:700; }}
QTableWidget::item:selected {{ background:#d9ecff; color:#0a4479; }}
QStatusBar {{ background:#07519a; color:white; }}
QProgressBar {{ border:0; border-radius:7px; background:#cfe4f6; min-height:12px; }}
QProgressBar::chunk {{ border-radius:7px; background:#1987e8; }}
QMessageBox QLabel {{ background:transparent; }}
"""
STYLE = make_style()

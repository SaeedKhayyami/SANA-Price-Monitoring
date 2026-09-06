from pathlib import Path
import os
import shutil
from PySide6.QtWidgets import *
from PySide6.QtGui import QPixmap,QIcon,QPainter,QColor,QFont,QFontDatabase,QPen
from PySide6.QtCore import Qt,QTimer,QThread,Signal,QStringListModel,QRectF
from .services.settings import Settings
from .services.database import Database
from .services.collector_runner import CollectorRunner
from .services.jalali import money,jalali_dt,now_label
from .ui.theme import make_style


class LoginDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("ورود به سانا")
        self.setModal(True)
        self.setFixedSize(460,520)
        self.setObjectName("loginDialog")

        self.setStyleSheet("""
        QDialog#loginDialog{
            background:#f4f8fc;
        }
        QFrame#loginCard{
            background:white;
            border:1px solid #d9e6f2;
            border-radius:20px;
        }
        QLabel#loginTitle{
            color:#0b5cab;
            font-size:22px;
            font-weight:800;
            background:transparent;
        }
        QLabel#loginSubtitle{
            color:#6c8195;
            font-size:12px;
            background:transparent;
        }
        QLabel#fieldLabel{
            color:#3e5870;
            font-size:12px;
            font-weight:700;
            background:transparent;
        }
        QLineEdit{
            min-height:44px;
            border:1px solid #c9d9e8;
            border-radius:10px;
            padding:0 12px;
            background:#f9fbfd;
            color:#17324d;
            font-size:13px;
        }
        QLineEdit:focus{
            border:2px solid #1687e0;
            background:white;
        }
        QPushButton#loginButton{
            min-height:46px;
            border:none;
            border-radius:11px;
            background:#0b6fc2;
            color:white;
            font-size:14px;
            font-weight:800;
        }
        QPushButton#loginButton:hover{
            background:#095fa7;
        }
        QPushButton#loginButton:pressed{
            background:#084e89;
        }
        QCheckBox{
            color:#59738b;
            background:transparent;
            spacing:7px;
        }
        """)

        outer=QVBoxLayout(self)
        outer.setContentsMargins(28,24,28,24)

        card=QFrame()
        card.setObjectName("loginCard")
        root=QVBoxLayout(card)
        root.setContentsMargins(34,28,34,28)
        root.setSpacing(12)

        title=QLabel("ورود به سانا")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        subtitle=QLabel("سامانه استعلام نرخ آهن‌آلات")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        root.addWidget(subtitle)
        root.addSpacing(8)

        user_label=QLabel("نام کاربری")
        user_label.setObjectName("fieldLabel")
        user_label.setAlignment(Qt.AlignRight)
        root.addWidget(user_label)

        self.username=QLineEdit()
        self.username.setPlaceholderText("نام کاربری را وارد کنید")
        self.username.setLayoutDirection(Qt.LeftToRight)
        self.username.setClearButtonEnabled(True)
        root.addWidget(self.username)

        pass_label=QLabel("رمز عبور")
        pass_label.setObjectName("fieldLabel")
        pass_label.setAlignment(Qt.AlignRight)
        root.addWidget(pass_label)

        self.password=QLineEdit()
        self.password.setPlaceholderText("رمز عبور را وارد کنید")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setLayoutDirection(Qt.LeftToRight)
        root.addWidget(self.password)

        self.show_password=QCheckBox("نمایش رمز عبور")
        self.show_password.toggled.connect(
            lambda checked:self.password.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        )
        root.addWidget(self.show_password,0,Qt.AlignRight)

        self.error=QLabel("")
        self.error.setAlignment(Qt.AlignCenter)
        self.error.setWordWrap(True)
        self.error.setStyleSheet("color:#c62828;font-weight:700;background:transparent;min-height:22px;")
        root.addWidget(self.error)

        btn=QPushButton("ورود به سامانه")
        btn.setObjectName("loginButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.check_login)
        root.addWidget(btn)

        footer=QLabel("Portfolio Edition")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color:#8aa0b4;font-size:11px;background:transparent;margin-top:6px;")
        root.addWidget(footer)

        outer.addWidget(card)

        self.username.returnPressed.connect(self.check_login)
        self.password.returnPressed.connect(self.check_login)
        self.username.setFocus()

    def check_login(self):
        expected_user=os.getenv("SANA_DEMO_USER")
        expected_password=os.getenv("SANA_DEMO_PASSWORD")
        if not expected_user or not expected_password:
            self.error.setText("اطلاعات ورود تنظیم نشده است. متغیرهای محیطی SANA_DEMO_USER و SANA_DEMO_PASSWORD را تنظیم کنید.")
            return
        if self.username.text().strip()==expected_user and self.password.text()==expected_password:
            self.accept()
        else:
            self.error.setText("نام کاربری یا رمز عبور اشتباه است.")
            self.password.clear()
            self.password.setFocus()


class Splash(QSplashScreen):
    def __init__(self,base):
        base=Path(base)
        pix=QPixmap(780,430)
        pix.fill(QColor("#063667"))
        painter=QPainter(pix)
        # subtle blue panels
        painter.fillRect(0,0,780,430,QColor("#063667"))
        logo_path=base/"resources"/"sana_logo_new_transparent.png"
        if not logo_path.exists(): logo_path=base/"resources"/"logo.png"
        logo=QPixmap(str(logo_path))
        if not logo.isNull():
            scaled=logo.scaled(165,165,Qt.KeepAspectRatio,Qt.SmoothTransformation)
            x=(780-scaled.width())//2
            painter.drawPixmap(x,45,scaled)
        painter.setPen(QColor("white"))
        f=QFont("B Nazanin",17);f.setBold(True);painter.setFont(f)
        painter.drawText(45,225,690,70,Qt.AlignCenter|Qt.TextWordWrap,
                         "SANA Market Price Monitoring — Portfolio Edition")
        painter.setPen(QColor("#bfe2ff"))
        painter.setFont(QFont("B Nazanin",12))
        painter.drawText(45,330,690,35,Qt.AlignCenter,"در حال بارگذاری نرم افزار...")
        painter.fillRect(120,385,540,12,QColor("#315f8d"))
        painter.fillRect(120,385,430,12,QColor("#1d8df0"))
        painter.end()
        super().__init__(pix)
        self.setWindowFlag(Qt.FramelessWindowHint)

class Worker(QThread):
    done=Signal(bool,int,str)
    def __init__(self,runner):super().__init__();self.runner=runner
    def run(self):
        ok,code,out=self.runner.run();self.done.emit(ok,code,out)

class MainWindow(QMainWindow):
    def __init__(self,base):
        super().__init__()
        self.base=Path(base);self.cfg=Settings(base)
        self.db=Database(self.cfg.resolve("db_path"))
        self.setWindowTitle("سانا")
        self.setWindowIcon(QIcon(str(self.base/"resources"/"app.ico")))
        self.resize(1480,880);self.setMinimumSize(1120,700);self.apply_font_settings(show_message=False)
        self.pages=QStackedWidget();self.nav_buttons=[];self.page_titles=[]
        self._build();self.refresh_all()
        self.timer=QTimer(self);self.timer.timeout.connect(self._clock);self.timer.start(30000);self._clock()

    def _build(self):
        root=QWidget();self.setCentralWidget(root)
        h=QHBoxLayout(root);h.setContentsMargins(0,0,0,0);h.setSpacing(0)
        side=QFrame();side.setObjectName("sidebar");side.setMinimumWidth(210);side.setMaximumWidth(290)
        sv=QVBoxLayout(side);sv.setContentsMargins(14,16,14,14)
        logo=QLabel();logo.setAlignment(Qt.AlignCenter);logo.setMinimumHeight(110);logo.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
        sidebar_logo=self.base/"resources"/"sana_logo_new_transparent.png"
        if not sidebar_logo.exists(): sidebar_logo=self.base/"resources"/"logo.png"
        pix=QPixmap(str(sidebar_logo))
        if not pix.isNull(): logo.setPixmap(pix.scaled(150,100,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        sv.addWidget(logo)
        b=QLabel("واحد نظارت، کنترل و برنامه ریزی");b.setObjectName("brand");b.setAlignment(Qt.AlignCenter);b.setWordWrap(True);b.setMinimumHeight(54);b.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);sv.addWidget(b);sv.addSpacing(12)
        builders=[("محصولات",self.products),("تاریخچه قیمت",self.history),
                  ("جمع‌آوری قیمت",self.collector),("اجراها",self.runs),("دیتابیس",self.database),("تنظیمات",self.settings),("درباره ما",self.about)]
        for i,(title,fn) in enumerate(builders):
            self.pages.addWidget(fn());self.page_titles.append(title)
            btn=QPushButton(title);btn.setObjectName("nav");btn.setCheckable(True);btn.clicked.connect(lambda _,x=i:self.goto(x));sv.addWidget(btn);self.nav_buttons.append(btn)
        sv.addStretch()
        main=QFrame();mv=QVBoxLayout(main);mv.setContentsMargins(0,0,0,0);mv.setSpacing(0)
        top=QFrame();top.setObjectName("topbar");top.setFixedHeight(56);th=QHBoxLayout(top);th.setContentsMargins(18,6,18,6)
        self.top_title=QLabel("سامانه استعلام نرخ آهن آلات(سانا)");self.top_title.setObjectName("topTitle");th.addWidget(self.top_title);th.addStretch()
        self.clock=QLabel();self.clock.setObjectName("clockLabel");self.clock.setStyleSheet("font-size:16px;font-weight:700;color:#d9edff;background:transparent;");th.addWidget(self.clock)
        mv.addWidget(top);mv.addWidget(self.pages)
        h.addWidget(side);h.addWidget(main,1);self.statusBar().hide();self.goto(0)

    def shell(self,title):
        w=QWidget();v=QVBoxLayout(w);v.setContentsMargins(22,18,22,18)
        t=QLabel(title);t.setObjectName("pageTitle");v.addWidget(t);return w,v

    def goto(self,i):
        self.pages.setCurrentIndex(i);self.top_title.setText("سامانه استعلام نرخ آهن آلات(سانا)")
        for j,b in enumerate(self.nav_buttons):b.setChecked(i==j)
        if i==0:self.load_products()
        elif i==1:self.load_history_products()
        elif i==3:self.load_runs()
        elif i==4:self.refresh_db()

    def metric(self,title):
        f=QFrame();f.setObjectName("card");v=QVBoxLayout(f)
        a=QLabel(title);a.setObjectName("metricTitle");v.addWidget(a)
        b=QLabel("—");b.setObjectName("metricValue");v.addWidget(b)
        return f,b

    def table_item(self,text,user_data=None):
        it=QTableWidgetItem(str(text))
        it.setTextAlignment(Qt.AlignCenter)
        if user_data is not None:
            it.setData(Qt.UserRole,user_data)
        return it

    def display_specification(self,r):
        ptype=r.get("product_type") or ""
        grade=str(r.get("grade") or "").strip()
        size=str(r.get("size") or "").strip()
        state=str(r.get("state") or "").strip()
        if ptype=="ورق سیاه":
            thickness=grade or size
            return f"ضخامت ورق {thickness} میلی متر" if thickness else ""
        if ptype=="میلگرد آجدار":
            return f"گرید {grade}" if grade else ""
        if ptype=="نبشی":
            parts=[]
            if grade: parts.append(f"ضخامت {grade} میلی متر")
            if state: parts.append(f"حالت {state}")
            return " ".join(parts)
        if ptype=="ناودانی":
            return state
        if ptype=="پروفیل ساختمانی":
            parts=[]
            if grade: parts.append(f"ضخامت {grade} میلی متر")
            if state: parts.append(f"حالت {state}")
            return " ".join(parts)
        if ptype=="تیرآهن":
            return grade
        return grade or size

    def products(self):
        w,v=self.shell("محصولات")
        note=QLabel("(کلیه نرخ ها بدون احتساب مالیات بر ارزش افزوده است)")
        note.setStyleSheet("color:#c62828;font-size:11px;font-weight:700;background:transparent;margin-top:-6px;margin-bottom:2px;")
        note.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        note.setContentsMargins(0,0,4,0)
        v.insertWidget(1,note)

        filter_card=QFrame()
        filter_card.setObjectName("card")
        grid=QGridLayout(filter_card)
        grid.setContentsMargins(14,12,14,12)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)

        self.search=QLineEdit()
        self.search.setPlaceholderText("جستجو در محصولات...")

        self.ptype=QComboBox()
        self.ptype.addItem("انتخاب نوع محصول","")
        self.ptype.addItems(["میلگرد آجدار","ورق سیاه","نبشی","ناودانی","پروفیل ساختمانی","تیرآهن"])

        self.size=QComboBox()
        self.grade=QComboBox()
        self.company=QComboBox()
        self.location=QComboBox()

        controls=[
            ("جستجو",self.search,220),
            ("نوع محصول",self.ptype,150),
            ("سایز",self.size,120),
            ("مشخصات",self.grade,155),
            ("شرکت",self.company,190),
            ("مکان تحویل",self.location,180),
        ]

        for col,(label,widget,min_width) in enumerate(controls):
            lab=QLabel(label)
            lab.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
            lab.setStyleSheet("color:#516d86;font-weight:700;background:transparent;")
            grid.addWidget(lab,0,col)
            widget.setMinimumWidth(min_width)
            widget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
            grid.addWidget(widget,1,col)
            grid.setColumnStretch(col,1)

        # Popup lists can be wider than the visible controls so long values remain readable.
        for combo,popup_width in [
            (self.ptype,210),(self.size,180),(self.grade,260),
            (self.company,330),(self.location,300)
        ]:
            combo.setMaxVisibleItems(20)
            combo.view().setMinimumWidth(popup_width)

        for c in [self.size,self.grade,self.company,self.location]:
            c.addItem("همه","")
            c.setEnabled(False)

        v.addWidget(filter_card)

        self.product_table=QTableWidget(0,9)
        self.product_table.setHorizontalHeaderLabels(["نام","سایز (mm)","مشخصات","نوع محصول","شرکت","مکان تحویل","آخرین قیمت (ریال)","آخرین بروزرسانی","میانگین قیمت (ریال)"])
        self.product_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.product_table.horizontalHeader().setStretchLastSection(False)
        self.product_table.setSortingEnabled(True)
        self.product_table.doubleClicked.connect(self.product_detail)
        v.addWidget(self.product_table)

        self.search.textChanged.connect(self.load_products)
        self.ptype.currentIndexChanged.connect(self.type_changed)
        for c in [self.size,self.grade,self.company,self.location]:
            c.currentIndexChanged.connect(self.load_products)

        self.current_product_rows=[]
        return w

    def type_changed(self):
        p=self.ptype.currentText() if self.ptype.currentData() is None else self.ptype.currentData()
        p="" if self.ptype.currentIndex()==0 else self.ptype.currentText()
        vals=self.db.filter_values(p)
        for combo,key in [(self.size,"size"),(self.grade,"grade"),(self.company,"company"),(self.location,"location")]:
            combo.blockSignals(True);combo.clear();combo.addItem("همه","")
            for x in vals[key]:combo.addItem(str(x),str(x))
            combo.setEnabled(bool(p));combo.blockSignals(False)
        self.load_products()

    def load_products(self):
        p="" if self.ptype.currentIndex()==0 else self.ptype.currentText()
        rows=self.db.products(self.search.text().strip(),p,self.size.currentData() or "",self.grade.currentData() or "",self.company.currentData() or "",self.location.currentData() or "")
        self.current_product_rows=rows;self.product_table.setSortingEnabled(False);self.product_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            spec=self.display_specification(r)
            size_display=r["size"] or ""
            vals=[r["name"] or "",size_display,spec,r["product_type"] or "",r["company"] or "",r["location"] or "",money(r["last_price"]),jalali_dt(r["last_update"]),money(r["average_price"])]
            for j,x in enumerate(vals):
                it=self.table_item(x,r["id"]);self.product_table.setItem(i,j,it)
        self.product_table.setSortingEnabled(True)

    def product_detail(self,index):
        item=self.product_table.item(index.row(),0)
        if not item:return
        pid=item.data(Qt.UserRole)
        r=next((x for x in self.current_product_rows if x["id"]==pid),None)
        if not r:return
        d=QDialog(self);d.setWindowTitle("جزئیات محصول");d.resize(900,620);lay=QVBoxLayout(d)
        title=QLabel(r["name"] or "محصول");title.setObjectName("pageTitle");lay.addWidget(title)
        form=QFormLayout()
        detail_spec=self.display_specification(r)
        detail_size=r["size"]
        for k,val in [("نوع محصول",r["product_type"]),("سایز",detail_size),("مشخصات",detail_spec),("شرکت",r["company"]),("مکان تحویل",r["location"]),("آخرین قیمت",money(r["last_price"])),("میانگین قیمت",money(r["average_price"])),("آخرین بروزرسانی",jalali_dt(r["last_update"]))]:
            form.addRow(k+":",QLabel(str(val or "—")))
        lay.addLayout(form)
        table=QTableWidget(0,3);table.setHorizontalHeaderLabels(["زمان جمع‌آوری","قیمت (ریال)","بروزرسانی سایت"]);table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter);table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        snaps=self.db.snapshots_for_product(pid);table.setRowCount(len(snaps))
        for i,s in enumerate(snaps):
            for j,x in enumerate([jalali_dt(s["collected_at"]),money(s["price"]),s["site_update_date"] or "—"]):table.setItem(i,j,self.table_item(x))
        lay.addWidget(table);d.exec()

    def history(self):
        w,v=self.shell("تاریخچه قیمت");top=QHBoxLayout()
        self.hist_product=QComboBox();self.hist_product.setEditable(True);self.hist_product.setInsertPolicy(QComboBox.NoInsert)
        self.hist_product.setMaxVisibleItems(25)
        self.hist_product.lineEdit().setPlaceholderText("نام، سایز، مشخصات، شرکت یا محل تحویل را جستجو کنید...")
        self.hist_completer=QCompleter(self.hist_product)
        self.hist_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.hist_completer.setFilterMode(Qt.MatchContains)
        self.hist_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.hist_product.setCompleter(self.hist_completer)
        self.hist_mode=QComboBox();self.hist_mode.addItems(["روزانه","ماهانه","فصلی"]);btn=QPushButton("نمایش");btn.setObjectName("primary");btn.clicked.connect(self.load_history)
        top.addWidget(QLabel("محصول:"));top.addWidget(self.hist_product,1);top.addWidget(self.hist_mode);top.addWidget(btn);v.addLayout(top)
        self.hist_table=QTableWidget(0,5);self.hist_table.setHorizontalHeaderLabels(["دوره","میانگین قیمت (ریال)","بیشترین","کمترین","تغییرات"]);self.hist_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter);self.hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);self.hist_table.setEditTriggers(QAbstractItemView.NoEditTriggers);v.addWidget(self.hist_table);return w

    def load_history_products(self):
        self.hist_product.blockSignals(True)
        self.hist_product.clear()
        labels=[]
        self.history_label_to_id={}
        for r in self.db.products():
            spec=self.display_specification(r)
            label=f'{r["product_type"]} | {r["size"] or ""} | {spec} | {r["company"] or ""} | {r["location"] or ""}'
            self.hist_product.addItem(label,r["id"])
            labels.append(label);self.history_label_to_id[label]=r["id"]
        self.hist_completer.setModel(QStringListModel(labels,self.hist_product))
        self.hist_product.setCurrentIndex(-1)
        self.hist_product.blockSignals(False)

    def load_history(self):
        pid=self.hist_product.currentData()
        typed=self.hist_product.currentText().strip()
        if pid is None or self.hist_product.currentIndex()<0:
            pid=getattr(self,"history_label_to_id",{}).get(typed)
        rows=self.db.history_groups(pid,self.hist_mode.currentText()) if pid else []
        self.hist_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            change="—" if r["change"] is None else f'{r["change"]:+.2f}%'
            for j,x in enumerate([r["period"],money(r["avg"]),money(r["max"]),money(r["min"]),change]):self.hist_table.setItem(i,j,self.table_item(x))

    def collector(self):
        w,v=self.shell("جمع‌آوری قیمت");c=QFrame();c.setObjectName("card");f=QFormLayout(c)
        self.collector_path=QLineEdit(str(self.cfg.resolve("collector_path")));browse=QPushButton("انتخاب فایل");browse.setObjectName("secondary");browse.clicked.connect(self.pick_collector)
        row=QHBoxLayout();row.addWidget(self.collector_path);row.addWidget(browse);f.addRow("Market Collector:",row)
        self.run_btn=QPushButton("اجرای جمع‌آوری قیمت");self.run_btn.setObjectName("primary");self.run_btn.clicked.connect(self.run_collector);f.addRow("",self.run_btn)
        self.collector_status=QLabel("آماده");self.collector_status.setWordWrap(True);f.addRow("وضعیت:",self.collector_status)
        v.addWidget(c);v.addStretch();return w

    def pick_collector(self):
        p,_=QFileDialog.getOpenFileName(self,"انتخاب Market Collector","","Collector (*.py *.exe *.bat *.cmd);;همه فایل‌ها (*.*)")
        if p:self.collector_path.setText(p);self.cfg.store_path("collector_path",p)

    def run_collector(self):
        p=self.collector_path.text().strip()
        if not p:
            QMessageBox.warning(self,"جمع‌آوری قیمت","فایل Market Collector انتخاب نشده است.");return
        path=Path(p).expanduser().resolve()
        if not path.exists():
            QMessageBox.warning(self,"جمع‌آوری قیمت",f"فایل Collector پیدا نشد:\n{path}");return
        self.cfg.store_path("collector_path",str(path))
        self.run_btn.setEnabled(False);self.collector_status.setText("در حال جمع‌آوری قیمت‌ها... مرورگر ممکن است باز شود.")
        self.worker=Worker(CollectorRunner(path,self.db.path,self.base/"logs"));self.worker.done.connect(self.collector_done);self.worker.start()

    def collector_done(self,ok,code,out):
        self.run_btn.setEnabled(True)
        if ok:
            self.collector_status.setText("موفق | جمع‌آوری قیمت تکمیل شد.")
            self.refresh_all()
            QMessageBox.information(self,"جمع‌آوری قیمت","جمع‌آوری قیمت با موفقیت تمام شد و دیتابیس به‌روزرسانی شد.")
            return

        reason=""
        details=""
        for line in (out or "").splitlines():
            if line.startswith("ERROR_REASON:"):
                reason=line.split(":",1)[1].strip()
            elif line.startswith("ERROR_DETAILS:"):
                details=line.split(":",1)[1].strip()

        if not reason:
            reason=(out or "خطای نامشخص").strip()[-1500:]
        message=f"جمع‌آوری قیمت ناموفق بود.\n\nعلت خطا:\n{reason}"
        if details:
            message += f"\n\nجزئیات:\n{details}"
        message += f"\n\nکد خروج: {code}\n\nهیچ داده جدیدی برای اجرای ناموفق ثبت نشده است."
        self.collector_status.setText(message)
        QMessageBox.critical(self,"خطای جمع‌آوری قیمت",message)

    def runs(self):
        w,v=self.shell("اجراها")

        actions=QHBoxLayout()
        delete_btn=QPushButton("حذف اجرای انتخاب‌شده")
        delete_btn.setObjectName("secondary")
        delete_btn.setMinimumWidth(190)
        delete_btn.clicked.connect(self.delete_selected_runs)
        actions.addWidget(delete_btn)
        actions.addStretch()
        v.addLayout(actions)

        self.run_table=QTableWidget(0,12)
        self.run_table.setHorizontalHeaderLabels([
            "شناسه","شروع","پایان","میلگرد معتبر","ورق معتبر",
            "نبشی معتبر","ناودانی معتبر","پروفیل معتبر","تیرآهن معتبر",
            "تکراری","Snapshot ذخیره‌شده","وضعیت"
        ])
        self.run_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.run_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.run_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.run_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.run_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.run_table.setAlternatingRowColors(True)
        self.run_table.doubleClicked.connect(self.run_detail)
        v.addWidget(self.run_table)

        self.current_runs=[]
        return w

    def load_runs(self):
        rows=self.db.runs();self.current_runs=rows;self.run_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            vals=[r.get("id"),jalali_dt(r.get("started_at")),jalali_dt(r.get("finished_at")),r.get("rebar_valid"),r.get("sheet_valid"),r.get("angle_valid"),r.get("channel_valid"),r.get("profile_valid"),r.get("beam_valid"),r.get("duplicates"),r.get("snapshots_saved"),r.get("status")]
            for j,x in enumerate(vals):
                it=self.table_item(x if x is not None else "—",r.get("id"));self.run_table.setItem(i,j,it)

    def delete_selected_runs(self):
        selection=self.run_table.selectionModel()
        rows=sorted({idx.row() for idx in selection.selectedRows()})

        # Fallback for a normal single click.
        if not rows:
            current=self.run_table.currentRow()
            if current>=0:
                rows=[current]

        if not rows:
            QMessageBox.information(
                self,"اجراها",
                "ابتدا یک یا چند ردیف از اجراها را انتخاب کنید."
            )
            return

        ids=[]
        for row in rows:
            item=self.run_table.item(row,0)
            if item is None:
                continue
            try:
                ids.append(int(item.text().strip()))
            except Exception:
                try:
                    ids.append(int(item.data(Qt.UserRole)))
                except Exception:
                    pass

        ids=sorted(set(ids))
        if not ids:
            QMessageBox.warning(self,"اجراها","شناسه اجرای انتخاب‌شده پیدا نشد.")
            return

        count=len(ids)
        text=(
            "این اجرا و تمام قیمت‌های ثبت‌شده مربوط به آن حذف شود؟"
            if count==1 else
            f"{count} اجرا و تمام قیمت‌های ثبت‌شده مربوط به آن‌ها حذف شوند؟"
        )
        text += "\n\nاین عملیات قابل بازگشت نیست."

        if QMessageBox.question(
            self,"تأیید حذف",text,
            QMessageBox.Yes|QMessageBox.No,
            QMessageBox.No
        ) != QMessageBox.Yes:
            return

        try:
            deleted_runs,deleted_snapshots=self.db.delete_runs(ids)

            # Reload from database and verify the selected run IDs are gone.
            self.load_runs()
            self.load_products()
            if hasattr(self,"load_history_products"):
                self.load_history_products()

            if deleted_runs != len(ids):
                QMessageBox.warning(
                    self,"حذف اجرا",
                    f"از {len(ids)} اجرای انتخاب‌شده، {deleted_runs} اجرا حذف شد. "
                    "لطفاً دیتابیس فعال را بررسی کنید."
                )
                return

            QMessageBox.information(
                self,"حذف انجام شد",
                f"{deleted_runs} اجرا و {deleted_snapshots} رکورد قیمت مربوط به آن‌ها حذف شد."
            )
        except Exception as e:
            QMessageBox.critical(
                self,"خطای حذف اجرا",
                f"حذف اجرا انجام نشد:\n{e}"
            )

    def run_detail(self,index):
        rid=self.run_table.item(index.row(),0).data(Qt.UserRole);r=next((x for x in self.current_runs if x.get("id")==rid),None)
        if not r:return
        rows=self.db.run_snapshots(r);d=QDialog(self);d.setWindowTitle(f"جزئیات اجرای شماره {rid}");d.resize(1050,650);lay=QVBoxLayout(d)
        t=QLabel(f"اجرای شماره {rid} | {jalali_dt(r.get('started_at'))} تا {jalali_dt(r.get('finished_at'))}");t.setObjectName("pageTitle");lay.addWidget(t)
        tb=QTableWidget(len(rows),8);tb.setHorizontalHeaderLabels(["سایز","مشخصات","نوع محصول","شرکت","مکان تحویل","قیمت","زمان جمع‌آوری","بروزرسانی سایت"]);tb.horizontalHeader().setDefaultAlignment(Qt.AlignCenter);tb.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i,x in enumerate(rows):
            vals=[x["size"],x["grade"],x["product_type"],x["company"],x["location"],money(x["price"]),jalali_dt(x["collected_at"]),x["site_update_date"] or "—"]
            for j,val in enumerate(vals):tb.setItem(i,j,self.table_item(val or "—"))
        lay.addWidget(tb);d.exec()

    def database(self):
        w,v=self.shell("دیتابیس");c=QFrame();c.setObjectName("card");f=QFormLayout(c)
        self.db_path=QLineEdit(str(self.db.path));b=QPushButton("انتخاب");b.setObjectName("secondary");b.clicked.connect(self.pick_db)
        row=QHBoxLayout();row.addWidget(self.db_path);row.addWidget(b);f.addRow("مسیر دیتابیس:",row)
        apply=QPushButton("اعمال");apply.setObjectName("primary");apply.clicked.connect(self.apply_db);f.addRow("",apply)
        backup=QPushButton("ایجاد پشتیبان");backup.setObjectName("secondary");backup.clicked.connect(self.backup);f.addRow("",backup)
        self.db_info=QLabel();self.db_info.setWordWrap(True);f.addRow("وضعیت:",self.db_info);v.addWidget(c);v.addStretch();return w

    def pick_db(self):
        p,_=QFileDialog.getOpenFileName(self,"انتخاب دیتابیس","","SQLite (*.db *.sqlite *.sqlite3);;همه فایل‌ها (*.*)")
        if p:self.db_path.setText(p)

    def apply_db(self):
        p=self.db_path.text().strip()
        if not p:
            QMessageBox.warning(self,"دیتابیس","مسیر دیتابیس خالی است.");return
        path=Path(p).expanduser().resolve()
        if not path.exists():
            QMessageBox.warning(self,"دیتابیس",f"فایل دیتابیس پیدا نشد:\n{path}");return
        try:
            test=Database(path)
            stats=test.stats()
            # Trigger a real schema query too
            test.products()
        except Exception as e:
            QMessageBox.critical(self,"خطای دیتابیس",f"فایل انتخاب‌شده قابل استفاده نیست:\n{e}");return
        self.cfg.store_path("db_path",str(path));self.db=test
        self.refresh_all()
        QMessageBox.information(self,"دیتابیس",f"دیتابیس با موفقیت بارگذاری شد.\nمحصولات: {stats['products']:,}\nSnapshotها: {stats['snapshots']:,}")

    def backup(self):
        if not self.db.exists():QMessageBox.warning(self,"پشتیبان‌گیری","دیتابیس پیدا نشد.");return
        from datetime import datetime
        dst=self.base/"backups"/f"prices_{datetime.now():%Y%m%d_%H%M%S}.db";shutil.copy2(self.db.path,dst);QMessageBox.information(self,"پشتیبان‌گیری",f"پشتیبان ایجاد شد:\n{dst}")

    def settings(self):
        w,v=self.shell("تنظیمات")
        c=QFrame();c.setObjectName("card");f=QFormLayout(c)

        self.font_combo=QComboBox()
        families=QFontDatabase.families()
        preferred=["B Nazanin","Vazirmatn","Tahoma","Segoe UI"]
        ordered=[]
        for x in preferred+families:
            if x in families and x not in ordered:ordered.append(x)
        self.font_combo.addItems(ordered)
        current=self.cfg.data.get("font_family","B Nazanin")
        idx=self.font_combo.findText(current)
        if idx>=0:self.font_combo.setCurrentIndex(idx)

        self.font_size=QSpinBox();self.font_size.setRange(9,24);self.font_size.setValue(int(self.cfg.data.get("font_size",13)))
        apply=QPushButton("اعمال تنظیمات ظاهر");apply.setObjectName("primary");apply.clicked.connect(lambda:self.apply_font_settings(show_message=True))
        f.addRow("فونت نرم افزار:",self.font_combo)
        f.addRow("اندازه نوشته‌ها:",self.font_size)
        f.addRow("",apply)

        note=QLabel("تغییر فونت و اندازه بلافاصله روی تمام بخش‌های نرم افزار اعمال و برای اجرای بعدی ذخیره می‌شود.")
        note.setWordWrap(True);f.addRow("",note)
        v.addWidget(c);v.addStretch();return w

    def apply_font_settings(self,show_message=False):
        family=self.cfg.data.get("font_family","B Nazanin")
        size=int(self.cfg.data.get("font_size",13))
        if hasattr(self,"font_combo"):
            family=self.font_combo.currentText() or family
        if hasattr(self,"font_size"):
            size=self.font_size.value()
        self.cfg.data["font_family"]=family
        self.cfg.data["font_size"]=size
        self.cfg.save()
        app=QApplication.instance()
        app.setFont(QFont(family,size))
        self.setStyleSheet(make_style(family,size))
        if show_message:
            QMessageBox.information(self,"تنظیمات","فونت و اندازه نوشته‌ها اعمال و ذخیره شد.")

    def about(self):
        w,v=self.shell("درباره ما")
        c=QFrame();c.setObjectName("card");cv=QVBoxLayout(c)
        logos=QHBoxLayout();logos.setAlignment(Qt.AlignCenter)
        for path in [self.base/"resources"/"logo14_current.png",self.base/"resources"/"logo1_current.png"]:
            if path.exists():
                lab=QLabel();lab.setAlignment(Qt.AlignCenter);lab.setMinimumSize(150,150)
                pix=QPixmap(str(path))
                if not pix.isNull():lab.setPixmap(pix.scaled(170,150,Qt.KeepAspectRatio,Qt.SmoothTransformation))
                logos.addWidget(lab)
        cv.addLayout(logos)

        org=QLabel("SANA Market Price Monitoring — Portfolio Edition")
        org.setAlignment(Qt.AlignCenter);org.setStyleSheet("font-size:17px;font-weight:700;color:#0b5cab;");org.setWordWrap(True)
        cv.addWidget(org)

        desc=QLabel("سامانه SANA برای یکپارچه‌سازی فرآیند جمع‌آوری، مشاهده و تحلیل تاریخچه قیمت بازار آهن‌آلات طراحی شده است. این نسخه برای نمایش نمونه‌کار فنی منتشر شده و فاقد داده‌ها و دارایی‌های سازمانی است.")
        desc.setWordWrap(True);desc.setAlignment(Qt.AlignCenter);desc.setStyleSheet("padding:16px;")
        cv.addWidget(desc)

        ver=QLabel(f'نسخه نرم‌افزار: {self.cfg.data.get("version","1.5.0")}')
        ver.setAlignment(Qt.AlignCenter);ver.setStyleSheet("font-weight:700;color:#516d86;")
        cv.addWidget(ver)
        v.addWidget(c);v.addStretch();return w

    def refresh_all(self):
        self.load_products()
        self.load_runs()
        self.refresh_db()

    def refresh_db(self):
        s=self.db.stats();self.db_info.setText(f'محصولات: {s["products"]:,} | Snapshotها: {s["snapshots"]:,} | اجراها: {s["runs"]:,}\n{self.db.path}')

    def _clock(self):self.clock.setText(now_label())

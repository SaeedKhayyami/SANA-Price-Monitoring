import os, subprocess, sys, shutil
from pathlib import Path
from datetime import datetime

ALLOWED={".py",".exe",".bat",".cmd"}

class CollectorRunner:
    def __init__(self,path,db,log_dir):
        self.path=Path(path);self.db=Path(db);self.log_dir=Path(log_dir)

    def _python_command(self):
        # Source mode: use current Python. Built EXE: try Windows py/python launcher.
        if not getattr(sys, "frozen", False):
            return [sys.executable, str(self.path)]
        for candidate in ("py","python","python3"):
            found=shutil.which(candidate)
            if found:
                return [found, "-3", str(self.path)] if candidate=="py" else [found, str(self.path)]
        return None

    def run(self):
        if not self.path.exists():
            return False,-1,f"فایل Collector پیدا نشد:\n{self.path}"
        if not self.db.parent.exists():
            return False,-1,f"پوشه دیتابیس پیدا نشد:\n{self.db.parent}"
        if self.path.suffix.lower() not in ALLOWED:
            return False,-1,"فرمت Collector پشتیبانی نمی‌شود. فرمت‌های مجاز: py / exe / bat / cmd"
        ext=self.path.suffix.lower()
        if ext==".py":
            cmd=self._python_command()
            if not cmd:
                return False,-1,"نسخه EXE نمی‌تواند فایل Python را اجرا کند چون Python روی سیستم پیدا نشد. فایل Collector.exe را انتخاب کنید."
        elif ext in {".bat",".cmd"}:
            cmd=["cmd.exe","/c",str(self.path)]
        else:
            cmd=[str(self.path)]
        env=os.environ.copy()
        env["PRICE_MONITOR_DB"]=str(self.db.resolve())
        env["PYTHONIOENCODING"]="utf-8"
        env["PYTHONUTF8"]="1"
        env["PRICE_MONITOR_DIAG"]=str((self.log_dir/"diagnostics").resolve())
        self.log_dir.mkdir(parents=True,exist_ok=True)
        try:
            cp=subprocess.run(cmd,cwd=str(self.path.parent),env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=3600,shell=False)
            out=((cp.stdout or "")+"\n"+(cp.stderr or "")).strip()
            diag_error=self.log_dir/"diagnostics"/"last_error.txt"
            if diag_error.exists():
                try:
                    diag_text=diag_error.read_text(encoding="utf-8",errors="replace").strip()
                    if diag_text and diag_text not in out:
                        out=(out+"\n\n"+diag_text).strip()
                except Exception:
                    pass
            stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
            (self.log_dir/f"collector_{stamp}.log").write_text(
                f"COMMAND: {cmd}\nDB: {self.db}\nEXIT: {cp.returncode}\n\n{out}",
                encoding="utf-8",errors="ignore")
            return cp.returncode==0,cp.returncode,out or "(بدون خروجی متنی)"
        except subprocess.TimeoutExpired:
            return False,-1,"زمان اجرای Collector از یک ساعت بیشتر شد و متوقف گردید."
        except Exception as e:
            return False,-1,f"{type(e).__name__}: {e}"

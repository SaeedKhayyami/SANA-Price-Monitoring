from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import timezone, timedelta

try:
    TEHRAN = ZoneInfo("Asia/Tehran")
except ZoneInfoNotFoundError:
    TEHRAN = timezone(timedelta(hours=3, minutes=30))
MONTHS = ["","فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"]
SEASONS = {1:"بهار",2:"تابستان",3:"پاییز",4:"زمستان"}

def gregorian_to_jalali(gy, gm, gd):
    gdm=[0,31,59,90,120,151,181,212,243,273,304,334]
    gy2=gy+1 if gm>2 else gy
    days=355666+365*gy+(gy2+3)//4-(gy2+99)//100+(gy2+399)//400+gd+gdm[gm-1]
    jy=-1595+33*(days//12053); days%=12053
    jy+=4*(days//1461); days%=1461
    if days>365:
        jy+=(days-1)//365; days=(days-1)%365
    if days<186: jm=1+days//31; jd=1+days%31
    else: jm=7+(days-186)//30; jd=1+(days-186)%30
    return jy,jm,jd

def parse_dt(v):
    if not v: return None
    try: d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    except Exception: return None
    if d.tzinfo is None: d=d.replace(tzinfo=TEHRAN)
    return d.astimezone(TEHRAN)

def jalali_dt(v, seconds=False):
    d=parse_dt(v)
    if not d: return str(v or "—")
    y,m,day=gregorian_to_jalali(d.year,d.month,d.day)
    fmt="%H:%M:%S" if seconds else "%H:%M"
    return f"{y:04d}/{m:02d}/{day:02d} - {d.strftime(fmt)}"

def jalali_period(v):
    d=parse_dt(v)
    if not d:return None
    y,m,_=gregorian_to_jalali(d.year,d.month,d.day)
    return y,m,(m-1)//3+1

def now_label():
    d=datetime.now(TEHRAN)
    y,m,day=gregorian_to_jalali(d.year,d.month,d.day)
    return f"{y:04d}/{m:02d}/{day:02d} - {d:%H:%M}"

def money(v):
    if v in (None,""): return "—"
    try: return f"{int(float(v)):,}"
    except Exception: return str(v)

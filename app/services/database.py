import sqlite3
from pathlib import Path
from .jalali import jalali_period, MONTHS, SEASONS

class Database:
    def __init__(self,path):
        self.path=Path(path)

    def connect(self):
        c=sqlite3.connect(self.path)
        c.row_factory=sqlite3.Row
        return c

    def exists(self): return self.path.exists()

    def stats(self):
        out={"products":0,"snapshots":0,"runs":0,"last_run":None}
        if not self.exists(): return out
        with self.connect() as c:
            for k,t in [("products","products"),("snapshots","price_snapshots"),("runs","collection_runs")]:
                try: out[k]=c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                except sqlite3.Error: pass
            try:
                out["last_run"]=c.execute("SELECT finished_at FROM collection_runs ORDER BY id DESC LIMIT 1").fetchone()[0]
            except Exception: pass
        return out

    def product_type_expr(self,alias="p"):
        return f"""CASE
          WHEN COALESCE({alias}.rebar_type,'')='تیرآهن' OR COALESCE({alias}.name,'') LIKE '%تیرآهن%' THEN 'تیرآهن'
          WHEN COALESCE({alias}.rebar_type,'')='پروفیل ساختمانی' OR COALESCE({alias}.name,'') LIKE '%پروفیل%' THEN 'پروفیل ساختمانی'
          WHEN COALESCE({alias}.rebar_type,'')='ناودانی' OR COALESCE({alias}.name,'') LIKE '%ناودانی%' THEN 'ناودانی'
          WHEN COALESCE({alias}.rebar_type,'')='نبشی' OR COALESCE({alias}.name,'') LIKE '%نبشی%' THEN 'نبشی'
          WHEN LOWER(COALESCE({alias}.rebar_type,'')) LIKE '%sheet%' OR COALESCE({alias}.name,'') LIKE '%ورق%' THEN 'ورق سیاه'
          ELSE 'میلگرد آجدار' END"""

    def filter_values(self,ptype):
        if not self.exists(): return {"size":[],"grade":[],"company":[],"location":[]}
        where,args="",[]
        if ptype:
            where=f" WHERE {self.product_type_expr('p')}=?"; args=[ptype]
        qbase=f" FROM products p{where}"
        with self.connect() as c:
            def vals(expr):
                return [r[0] for r in c.execute(f"SELECT DISTINCT {expr} {qbase} AND {expr} IS NOT NULL AND TRIM({expr})<>'' ORDER BY {expr}" if where else f"SELECT DISTINCT {expr} {qbase} WHERE {expr} IS NOT NULL AND TRIM({expr})<>'' ORDER BY {expr}",args)]
            return {
                "size": vals("p.size"),
                "grade": vals("p.grade"),
                "company": vals("COALESCE(NULLIF(p.factory,''),p.brand)"),
                "location": vals("p.location"),
            }

    def products(self,search="",ptype="",size="",grade="",company="",location=""):
        if not self.exists(): return []
        where=[];args=[]
        if search:
            where.append("(p.name LIKE ? OR p.size LIKE ? OR p.grade LIKE ? OR p.factory LIKE ? OR p.brand LIKE ? OR p.location LIKE ?)")
            args += [f"%{search}%"]*6
        if ptype: where.append(self.product_type_expr("p")+"=?"); args.append(ptype)
        if size: where.append("p.size=?"); args.append(size)
        if grade: where.append("p.grade=?"); args.append(grade)
        if company: where.append("COALESCE(NULLIF(p.factory,''),p.brand)=?"); args.append(company)
        if location: where.append("p.location=?"); args.append(location)
        w=" WHERE "+" AND ".join(where) if where else ""
        q=f"""SELECT p.id,p.name,p.size,p.grade,{self.product_type_expr("p")} AS product_type,
        COALESCE(NULLIF(p.factory,''),p.brand) company,p.location,
        last.price last_price,last.collected_at last_update,
        ROUND(AVG(ps.price),2) average_price
        FROM products p
        LEFT JOIN price_snapshots ps ON ps.product_id=p.id
        LEFT JOIN (
          SELECT ps1.product_id,ps1.price,ps1.collected_at
          FROM price_snapshots ps1
          JOIN (SELECT product_id,MAX(id) max_id FROM price_snapshots GROUP BY product_id)x
          ON x.product_id=ps1.product_id AND x.max_id=ps1.id
        ) last ON last.product_id=p.id
        {w}
        GROUP BY p.id ORDER BY p.id DESC"""
        with self.connect() as c:return [dict(r) for r in c.execute(q,args)]

    def snapshots_for_product(self,pid):
        if not self.exists():return []
        with self.connect() as c:
            return [dict(r) for r in c.execute(
                "SELECT id,price,price_text,site_update_date,collected_at,source_url FROM price_snapshots WHERE product_id=? ORDER BY id",
                (pid,))]

    def history_groups(self,pid,mode):
        rows=self.snapshots_for_product(pid)
        buckets={}
        for r in rows:
            per=jalali_period(r["collected_at"])
            if not per or r["price"] is None: continue
            y,m,s=per
            if mode=="ماهانه": key=(y,m); label=f"{MONTHS[m]} {y}"
            elif mode=="فصلی": key=(y,s); label=f"{SEASONS[s]} {y}"
            else:
                # daily
                from .jalali import parse_dt, gregorian_to_jalali
                d=parse_dt(r["collected_at"])
                yy,mm,dd=gregorian_to_jalali(d.year,d.month,d.day)
                key=(yy,mm,dd);label=f"{yy:04d}/{mm:02d}/{dd:02d}"
            buckets.setdefault(key,{"label":label,"values":[]})["values"].append(int(r["price"]))
        result=[]
        prev=None
        for key in sorted(buckets):
            vals=buckets[key]["values"]; avg=sum(vals)/len(vals)
            change=((avg-prev)/prev*100) if prev else None
            result.append({"period":buckets[key]["label"],"avg":avg,"max":max(vals),"min":min(vals),"change":change})
            prev=avg
        return result

    def market_analysis(self, limit=10):
        """Return latest-vs-previous price changes for products, sorted by absolute percent change."""
        if not self.exists():
            return []
        q=f"""
        WITH ranked AS (
            SELECT ps.product_id, ps.price, ps.collected_at,
                   ROW_NUMBER() OVER (PARTITION BY ps.product_id ORDER BY ps.id DESC) rn
            FROM price_snapshots ps
        )
        SELECT p.id,p.name,p.size,p.grade,{self.product_type_expr("p")} product_type,
               COALESCE(NULLIF(p.factory,''),p.brand) company,p.location,
               MAX(CASE WHEN r.rn=1 THEN r.price END) latest_price,
               MAX(CASE WHEN r.rn=2 THEN r.price END) previous_price,
               MAX(CASE WHEN r.rn=1 THEN r.collected_at END) latest_time
        FROM products p
        JOIN ranked r ON r.product_id=p.id AND r.rn IN (1,2)
        GROUP BY p.id
        HAVING latest_price IS NOT NULL AND previous_price IS NOT NULL
        """
        with self.connect() as c:
            rows=[dict(r) for r in c.execute(q)]
        out=[]
        for r in rows:
            prev=r.get("previous_price") or 0
            latest=r.get("latest_price") or 0
            if not prev:
                continue
            r["change_percent"]=(latest-prev)/prev*100
            r["change_amount"]=latest-prev
            out.append(r)
        out.sort(key=lambda x: abs(x["change_percent"]), reverse=True)
        return out[:limit]

    def market_summary(self):
        rows=self.market_analysis(limit=10000)
        if not rows:
            return {"max_up":None,"max_down":None,"avg_change":None,"changed_count":0}
        ups=[r for r in rows if r["change_percent"]>0]
        downs=[r for r in rows if r["change_percent"]<0]
        return {
            "max_up": max(ups,key=lambda x:x["change_percent"]) if ups else None,
            "max_down": min(downs,key=lambda x:x["change_percent"]) if downs else None,
            "avg_change": sum(r["change_percent"] for r in rows)/len(rows),
            "changed_count": len([r for r in rows if abs(r["change_percent"])>1e-9]),
        }

    def delete_runs(self,ids):
        clean=sorted({int(x) for x in ids if x is not None})
        if not clean:
            return 0,0

        marks=",".join("?" for _ in clean)
        deleted_snapshots=0

        with self.connect() as c:
            runs=[dict(r) for r in c.execute(
                f"SELECT id,started_at,finished_at FROM collection_runs WHERE id IN ({marks})",
                clean
            )]

            if not runs:
                return 0,0

            # Delete all price data belonging to each selected run.
            # Current schema relates snapshots to a run by collection time window.
            for run in runs:
                start=run.get("started_at")
                end=run.get("finished_at")
                if start and end:
                    cur=c.execute(
                        "DELETE FROM price_snapshots WHERE collected_at>=? AND collected_at<=?",
                        (start,end)
                    )
                    if cur.rowcount and cur.rowcount>0:
                        deleted_snapshots += cur.rowcount

            c.execute(
                f"DELETE FROM collection_runs WHERE id IN ({marks})",
                clean
            )
            c.commit()

            left=c.execute(
                f"SELECT COUNT(*) FROM collection_runs WHERE id IN ({marks})",
                clean
            ).fetchone()[0]

        deleted_runs=len(clean)-left
        return deleted_runs,deleted_snapshots

    def runs(self):
        if not self.exists(): return []
        with self.connect() as c:
            try:return [dict(r) for r in c.execute("SELECT * FROM collection_runs ORDER BY id DESC")]
            except sqlite3.Error:return []

    def run_snapshots(self,runrow):
        start,end=runrow.get("started_at"),runrow.get("finished_at")
        if not start or not end:return []
        q=f"""SELECT p.size,p.grade,{self.product_type_expr("p")} product_type,
        COALESCE(NULLIF(p.factory,''),p.brand) company,p.location,
        ps.price,ps.collected_at,ps.site_update_date
        FROM price_snapshots ps JOIN products p ON p.id=ps.product_id
        WHERE ps.collected_at>=? AND ps.collected_at<=? ORDER BY ps.id"""
        with self.connect() as c:return [dict(r) for r in c.execute(q,(start,end))]

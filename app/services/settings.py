import json
from pathlib import Path

class Settings:
    def __init__(self, base):
        self.base=Path(base)
        self.file=self.base/"settings.json"
        self.data={}
        self.load()

    def load(self):
        self.data=json.loads(self.file.read_text(encoding="utf-8-sig"))

    def save(self):
        self.file.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding="utf-8",newline="\n")

    def resolve(self,key):
        p=Path(self.data[key])
        return p if p.is_absolute() else (self.base/p).resolve()

    def store_path(self,key,path):
        p=Path(path).resolve()
        try:self.data[key]=str(p.relative_to(self.base.resolve()))
        except ValueError:self.data[key]=str(p)
        self.save()

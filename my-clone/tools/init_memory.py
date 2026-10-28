from pathlib import Path
from datetime import date
import json, shutil

def initialize(root):
    root=Path(root)
    for folder in ("memory","private","legacy/family","sources","reviews","archive","imports","work","chats/records"):
        (root/folder).mkdir(parents=True,exist_ok=True)
    for name in ("PROFILE.md","CURRENT.md","BEHAVIOUR.md"):
        dest=root/"memory"/name
        if not dest.exists(): shutil.copyfile(root/"templates"/name,dest)
    episodes=root/"memory/EPISODES.jsonl"
    if not episodes.exists(): episodes.write_text("",encoding="utf-8")
    manifest=root/"manifest.json"
    if not manifest.exists():
        manifest.write_text(json.dumps(dict(schema_version=1,revision=1,updated_at=date.today().isoformat(),automatic_sync=False,model_finetuned=False),indent=2)+"\n",encoding="utf-8")
    return root

if __name__=="__main__":
    initialize(Path(__file__).resolve().parent.parent)
    print("Local private memory initialized; existing files preserved.")

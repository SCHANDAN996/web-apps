from pathlib import Path
import json

def build(root):
    root=Path(root)
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8-sig"))
    lines=["# मेरी डिजिटल स्मृति — निजी snapshot",f"revision {manifest['revision']} · {manifest['updated_at']}","यह private local snapshot है; family-approved export या trained model नहीं।",""]
    for name in ("memory/PROFILE.md","memory/CURRENT.md","memory/BEHAVIOUR.md"):
        path=root/name
        lines.extend(["---","स्रोत: "+name,"",path.read_text(encoding="utf-8-sig"),""])
    target=root/"MY-DIGITAL-MEMORY.md"
    target.write_text("\n".join(lines),encoding="utf-8")
    return target

if __name__=="__main__":
    print(build(Path(__file__).resolve().parent.parent))

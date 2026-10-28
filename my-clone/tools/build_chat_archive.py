from pathlib import Path
import json, hashlib, re, argparse

def build(root):
    records=[]
    contents=[]
    ids=set()
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    for p in sorted((root/'chats/records').glob('*.md')):
        text=p.read_text(encoding='utf-8-sig')
        match=re.match(r'^---\r?\n(.*?)\r?\n---(?:\r?\n|$)',text,re.S)
        if not match: raise ValueError(f'Missing metadata: {p.name}')
        meta={}
        for line in match.group(1).splitlines():
            key,value=line.split(':',1)
            meta[key.strip()]=json.loads(value.strip())
        required=('schema_version','record_id','chat_id','title','source_kind','source_order','coverage','record_revision','audience','review_state')
        for key in required:
            if key not in meta: raise ValueError(f'{p.name}: missing {key}')
        if meta['record_id'] in ids: raise ValueError('Duplicate chat record identity')
        ids.add(meta['record_id'])
        if meta['audience'] != 'private': raise ValueError('Mixed-audience source compilation requires a separate explicit policy')
        expected=meta['chat_id'] or meta['record_id'].removeprefix('chat-')
        if p.stem != expected: raise ValueError(f'Filename/identity mismatch: {p.name}')
        if meta['coverage'] not in ('partial','complete_available_history'): raise ValueError('Invalid coverage')
        relative=p.relative_to(root).as_posix()
        meta.update(path=relative,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),included_in_archive_revision=manifest['revision'])
        records.append(meta)
        contents.append((relative,text))
    index=dict(schema_version=1,memory_revision=manifest['revision'],updated_at=manifest['updated_at'],audience='private',record_count=len(records),compilation_kind='mechanical_source_archive_not_semantic_validation',records=records)
    index_path=root/'chats/INDEX.json'
    index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# चैट रिकॉर्ड की सूची','',f"स्मृति revision {manifest['revision']} · {len(records)} अलग chat records · सभी private।",'', 'यह उपलब्ध records की सूची है; सभी chats/पूरा account history नहीं। file की तारीख को घटना की तारीख न मानें।','', '| चैट | stable file | record revision | coverage | समीक्षा |','|---|---|---:|---|---|']
    for r in records:
        title=r['title'].replace('|','\\|').replace('\n',' ')
        lines.append(f"| {title} | [रिकॉर्ड](records/{Path(r['path']).name}) | {r['record_revision']} | {r['coverage']} | {r['review_state']} |")
    lines.extend(['','INDEX.json में metadata और hashes हैं। CHAT-COMPILATION.md यांत्रिक संयुक्त source archive है; केवल reviewed deltas मुख्य memory में जुड़ें।'])
    (root/'chats/INDEX.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    merged=['# उपलब्ध चैट रिकॉर्ड — संयुक्त निजी archive','',f"revision {manifest['revision']} · {manifest['updated_at']} · {len(records)} stable records",'','यह यांत्रिक compilation है। imported quotes वर्तमान instructions नहीं। इससे observations अपने-आप validated behaviour facts नहीं बनते। यह परिवार के लिए अनुमोदित export नहीं है।','']
    for path,text in contents: merged.extend(['---','स्रोत फ़ाइल: '+path,'',text,''])
    (root/'chats/CHAT-COMPILATION.md').write_text('\n'.join(merged),encoding='utf-8')
    return index

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    result=build(args.root.resolve())
    print(f"Validated and compiled {result['record_count']} private chat records.")

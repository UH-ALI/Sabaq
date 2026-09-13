import json

chunks = [json.loads(l) for l in open('data/bio9/chunks.jsonl', encoding='utf-8') if l.strip()]
ch4 = [c for c in chunks if 'Chapter 4' in c['chapter']]
targets = [c for c in ch4 if c['chunk_id'] in ['bio9_ch04_c046','bio9_ch04_c047','bio9_ch04_c048','bio9_ch04_c049','bio9_ch04_c050','bio9_ch04_c051','bio9_ch04_c052']]

for c in targets:
    sep = '=' * 70
    print(sep)
    print(f"CHUNK ID : {c['chunk_id']}")
    print(f"HEADING  : {c['section_heading']}")
    print(f"PAGE     : {c['page_hint']}")
    print(f"TEXT:\n{c['text']}")
    print()

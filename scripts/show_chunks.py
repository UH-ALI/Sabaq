import json

targets = {"bio9_ch04_c000", "bio9_ch04_c026", "bio9_ch01_c020", "bio9_ch01_c021"}
found = {}

with open("data/bio9/chunks.jsonl", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj["chunk_id"] in targets:
            found[obj["chunk_id"]] = obj

for cid in ["bio9_ch01_c020", "bio9_ch01_c021", "bio9_ch04_c000", "bio9_ch04_c026"]:
    print("=" * 70)
    if cid in found:
        obj = found[cid]
        print(f"chunk_id    : {obj['chunk_id']}")
        print(f"section     : {obj['section_heading']}")
        print(f"page_hint   : {obj['page_hint']}")
        print(f"text length : {len(obj['text'])} chars")
        print(f"text:")
        print(obj["text"])
    else:
        print(f"NOT FOUND IN chunks.jsonl: {cid}")
    print()

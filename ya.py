import json, glob

# Gabungkan semua file JSON batch kamu
files = glob.glob("dataset.json")  # atau pakai "datasets_unsiq/*.json" jika banyak file
merged = []

for f in files:
    with open(f, encoding="utf-8") as infile:  # tambahkan encoding UTF-8
        merged.extend(json.load(infile))

# Tulis ke JSONL untuk training
with open("unsiq_full.jsonl", "w", encoding="utf-8") as f:
    for d in merged:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

print("✅ Dataset lengkap siap training: unsiq_full.jsonl")

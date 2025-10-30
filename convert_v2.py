import json

# Ganti dengan nama file teks kamu
input_file = "dataset_v2.txt"
output_file = "dataset_v2.json"

data = []
entry = {}

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("q:"):
            entry = {"Q": line[2:].strip()}
        elif line.lower().startswith("a:"):
            entry["A"] = line[2:].strip()
            data.append(entry)
            entry = {}

# Simpan ke file JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Konversi selesai! Total pasangan Q&A: {len(data)}")
print(f"💾 File tersimpan sebagai: {output_file}")

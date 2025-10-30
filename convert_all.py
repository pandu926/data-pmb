import json
import glob

# ==== KONFIGURASI ====
INPUT_PATTERN = "variations_q*_styled.json"   # otomatis baca semua variations_q1_styled.json ... q48
OUTPUT_FILE = "dataset_gemma_fix.json"

SYSTEM_PROMPT = (
    "Anda adalah asisten virtual untuk Penerimaan Mahasiswa Baru (PMB) di "
    "Universitas Sains Al-Qur'an (UNSIQ) Wonosobo.\n"
    "Tugas Anda adalah memberikan informasi yang akurat, jelas, dan membantu calon mahasiswa "
    "dalam proses pendaftaran.\n"
    "Jawab pertanyaan dengan ramah, informatif, dan profesional."
)

# ==== GABUNGKAN SEMUA FILE ====
all_files = sorted(glob.glob(INPUT_PATTERN))
merged = []

print(f"📂 Ditemukan {len(all_files)} file JSON...")

for path in all_files:
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                merged.append(data)
            elif isinstance(data, list):
                merged.extend(data)
            else:
                print(f"⚠️ Format tidak dikenali di {path}")
        except json.JSONDecodeError:
            print(f"❌ Gagal membaca {path} — bukan JSON valid.")

print(f"✅ Total item sebelum konversi: {len(merged)}")

# ==== KONVERSI KE FORMAT GEMMA ====
output = []

for item in merged:
    question = item.get("question", "").strip()
    answer = item.get("answer", "").strip()

    # format utama
    formatted = {
        "text": (
            f"<start_of_turn>system\n{SYSTEM_PROMPT}<end_of_turn>\n"
            f"<start_of_turn>user\n{question}<end_of_turn>\n"
            f"<start_of_turn>model\n{answer}<end_of_turn>"
        ),
        "question": question,
        "answer": answer
    }
    output.append(formatted)

    # variasi pertanyaan (jika ada)
    for v in item.get("variations", []):
        var_q = v.get("question", "").strip()
        formatted_var = {
            "text": (
                f"<start_of_turn>system\n{SYSTEM_PROMPT}<end_of_turn>\n"
                f"<start_of_turn>user\n{var_q}<end_of_turn>\n"
                f"<start_of_turn>model\n{answer}<end_of_turn>"
            ),
            "question": var_q,
            "answer": answer
        }
        output.append(formatted_var)

# ==== SIMPAN HASIL ====
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n🎉 Konversi selesai!")
print(f"📊 Total data siap training: {len(output)}")
print(f"💾 File tersimpan sebagai: {OUTPUT_FILE}")

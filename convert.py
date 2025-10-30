import json

# ==== KONFIGURASI ====
INPUT_FILE = "variations_q1_styled.json"
OUTPUT_FILE = "dataset_gemma.json"

SYSTEM_PROMPT = (
    "Anda adalah asisten virtual untuk Penerimaan Mahasiswa Baru (PMB) di "
    "Universitas Sains Al-Qur'an (UNSIQ) Wonosobo.\n"
    "Tugas Anda adalah memberikan informasi yang akurat, jelas, dan membantu calon mahasiswa "
    "dalam proses pendaftaran.\n"
    "Jawab pertanyaan dengan ramah, informatif, dan profesional."
)

HARDCODE_METADATA = {
    "topic": "PMB UNSIQ",
    "subtopic": "Informasi Umum"
}

# ==== BACA FILE INPUT ====
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Pastikan bentuk data selalu list
if isinstance(data, dict):
    data = [data]

output = []

# ==== PROSES KONVERSI ====
for item in data:
    question = item.get("question", "")
    answer = item.get("answer", "")

    # format utama
    formatted = {
        "text": (
            f"<start_of_turn>system\n{SYSTEM_PROMPT}<end_of_turn>\n"
            f"<start_of_turn>user\n{question}<end_of_turn>\n"
            f"<start_of_turn>model\n{answer}<end_of_turn>"
        ),
        "question": question,
        "answer": answer,
        "metadata": HARDCODE_METADATA
    }
    output.append(formatted)

    # tambahkan variasi (jika ada)
    for v in item.get("variations", []):
        var_q = v.get("question", "")
        formatted_var = {
            "text": (
                f"<start_of_turn>system\n{SYSTEM_PROMPT}<end_of_turn>\n"
                f"<start_of_turn>user\n{var_q}<end_of_turn>\n"
                f"<start_of_turn>model\n{answer}<end_of_turn>"
            ),
            "question": var_q,
            "answer": answer,
            "metadata": HARDCODE_METADATA
        }
        output.append(formatted_var)

# ==== SIMPAN HASIL ====
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ Konversi selesai! Total data: {len(output)}")
print(f"💾 File tersimpan sebagai: {OUTPUT_FILE}")

import json

# Baca file input
with open("dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

output = []
SYSTEM_PROMPT = (
    "Anda adalah asisten virtual untuk Penerimaan Mahasiswa Baru (PMB) di "
    "Universitas Sains Al-Qur'an (UNSIQ) Wonosobo.\n"
    "Tugas Anda adalah memberikan informasi yang akurat, jelas, dan membantu calon mahasiswa "
    "dalam proses pendaftaran.\n"
    "Jawab pertanyaan dengan ramah, informatif, dan profesional."
)

# Konversi format
for item in data:
    messages = item["messages"]
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    model_msg = next((m["content"] for m in messages if m["role"] == "model"), "")

    formatted = {
        "text": (
            f"<start_of_turn>system\n{SYSTEM_PROMPT}<end_of_turn>\n"
            f"<start_of_turn>user\n{user_msg}<end_of_turn>\n"
            f"<start_of_turn>model\n{model_msg}<end_of_turn>"
        ),
        "question": user_msg,
        "answer": model_msg,
        "metadata": item.get("metadata", {})
    }
    output.append(formatted)

# Simpan hasil ke file baru
with open("dataset_gemma.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("✅ Konversi selesai! File tersimpan sebagai dataset_gemma.json")

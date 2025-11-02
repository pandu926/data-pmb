"""
Script untuk validasi cosine similarity pasangan Q-A menggunakan sentence-transformers
Mengecek bahwa setiap pasangan Q-A memiliki:
1. Cosine similarity > 0.85
2. Tidak identik secara string
"""

import re
from typing import List, Tuple, Dict
from sentence_transformers import SentenceTransformer, util
import torch

def parse_qa_pairs(file_path: str) -> List[Tuple[str, str, int]]:
    """
    Parse file data_v3.txt untuk ekstrak pasangan Q-A
    Returns: List of (question, answer, line_number)
    """
    qa_pairs = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Cek apakah baris dimulai dengan "Q:"
        if line.startswith('Q:'):
            question = line[2:].strip()  # Hapus "Q:" prefix
            q_line_num = i + 1  # Line number (1-indexed)

            # Cari answer di baris berikutnya
            i += 1
            if i < len(lines):
                answer_line = lines[i].strip()
                if answer_line.startswith('A:'):
                    answer = answer_line[2:].strip()  # Hapus "A:" prefix
                    qa_pairs.append((question, answer, q_line_num))

        i += 1

    return qa_pairs

def calculate_similarity_stats(qa_pairs: List[Tuple[str, str, int]], model) -> Dict:
    """
    Hitung cosine similarity untuk semua pasangan Q-A
    """
    print(f"\nMemproses {len(qa_pairs)} pasangan Q-A...")
    print("Menghitung embeddings...")

    questions = [qa[0] for qa in qa_pairs]
    answers = [qa[1] for qa in qa_pairs]

    # Generate embeddings
    question_embeddings = model.encode(questions, convert_to_tensor=True, show_progress_bar=True)
    answer_embeddings = model.encode(answers, convert_to_tensor=True, show_progress_bar=True)

    # Hitung cosine similarity untuk setiap pasangan
    similarities = []
    for i in range(len(qa_pairs)):
        sim = util.cos_sim(question_embeddings[i], answer_embeddings[i]).item()
        similarities.append(sim)

    # Analisis hasil
    results = {
        'total_pairs': len(qa_pairs),
        'similarities': similarities,
        'min_similarity': min(similarities),
        'max_similarity': max(similarities),
        'avg_similarity': sum(similarities) / len(similarities),
        'pairs_above_085': sum(1 for s in similarities if s > 0.85),
        'pairs_below_085': [],
        'identical_pairs': [],
        'all_results': []
    }

    # Identifikasi pasangan bermasalah
    for i, (q, a, line_num) in enumerate(qa_pairs):
        sim = similarities[i]
        is_identical = (q.lower().strip() == a.lower().strip())

        result = {
            'line': line_num,
            'question': q,
            'answer': a,
            'similarity': sim,
            'is_identical': is_identical,
            'passes': sim > 0.85 and not is_identical
        }

        results['all_results'].append(result)

        if sim <= 0.85:
            results['pairs_below_085'].append(result)

        if is_identical:
            results['identical_pairs'].append(result)

    return results

def print_report(results: Dict):
    """
    Cetak laporan hasil validasi
    """
    print("\n" + "="*80)
    print("LAPORAN VALIDASI COSINE SIMILARITY PASANGAN Q-A")
    print("="*80)

    print(f"\n📊 STATISTIK UMUM:")
    print(f"  Total pasangan Q-A: {results['total_pairs']}")
    print(f"  Similarity rata-rata: {results['avg_similarity']:.4f}")
    print(f"  Similarity minimum: {results['min_similarity']:.4f}")
    print(f"  Similarity maksimum: {results['max_similarity']:.4f}")

    print(f"\n✅ VALIDASI:")
    print(f"  Pasangan dengan similarity > 0.85: {results['pairs_above_085']}/{results['total_pairs']} ({results['pairs_above_085']/results['total_pairs']*100:.1f}%)")
    print(f"  Pasangan dengan similarity ≤ 0.85: {len(results['pairs_below_085'])}")
    print(f"  Pasangan identik (string): {len(results['identical_pairs'])}")

    # Hitung pasangan yang LULUS validasi
    passed = sum(1 for r in results['all_results'] if r['passes'])
    print(f"\n🎯 HASIL AKHIR:")
    print(f"  Pasangan LULUS (similarity > 0.85 DAN tidak identik): {passed}/{results['total_pairs']} ({passed/results['total_pairs']*100:.1f}%)")

    # Detail pasangan dengan similarity rendah
    if results['pairs_below_085']:
        print(f"\n⚠️  PASANGAN DENGAN SIMILARITY ≤ 0.85 ({len(results['pairs_below_085'])} pasangan):")
        print("-" * 80)
        for i, item in enumerate(results['pairs_below_085'][:10], 1):  # Tampilkan max 10
            print(f"\n{i}. Baris {item['line']} | Similarity: {item['similarity']:.4f}")
            print(f"   Q: {item['question'][:100]}...")
            print(f"   A: {item['answer'][:100]}...")

        if len(results['pairs_below_085']) > 10:
            print(f"\n   ... dan {len(results['pairs_below_085']) - 10} pasangan lainnya")

    # Detail pasangan identik
    if results['identical_pairs']:
        print(f"\n❌ PASANGAN IDENTIK SECARA STRING ({len(results['identical_pairs'])} pasangan):")
        print("-" * 80)
        for i, item in enumerate(results['identical_pairs'][:5], 1):  # Tampilkan max 5
            print(f"\n{i}. Baris {item['line']}")
            print(f"   Q: {item['question'][:100]}...")
            print(f"   A: {item['answer'][:100]}...")

        if len(results['identical_pairs']) > 5:
            print(f"\n   ... dan {len(results['identical_pairs']) - 5} pasangan lainnya")

    # Distribusi similarity
    print(f"\n📈 DISTRIBUSI SIMILARITY:")
    ranges = [
        (0.0, 0.5, "Sangat rendah (< 0.5)"),
        (0.5, 0.7, "Rendah (0.5-0.7)"),
        (0.7, 0.85, "Sedang (0.7-0.85)"),
        (0.85, 0.95, "Tinggi (0.85-0.95)"),
        (0.95, 1.01, "Sangat tinggi (≥ 0.95)")
    ]

    for min_val, max_val, label in ranges:
        count = sum(1 for s in results['similarities'] if min_val <= s < max_val)
        percentage = count / results['total_pairs'] * 100
        bar = '█' * int(percentage / 2)
        print(f"  {label:25} {count:4d} ({percentage:5.1f}%) {bar}")

    print("\n" + "="*80)

def save_detailed_report(results: Dict, output_file: str):
    """
    Simpan laporan detail ke file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("LAPORAN DETAIL VALIDASI COSINE SIMILARITY\n")
        f.write("="*100 + "\n\n")

        # Pasangan dengan similarity rendah
        if results['pairs_below_085']:
            f.write(f"PASANGAN DENGAN SIMILARITY ≤ 0.85 ({len(results['pairs_below_085'])} pasangan)\n")
            f.write("-"*100 + "\n\n")
            for item in results['pairs_below_085']:
                f.write(f"Baris: {item['line']} | Similarity: {item['similarity']:.4f}\n")
                f.write(f"Q: {item['question']}\n")
                f.write(f"A: {item['answer']}\n")
                f.write("-"*100 + "\n")

        # Pasangan identik
        if results['identical_pairs']:
            f.write(f"\nPASANGAN IDENTIK SECARA STRING ({len(results['identical_pairs'])} pasangan)\n")
            f.write("-"*100 + "\n\n")
            for item in results['identical_pairs']:
                f.write(f"Baris: {item['line']}\n")
                f.write(f"Q: {item['question']}\n")
                f.write(f"A: {item['answer']}\n")
                f.write("-"*100 + "\n")

        # Semua hasil (sorted by similarity)
        f.write(f"\nSEMUA PASANGAN (SORTED BY SIMILARITY)\n")
        f.write("-"*100 + "\n\n")
        sorted_results = sorted(results['all_results'], key=lambda x: x['similarity'])
        for item in sorted_results:
            status = "✓ LULUS" if item['passes'] else "✗ GAGAL"
            f.write(f"[{status}] Baris: {item['line']} | Similarity: {item['similarity']:.4f}\n")
            f.write(f"Q: {item['question']}\n")
            f.write(f"A: {item['answer']}\n")
            f.write("-"*100 + "\n")

    print(f"\n💾 Laporan detail disimpan ke: {output_file}")

def main():
    # Path file
    data_file = "data_v3.txt"
    report_file = "similarity_report_detailed.txt"

    print("="*80)
    print("VALIDASI COSINE SIMILARITY PASANGAN Q-A")
    print("="*80)
    print(f"\nFile data: {data_file}")
    print(f"Kriteria validasi:")
    print(f"  1. Cosine similarity > 0.85")
    print(f"  2. Tidak identik secara string (Q ≠ A)")

    # Load model
    print(f"\n🔄 Loading model sentence-transformers...")
    model_name = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
    print(f"   Model: {model_name}")
    model = SentenceTransformer(model_name)
    print("   ✓ Model loaded")

    # Parse file
    print(f"\n📖 Parsing file {data_file}...")
    qa_pairs = parse_qa_pairs(data_file)
    print(f"   ✓ Ditemukan {len(qa_pairs)} pasangan Q-A")

    # Hitung similarity
    results = calculate_similarity_stats(qa_pairs, model)

    # Print laporan
    print_report(results)

    # Simpan laporan detail
    save_detailed_report(results, report_file)

    print(f"\n✅ Validasi selesai!")

if __name__ == "__main__":
    main()

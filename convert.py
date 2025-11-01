"""
Script untuk Format Dataset TANPA System Prompt (Optimal untuk Gemma)
Dengan handling untuk berbagai format input dan debugging
"""

import json
import os
from pathlib import Path


def format_clean_gemma(data):
    """
    Format dataset dengan chat template Gemma TANPA system prompt
    System prompt akan ditambahkan di training script, bukan per-sample
    
    Args:
        data: List of dict dengan keys 'Q' dan 'A' (atau 'question' dan 'answer')
    
    Returns:
        List of dict dengan key 'text' saja (clean)
    """
    
    formatted_data = []
    skipped = 0
    
    for idx, item in enumerate(data):
        # Deteksi berbagai format key
        question = None
        answer = None
        
        # Try different key formats
        if 'Q' in item:
            question = item['Q']
        elif 'question' in item:
            question = item['question']
        
        if 'A' in item:
            answer = item['A']
        elif 'answer' in item:
            answer = item['answer']
        
        # Clean whitespace
        if question:
            question = str(question).strip()
        if answer:
            answer = str(answer).strip()
        
        # Validasi: skip jika question atau answer kosong
        if not question or not answer or question == '' or answer == '':
            skipped += 1
            if skipped <= 5:  # Hanya print 5 pertama untuk debugging
                print(f"  ⚠️  Skipping sample #{idx}: Q='{question}' A='{answer}'")
            continue
        
        # Format CLEAN menggunakan Gemma chat template
        text = f"<start_of_turn>user\n{question}<end_of_turn>\n<start_of_turn>model\n{answer}<end_of_turn>"
        
        formatted_item = {
            "text": text
        }
        
        formatted_data.append(formatted_item)
    
    if skipped > 5:
        print(f"  ⚠️  ... and {skipped - 5} more skipped samples")
    
    return formatted_data, skipped


def validate_response_length(data):
    """
    Validasi panjang response dan beri warning jika terlalu pendek/panjang
    
    Args:
        data: Formatted dataset
    
    Returns:
        Statistics dict
    """
    if not data:
        return {
            "too_short": 0,
            "optimal": 0,
            "too_long": 0,
            "total": 0
        }
    
    stats = {
        "too_short": 0,  # < 30 tokens
        "optimal": 0,     # 30-200 tokens
        "too_long": 0,    # > 200 tokens
        "total": len(data)
    }
    
    for item in data:
        # Rough token estimation (1 token ≈ 4 chars untuk bahasa Indonesia)
        answer_start = item['text'].find("<start_of_turn>model\n") + len("<start_of_turn>model\n")
        answer_end = item['text'].find("<end_of_turn>", answer_start)
        answer = item['text'][answer_start:answer_end]
        
        estimated_tokens = len(answer) // 4
        
        if estimated_tokens < 30:
            stats["too_short"] += 1
        elif estimated_tokens <= 200:
            stats["optimal"] += 1
        else:
            stats["too_long"] += 1
    
    return stats


def inspect_dataset_structure(data, filename):
    """
    Debug function untuk inspect struktur dataset
    """
    print(f"\n🔍 Inspecting {filename}:")
    print(f"  • Type: {type(data)}")
    print(f"  • Length: {len(data) if isinstance(data, list) else 'N/A'}")
    
    if isinstance(data, list) and len(data) > 0:
        first_item = data[0]
        print(f"  • First item type: {type(first_item)}")
        print(f"  • Keys: {first_item.keys() if isinstance(first_item, dict) else 'Not a dict'}")
        print(f"  • Sample:")
        print(f"    {json.dumps(first_item, ensure_ascii=False, indent=4)[:200]}...")
    
    # Check for hidden characters
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        for key in data[0].keys():
            print(f"  • Key '{key}' -> repr: {repr(key)}")


def main():
    """Main function untuk format dataset"""
    
    print("="*80)
    print("📝 FORMATTING DATASET - CLEAN VERSION (Optimal for Gemma)")
    print("="*80)
    
    # Path files
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    
    # File yang akan diformat
    input_files = {
        "dataset_v2.json": "dataset_v2_formatted_clean.json",
        "pmb_dataset_augmented.json": "pmb_dataset_augmented_formatted_clean.json",
    }
    
    print(f"\n💡 Format Strategy:")
    print("-"*80)
    print("✅ System prompt REMOVED dari setiap sample (efisien)")
    print("✅ Hanya field 'text' yang disimpan (clean)")
    print("✅ System prompt akan ditambahkan di training script")
    print("✅ Response length validation included")
    print("-"*80)
    
    # Process each file
    all_stats = {}
    
    for input_file, output_file in input_files.items():
        input_path = data_dir / input_file
        output_path = data_dir / output_file
        
        if not input_path.exists():
            print(f"\n⏭️  Skipping {input_file} (file not found)")
            continue
        
        print(f"\n📖 Processing: {input_file}")
        
        # Load data
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ❌ Error loading {input_file}: {e}")
            continue
        
        print(f"  • Loaded {len(data)} samples")
        
        # Inspect structure for debugging
        inspect_dataset_structure(data, input_file)
        
        # Format data
        formatted_data, skipped = format_clean_gemma(data)
        
        print(f"\n  • Successfully formatted: {len(formatted_data)} samples")
        print(f"  • Skipped: {skipped} samples")
        
        if len(formatted_data) == 0:
            print(f"\n  ❌ ERROR: No samples formatted! Check dataset structure.")
            print(f"  💡 Expected format: [{{'Q': '...', 'A': '...'}}, ...]")
            continue
        
        # Validate response lengths
        stats = validate_response_length(formatted_data)
        all_stats[input_file] = stats
        
        print(f"\n  📊 Response Length Statistics:")
        print(f"     • Too Short (<30 tokens):  {stats['too_short']:4d} ({stats['too_short']/stats['total']*100:.1f}%)")
        print(f"     • Optimal (30-200 tokens): {stats['optimal']:4d} ({stats['optimal']/stats['total']*100:.1f}%)")
        print(f"     • Too Long (>200 tokens):  {stats['too_long']:4d} ({stats['too_long']/stats['total']*100:.1f}%)")
        
        # Warning jika banyak yang terlalu pendek
        if stats['too_short'] > stats['total'] * 0.3:
            print(f"\n  ⚠️  WARNING: {stats['too_short']/stats['total']*100:.1f}% responses terlalu pendek!")
            print(f"     Pertimbangkan untuk memperkaya jawaban (50-150 tokens optimal)")
        
        # Save formatted data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n  ✅ Saved to: {output_file}")
        
        # Show sample
        if formatted_data:
            print(f"\n  📝 Sample output:")
            print("  " + "-"*76)
            sample_text = formatted_data[0]['text']
            for line in sample_text.split('\n'):
                print(f"  {line}")
            print("  " + "-"*76)
    
    print("\n" + "="*80)
    
    if not all_stats:
        print("❌ NO FILES PROCESSED!")
        print("="*80)
        return
    
    print("✅ FORMATTING SELESAI!")
    print("="*80)
    
    # Summary
    print("\n📊 Overall Statistics:")
    for filename, stats in all_stats.items():
        print(f"\n  {filename}:")
        print(f"    • Total: {stats['total']}")
        if stats['total'] > 0:
            print(f"    • Optimal responses: {stats['optimal']/stats['total']*100:.1f}%")
    
    print("\n💡 Next Steps:")
    print("  1. Review dataset jika ada banyak response yang terlalu pendek")
    print("  2. Update configs/qlora_config.yaml:")
    print("     augmented_file: 'data/pmb_dataset_augmented_formatted_clean.json'")
    print("  3. System prompt akan ditambahkan otomatis saat training")
    print("  4. Run training:")
    print("     python3 scripts/train_v2.py")
    
    print("\n✨ Benefits dari format ini:")
    print("  • Dataset 30-40% lebih kecil (tanpa system prompt repetition)")
    print("  • Training lebih cepat")
    print("  • Model fokus pada Q&A mapping, bukan system prompt")
    print("  • Lebih mudah maintenance")


if __name__ == "__main__":
    main()

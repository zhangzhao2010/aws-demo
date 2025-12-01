#!/usr/bin/env python3
"""
Validate the split dataset files to ensure correct distribution and format.
"""

import json
from pathlib import Path
from collections import Counter


def validate_split_files():
    """Validate the split dataset files."""
    print("Split Dataset Validation Report")
    print("=" * 40)

    # File paths
    train_file = Path("train_dataset/train.jsonl")
    validation_file = Path("train_dataset/validation.jsonl")
    test_file = Path("train_dataset/test.jsonl")

    files_info = [
        ("Train", train_file, 300),
        ("Validation", validation_file, 60),
        ("Test", test_file, 240)
    ]

    total_records = 0
    all_categories = []

    for dataset_name, file_path, expected_count in files_info:
        print(f"\n{dataset_name} Dataset ({file_path}):")

        if not file_path.exists():
            print(f"  ❌ File not found!")
            continue

        # Load and count records
        records = []
        categories = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line.strip())
                        records.append(record)

                        # Extract category from assistant response
                        category = record['messages'][1]['content'][0]['text']
                        categories.append(category)

                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        print(f"  ⚠️  Error in line {line_num}: {e}")

        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            continue

        # Validate count
        actual_count = len(records)
        if actual_count == expected_count:
            print(f"  ✅ Record count: {actual_count}/{expected_count}")
        else:
            print(f"  ❌ Record count: {actual_count}/{expected_count}")

        # Validate category distribution
        category_counts = Counter(categories)
        print(f"  📊 Category distribution:")
        for category in ['neutral', 'porn', 'sexy']:
            count = category_counts.get(category, 0)
            print(f"     {category}: {count}")

        # Validate format
        valid_format = 0
        for record in records:
            try:
                if (record.get('schemaVersion') == 'bedrock-conversation-2024' and
                        'system' in record and 'messages' in record):
                    valid_format += 1
            except:
                pass

        print(f"  ✅ Valid format: {valid_format}/{actual_count}")

        total_records += actual_count
        all_categories.extend(categories)

    # Overall summary
    print(f"\n" + "=" * 40)
    print(f"Overall Summary:")
    print(f"Total records: {total_records}")
    print(f"Expected total: 600")

    overall_category_counts = Counter(all_categories)
    print(f"Overall category distribution:")
    for category in ['neutral', 'porn', 'sexy']:
        count = overall_category_counts.get(category, 0)
        print(f"  {category}: {count}")

    # Expected distribution check
    expected_dist = {
        'neutral': 200,  # 100 + 20 + 80
        'porn': 200,     # 100 + 20 + 80
        'sexy': 200      # 100 + 20 + 80
    }

    print(f"\nExpected vs Actual Distribution:")
    all_correct = True
    for category, expected in expected_dist.items():
        actual = overall_category_counts.get(category, 0)
        status = "✅" if actual == expected else "❌"
        print(f"  {category}: {actual}/{expected} {status}")
        if actual != expected:
            all_correct = False

    if all_correct and total_records == 600:
        print(f"\n🎉 All validations passed! Dataset split is correct.")
    else:
        print(f"\n⚠️  Some validations failed. Please check the results above.")


if __name__ == "__main__":
    validate_split_files()

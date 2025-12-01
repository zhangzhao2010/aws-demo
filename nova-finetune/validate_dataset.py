#!/usr/bin/env python3
"""
Validate the generated JSONL dataset files.
"""

import json
from pathlib import Path


def validate_jsonl_file(file_path: Path):
    """Validate a JSONL file."""
    print(f"\nValidating {file_path.name}...")

    valid_count = 0
    total_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                total_count += 1
                try:
                    # Parse JSON
                    data = json.loads(line.strip())

                    # Basic validation
                    required_fields = ['schemaVersion', 'system', 'messages']
                    if all(field in data for field in required_fields):
                        if data['schemaVersion'] == 'bedrock-conversation-2024':
                            valid_count += 1
                        else:
                            print(f"  Line {line_num}: Invalid schema version")
                    else:
                        print(f"  Line {line_num}: Missing required fields")

                except json.JSONDecodeError as e:
                    print(f"  Line {line_num}: JSON decode error - {e}")

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, 0

    print(f"  Valid samples: {valid_count}/{total_count}")
    return valid_count, total_count


def main():
    """Main validation function."""
    print("Dataset Validation Report")
    print("=" * 30)

    jsonl_files = list(Path('.').glob('*.jsonl'))

    if not jsonl_files:
        print("No JSONL files found!")
        return

    total_valid = 0
    total_samples = 0

    for file_path in sorted(jsonl_files):
        valid, total = validate_jsonl_file(file_path)
        total_valid += valid
        total_samples += total

    print(f"\nOverall Summary:")
    print(f"Total valid samples: {total_valid}/{total_samples}")
    print(f"Success rate: {(total_valid/total_samples)*100:.1f}%")


if __name__ == "__main__":
    main()

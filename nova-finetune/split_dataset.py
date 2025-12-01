#!/usr/bin/env python3
"""
Split dataset into train/validation/test sets with specified sampling strategy.

Sampling Strategy:
1. From each category file (neutral.jsonl, porn.jsonl, sexy.jsonl):
   - Randomly sample 200 records
2. From each 200 records:
   - Take 100 for train.jsonl (total: 300 records)
   - Take 20 from remaining 100 for validation.jsonl (total: 60 records)  
   - Take remaining 80 for test.jsonl (total: 240 records)
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Configuration
CATEGORIES = ["neutral", "porn", "sexy"]
SAMPLE_SIZE_PER_CATEGORY = 1000
TRAIN_SIZE_PER_CATEGORY = 700
VALIDATION_SIZE_PER_CATEGORY = 50
# TEST_SIZE_PER_CATEGORY = 80 (remaining)

RANDOM_SEED = 42


class DatasetSplitter:
    """Split dataset into train/validation/test sets."""

    def __init__(self, random_seed: int = RANDOM_SEED):
        """
        Initialize dataset splitter.

        Args:
            random_seed: Random seed for reproducible results
        """
        self.random_seed = random_seed
        random.seed(random_seed)

    def load_jsonl_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Load data from JSONL file.

        Args:
            file_path: Path to JSONL file

        Returns:
            List of JSON records
        """
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line.strip())
                        data.append(record)
                    except json.JSONDecodeError as e:
                        print(
                            f"Error parsing line {line_num} in {file_path}: {e}")
                        continue

            print(f"Loaded {len(data)} records from {file_path}")
            return data

        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

    def sample_records(self, records: List[Dict[str, Any]], sample_size: int) -> List[Dict[str, Any]]:
        """
        Randomly sample records from a list.

        Args:
            records: List of records to sample from
            sample_size: Number of records to sample

        Returns:
            List of sampled records
        """
        if len(records) < sample_size:
            print(
                f"Warning: Requested {sample_size} samples but only {len(records)} available")
            return records.copy()

        return random.sample(records, sample_size)

    def split_records(self, records: List[Dict[str, Any]],
                      train_size: int, validation_size: int) -> tuple:
        """
        Split records into train, validation, and test sets.

        Args:
            records: List of records to split
            train_size: Number of records for training
            validation_size: Number of records for validation

        Returns:
            Tuple of (train_records, validation_records, test_records)
        """
        if len(records) < train_size + validation_size:
            raise ValueError(
                f"Not enough records to split: need {train_size + validation_size}, got {len(records)}")

        # Shuffle records for random distribution
        shuffled_records = records.copy()
        random.shuffle(shuffled_records)

        # Split records
        train_records = shuffled_records[:train_size]
        validation_records = shuffled_records[train_size:train_size + validation_size]
        test_records = shuffled_records[train_size + validation_size:]

        return train_records, validation_records, test_records

    def write_jsonl_file(self, records: List[Dict[str, Any]], output_path: Path):
        """
        Write records to JSONL file.

        Args:
            records: List of records to write
            output_path: Output file path
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for record in records:
                    json_line = json.dumps(record, ensure_ascii=False)
                    f.write(json_line + '\n')

            print(
                f"Successfully wrote {len(records)} records to {output_path}")

        except Exception as e:
            print(f"Error writing to {output_path}: {e}")

    def process_category(self, category: str) -> tuple:
        """
        Process a single category file and return split data.

        Args:
            category: Category name (neutral, porn, sexy)

        Returns:
            Tuple of (train_records, validation_records, test_records)
        """
        print(f"\nProcessing category: {category}")

        # Load category data
        input_file = Path(f"{category}.jsonl")
        if not input_file.exists():
            print(f"Error: {input_file} not found")
            return [], [], []

        all_records = self.load_jsonl_file(input_file)
        if not all_records:
            return [], [], []

        # Step 1: Sample 200 records from category
        sampled_records = self.sample_records(
            all_records, SAMPLE_SIZE_PER_CATEGORY)
        print(f"Sampled {len(sampled_records)} records from {category}")

        # Step 2: Split sampled records
        train_records, validation_records, test_records = self.split_records(
            sampled_records,
            TRAIN_SIZE_PER_CATEGORY,
            VALIDATION_SIZE_PER_CATEGORY
        )

        print(
            f"Split {category}: train={len(train_records)}, validation={len(validation_records)}, test={len(test_records)}")

        return train_records, validation_records, test_records

    def split_all_datasets(self, output_dir: Path = Path(".")):
        """
        Split all category datasets into train/validation/test sets.

        Args:
            output_dir: Output directory for split files
        """
        print("Dataset Splitting Process")
        print("=" * 40)
        print(f"Random seed: {self.random_seed}")
        print(f"Sample size per category: {SAMPLE_SIZE_PER_CATEGORY}")
        print(f"Train size per category: {TRAIN_SIZE_PER_CATEGORY}")
        print(f"Validation size per category: {VALIDATION_SIZE_PER_CATEGORY}")
        print(
            f"Test size per category: {SAMPLE_SIZE_PER_CATEGORY - TRAIN_SIZE_PER_CATEGORY - VALIDATION_SIZE_PER_CATEGORY}")

        # Initialize combined datasets
        all_train_records = []
        all_validation_records = []
        all_test_records = []

        # Process each category
        for category in CATEGORIES:
            train_records, validation_records, test_records = self.process_category(
                category)

            # Add to combined datasets
            all_train_records.extend(train_records)
            all_validation_records.extend(validation_records)
            all_test_records.extend(test_records)

        # Shuffle combined datasets for better distribution
        random.shuffle(all_train_records)
        random.shuffle(all_validation_records)
        random.shuffle(all_test_records)

        # Write output files
        print(f"\nWriting combined datasets...")

        train_file = output_dir / "train.jsonl"
        validation_file = output_dir / "validation.jsonl"
        test_file = output_dir / "test.jsonl"

        self.write_jsonl_file(all_train_records, train_file)
        self.write_jsonl_file(all_validation_records, validation_file)
        self.write_jsonl_file(all_test_records, test_file)

        # Print summary
        print(f"\nDataset Split Summary:")
        print(f"=" * 30)
        print(f"Train set: {len(all_train_records)} records")
        print(f"Validation set: {len(all_validation_records)} records")
        print(f"Test set: {len(all_test_records)} records")
        print(
            f"Total: {len(all_train_records) + len(all_validation_records) + len(all_test_records)} records")

        # Verify category distribution
        self.verify_category_distribution(
            all_train_records, all_validation_records, all_test_records)

    def verify_category_distribution(self, train_records: List[Dict],
                                     validation_records: List[Dict],
                                     test_records: List[Dict]):
        """
        Verify category distribution in split datasets.

        Args:
            train_records: Training records
            validation_records: Validation records
            test_records: Test records
        """
        print(f"\nCategory Distribution Verification:")
        print(f"=" * 40)

        def count_categories(records: List[Dict], dataset_name: str):
            category_counts = {category: 0 for category in CATEGORIES}

            for record in records:
                try:
                    # Extract category from assistant response
                    assistant_content = record['messages'][1]['content'][0]['text']
                    if assistant_content in category_counts:
                        category_counts[assistant_content] += 1
                except (KeyError, IndexError):
                    print(
                        f"Warning: Could not extract category from record in {dataset_name}")

            print(f"{dataset_name}:")
            for category, count in category_counts.items():
                print(f"  {category}: {count}")

            return category_counts

        train_counts = count_categories(train_records, "Train")
        val_counts = count_categories(validation_records, "Validation")
        test_counts = count_categories(test_records, "Test")

        # Check if distribution is as expected
        expected_train = TRAIN_SIZE_PER_CATEGORY
        expected_val = VALIDATION_SIZE_PER_CATEGORY
        expected_test = SAMPLE_SIZE_PER_CATEGORY - \
            TRAIN_SIZE_PER_CATEGORY - VALIDATION_SIZE_PER_CATEGORY

        print(f"\nExpected vs Actual:")
        print(
            f"Train - Expected: {expected_train} per category, Actual: {list(train_counts.values())}")
        print(
            f"Validation - Expected: {expected_val} per category, Actual: {list(val_counts.values())}")
        print(
            f"Test - Expected: {expected_test} per category, Actual: {list(test_counts.values())}")


def main():
    """Main function to run dataset splitting."""
    parser = argparse.ArgumentParser(
        description="Split dataset into train/validation/test sets")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED,
                        help=f"Random seed for reproducible results (default: {RANDOM_SEED})")
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Output directory for split files (default: current directory)")

    args = parser.parse_args()

    # Initialize splitter
    splitter = DatasetSplitter(random_seed=args.seed)

    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Split datasets
    splitter.split_all_datasets(output_dir)


if __name__ == "__main__":
    main()

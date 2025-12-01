#!/usr/bin/env python3
"""
Test script for evaluating Amazon Nova Pro model accuracy on image classification.
This script reads test data, queries the Nova Pro model, and calculates accuracy.
"""

import boto3
import json
import time
import re
from typing import Dict, List, Tuple
from pathlib import Path

# Configuration
PRO_MODEL_ID = "us.amazon.nova-pro-v1:0"
REGION_NAME = "us-east-1"
TEST_FILE = "train_dataset_full/test_micro.jsonl"
RESULT_FILE = "train_dataset_full/nova_pro_test_result_ft.jsonl"
BUCKET_OWNER = "xxxx"


class NovaProTester:
    def __init__(self):
        """Initialize the Bedrock client."""
        self.client = boto3.client("bedrock-runtime", region_name=REGION_NAME)
        self.results = []

    def load_test_data(self, file_path: str) -> List[Dict]:
        """Load test data from JSONL file."""
        test_data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    test_data.append(json.loads(line.strip()))
        print(f"Loaded {len(test_data)} test samples")
        return test_data

    def extract_image_info(self, test_item: Dict) -> Tuple[str, str, str]:
        """Extract image URI, expected label, and user prompt from test item."""
        # Get expected label from assistant response
        expected_label = test_item["messages"][1]["content"][0]["text"].strip(
        ).lower()

        # Get image URI from user message
        user_content = test_item["messages"][0]["content"]
        image_uri = None
        user_prompt = None
        image_format = "jpeg"

        for content in user_content:
            if "image" in content:
                image_uri = content["image"]["source"]["s3Location"]["uri"]
                image_format = content["image"]["format"]
            elif "text" in content:
                user_prompt = content["text"]

        return image_format, image_uri, expected_label, user_prompt

    def query_nova_pro(self, image_format: str, image_uri: str, user_prompt: str, system_prompt: str) -> str:
        """Query Nova Pro model with image and prompt."""
        # Extract bucket owner from the original test data format
        bucket_owner = BUCKET_OWNER  # From the test data

        messages = [{
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": image_format,
                        "source": {
                            "s3Location": {
                                "uri": image_uri,
                                "bucketOwner": bucket_owner
                            }
                        }
                    }
                },
                {"text": user_prompt}
            ]
        }]

        inf_params = {
            "maxTokens": 50,
            "topP": 0.1,
            "temperature": 0.1
        }

        try:
            response = self.client.converse(
                modelId=PRO_MODEL_ID,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig=inf_params
            )

            response_text = response["output"]["message"]["content"][0]["text"].strip(
            ).lower()
            return response_text

        except Exception as e:
            print(f"Error querying model: {e}")
            return "error"

    def normalize_prediction(self, prediction: str) -> str:
        """Normalize model prediction to standard categories."""
        prediction = prediction.lower().strip()

        # Direct matches
        if prediction in ["porn", "sexy", "neutral"]:
            return prediction

        # Pattern matching for common variations
        if re.search(r'\bporn\b|\bpornographic\b', prediction):
            return "porn"
        elif re.search(r'\bsexy\b|\bsexual\b', prediction):
            return "sexy"
        elif re.search(r'\bneutral\b|\bnon-sexual\b|\bnot sexual\b', prediction):
            return "neutral"

        # If no clear match, return the original prediction
        return prediction

    def run_test(self, test_data: List[Dict]) -> List[Dict]:
        """Run the test on all samples."""
        results = []
        total_samples = len(test_data)

        for i, test_item in enumerate(test_data):
            print(f"Processing sample {i+1}/{total_samples}...")

            # Extract information
            image_format, image_uri, expected_label, user_prompt = self.extract_image_info(
                test_item)
            system_prompt = test_item["system"][0]["text"]

            # Query model
            raw_prediction = self.query_nova_pro(
                image_format, image_uri, user_prompt, system_prompt)
            normalized_prediction = self.normalize_prediction(raw_prediction)

            # Store result
            result = {
                "image_uri": image_uri,
                "user_prompt": user_prompt,
                "expected_label": expected_label,
                "raw_prediction": raw_prediction,
                "normalized_prediction": normalized_prediction,
                "correct": normalized_prediction == expected_label
            }

            results.append(result)

            # Add small delay to avoid rate limiting
            time.sleep(0.4)

            # Print progress every 10 samples
            if (i + 1) % 10 == 0:
                correct_so_far = sum(1 for r in results if r["correct"])
                accuracy_so_far = correct_so_far / len(results) * 100
                print(
                    f"Progress: {i+1}/{total_samples}, Accuracy so far: {accuracy_so_far:.2f}%")

        return results

    def save_results(self, results: List[Dict], file_path: str):
        """Save results to JSONL file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        print(f"Results saved to {file_path}")

    def calculate_accuracy(self, results: List[Dict]) -> Dict:
        """Calculate overall and per-category accuracy."""
        total_samples = len(results)
        correct_predictions = sum(1 for r in results if r["correct"])
        overall_accuracy = correct_predictions / total_samples * 100

        # Per-category accuracy
        categories = ["porn", "sexy", "neutral"]
        category_stats = {}

        for category in categories:
            category_results = [
                r for r in results if r["expected_label"] == category]
            if category_results:
                category_correct = sum(
                    1 for r in category_results if r["correct"])
                category_accuracy = category_correct / \
                    len(category_results) * 100
                category_stats[category] = {
                    "total": len(category_results),
                    "correct": category_correct,
                    "accuracy": category_accuracy
                }

        # Confusion matrix
        confusion_matrix = {}
        for expected in categories:
            confusion_matrix[expected] = {}
            for predicted in categories:
                count = sum(1 for r in results
                            if r["expected_label"] == expected and r["normalized_prediction"] == predicted)
                confusion_matrix[expected][predicted] = count

        return {
            "overall_accuracy": overall_accuracy,
            "total_samples": total_samples,
            "correct_predictions": correct_predictions,
            "category_stats": category_stats,
            "confusion_matrix": confusion_matrix
        }

    def print_results(self, accuracy_stats: Dict):
        """Print formatted results."""
        print("\n" + "="*60)
        print("NOVA PRO MODEL ACCURACY RESULTS")
        print("="*60)

        print(f"\nOverall Accuracy: {accuracy_stats['overall_accuracy']:.2f}%")
        print(
            f"Correct Predictions: {accuracy_stats['correct_predictions']}/{accuracy_stats['total_samples']}")

        print("\nPer-Category Results:")
        print("-" * 40)
        for category, stats in accuracy_stats['category_stats'].items():
            print(
                f"{category.upper():>8}: {stats['accuracy']:>6.2f}% ({stats['correct']:>3}/{stats['total']:>3})")

        print("\nConfusion Matrix:")
        print("-" * 40)
        categories = ["porn", "sexy", "neutral"]
        print(f"{'Actual':>8} | {'Predicted':>20}")
        print(f"{'':>8} | {'porn':>6} {'sexy':>6} {'neutral':>8}")
        print("-" * 40)

        for actual in categories:
            row = f"{actual:>8} |"
            for predicted in categories:
                count = accuracy_stats['confusion_matrix'][actual][predicted]
                row += f"{count:>6}"
            print(row)


def main():
    """Main function to run the test."""
    print("Starting Nova Pro Model Accuracy Test...")

    # Initialize tester
    tester = NovaProTester()

    # Load test data
    test_data = tester.load_test_data(TEST_FILE)

    # Run test
    print("Running inference on test samples...")
    results = tester.run_test(test_data)

    # Save results
    tester.save_results(results, RESULT_FILE)

    # Calculate and print accuracy
    accuracy_stats = tester.calculate_accuracy(results)
    tester.print_results(accuracy_stats)

    # Save accuracy stats
    stats_file = "train_dataset/accuracy_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(accuracy_stats, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed accuracy statistics saved to {stats_file}")


if __name__ == "__main__":
    main()

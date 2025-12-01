#!/usr/bin/env python3
"""
Sample test script for Nova Pro model - tests only first 5 samples for quick verification.
"""

import boto3
import json
import re
from typing import Dict, List, Tuple

# Configuration
PRO_MODEL_ID = "us.amazon.nova-pro-v1:0"
REGION_NAME = "us-east-1"
TEST_FILE = "train_dataset_full/test.jsonl"
SAMPLE_SIZE = 10  # Test only first 5 samples
BUCKET_OWNER = "xxxx"


def load_sample_data(file_path: str, sample_size: int) -> List[Dict]:
    """Load first N samples from test data."""
    test_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= sample_size:
                break
            if line.strip():
                test_data.append(json.loads(line.strip()))
    print(f"Loaded {len(test_data)} sample(s) for testing")
    return test_data


def extract_image_info(test_item: Dict) -> Tuple[str, str, str]:
    """Extract image URI, expected label, and user prompt."""
    expected_label = test_item["messages"][1]["content"][0]["text"].strip(
    ).lower()

    user_content = test_item["messages"][0]["content"]
    image_uri = None
    user_prompt = None
    image_format = 'jpeg'

    for content in user_content:
        if "image" in content:
            image_uri = content["image"]["source"]["s3Location"]["uri"]
            image_format = content["image"]["format"]
        elif "text" in content:
            user_prompt = content["text"]

    return image_format, image_uri, expected_label, user_prompt


def query_nova_pro(client, image_format: str,  image_uri: str, user_prompt: str, system_prompt: str) -> str:
    """Query Nova Pro model."""
    bucket_owner = BUCKET_OWNER

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
        response = client.converse(
            modelId=PRO_MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig=inf_params
        )

        return response["output"]["message"]["content"][0]["text"].strip()

    except Exception as e:
        print(f"Error querying model: {e}")
        return f"ERROR: {str(e)}"


def normalize_prediction(prediction: str) -> str:
    """Normalize model prediction."""
    prediction = prediction.lower().strip()

    if prediction in ["porn", "sexy", "neutral"]:
        return prediction

    if re.search(r'\bporn\b|\bpornographic\b', prediction):
        return "porn"
    elif re.search(r'\bsexy\b|\bsexual\b', prediction):
        return "sexy"
    elif re.search(r'\bneutral\b|\bnon-sexual\b|\bnot sexual\b', prediction):
        return "neutral"

    return prediction


def main():
    """Run sample test."""
    print("Running Nova Pro Sample Test...")

    # Initialize client
    client = boto3.client("bedrock-runtime", region_name=REGION_NAME)

    # Load sample data
    test_data = load_sample_data(TEST_FILE, SAMPLE_SIZE)

    results = []
    for i, test_item in enumerate(test_data):
        print(f"\nTesting sample {i+1}/{len(test_data)}...")

        # Extract info
        image_format, image_uri, expected_label, user_prompt = extract_image_info(
            test_item)
        system_prompt = test_item["system"][0]["text"]

        print(f"Expected: {expected_label}")
        print(f"Image: {image_uri.split('/')[-1]}")

        # Query model
        raw_prediction = query_nova_pro(
            client, image_format, image_uri, user_prompt, system_prompt)
        normalized_prediction = normalize_prediction(raw_prediction)

        print(f"Raw prediction: {raw_prediction}")
        print(f"Normalized: {normalized_prediction}")

        is_correct = normalized_prediction == expected_label
        print(f"Correct: {is_correct}")

        results.append({
            "expected": expected_label,
            "predicted": normalized_prediction,
            "correct": is_correct
        })

    # Summary
    correct_count = sum(1 for r in results if r["correct"])
    accuracy = correct_count / len(results) * 100

    print(f"\n{'='*50}")
    print(f"SAMPLE TEST RESULTS")
    print(f"{'='*50}")
    print(f"Accuracy: {accuracy:.1f}% ({correct_count}/{len(results)})")

    if accuracy == 100:
        print("✅ Perfect! Ready to run full test.")
    else:
        print("⚠️  Some predictions were incorrect. Check the results above.")


if __name__ == "__main__":
    main()

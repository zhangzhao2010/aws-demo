#!/usr/bin/env python3
"""
Generate training dataset from S3 stored images for Nova content moderation fine-tuning.
Creates separate JSONL files for each category (neutral.jsonl, sexy.jsonl, porn.jsonl).
"""

import json
import random
import boto3
from typing import List, Dict, Any
import os
from pathlib import Path

# Configuration
BUCKET_NAME = "sagemaker-us-east-1-xxxxx"
BUCKET_OWNER_ID = "xxxxx"
S3_PREFIX = "nova-finetune"
CATEGORIES = ["neutral", "porn", "sexy"]
OUTPUT_DIR = Path(".")

# System message for all samples
SYSTEM_MESSAGE = "You are a content moderation classifier that determines if an image is porn, sexy, or neutral."

# User prompt variations
USER_PROMPTS = [
    "Classify this image into one of the categories: porn, sexy, neutral. Reply only porn, sexy, or neutral, do not provide any other description",
    "Please identify the content category of this image: porn / sexy / neutral.  Reply only porn, sexy, or neutral, do not provide any other description",
    "Is this image pornographic, sexual, or neutral?  Reply only porn, sexy, or neutral, do not provide any other description",
    "Determine the content moderation category for this image.  Reply only porn, sexy, or neutral, do not provide any other description",
    "What category does this image belong to: porn, sexy, or neutral?  Reply only porn, sexy, or neutral, do not provide any other description"
]


class DatasetGenerator:
    """Generate Bedrock conversation format dataset from S3 images."""

    def __init__(self, bucket_name: str, bucket_owner_id: str, s3_prefix: str):
        """
        Initialize dataset generator.

        Args:
            bucket_name: S3 bucket name
            bucket_owner_id: AWS account ID that owns the bucket
            s3_prefix: S3 prefix for images
        """
        self.bucket_name = bucket_name
        self.bucket_owner_id = bucket_owner_id
        self.s3_prefix = s3_prefix
        self.s3_client = boto3.client('s3')

    def list_s3_images(self, category: str) -> List[str]:
        """
        List all images in S3 for a specific category.

        Args:
            category: Image category (neutral, porn, sexy)

        Returns:
            List of S3 object keys
        """
        prefix = f"{self.s3_prefix}/{category}/"

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' not in response:
                print(f"No objects found for category: {category}")
                return []

            # Filter for image files and extract keys
            image_keys = []
            for obj in response['Contents']:
                key = obj['Key']
                if key.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_keys.append(key)

            print(f"Found {len(image_keys)} images for category: {category}")
            return image_keys

        except Exception as e:
            print(f"Error listing S3 objects for {category}: {e}")
            return []

    def create_conversation_sample(self, s3_key: str, category: str) -> Dict[str, Any]:
        """
        Create a single conversation sample in Bedrock format.

        Args:
            s3_key: S3 object key for the image
            category: Image category

        Returns:
            Dictionary in Bedrock conversation format
        """
        # Construct S3 URI
        s3_uri = f"s3://{self.bucket_name}/{s3_key}"

        # Determine image format from file extension
        if s3_key.lower().endswith('.png'):
            image_format = "png"
        else:
            image_format = "jpeg"

        # Randomly select a user prompt
        user_prompt = random.choice(USER_PROMPTS)

        # Create the conversation sample
        sample = {
            "schemaVersion": "bedrock-conversation-2024",
            "system": [
                {
                    "text": SYSTEM_MESSAGE
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": image_format,
                                "source": {
                                    "s3Location": {
                                        "uri": s3_uri,
                                        "bucketOwner": self.bucket_owner_id
                                    }
                                }
                            }
                        },
                        {
                            "text": user_prompt
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "text": category
                        }
                    ]
                }
            ]
        }

        return sample

    def generate_category_dataset(self, category: str) -> List[Dict[str, Any]]:
        """
        Generate dataset for a specific category.

        Args:
            category: Image category

        Returns:
            List of conversation samples
        """
        print(f"\nGenerating dataset for category: {category}")

        # Get list of images from S3
        image_keys = self.list_s3_images(category)

        if not image_keys:
            print(f"No images found for category: {category}")
            return []

        # Generate conversation samples
        samples = []
        for i, s3_key in enumerate(image_keys):
            try:
                sample = self.create_conversation_sample(s3_key, category)
                samples.append(sample)

                # Progress indicator
                if (i + 1) % 100 == 0:
                    print(
                        f"Generated {i + 1}/{len(image_keys)} samples for {category}")

            except Exception as e:
                print(f"Error creating sample for {s3_key}: {e}")
                continue

        print(f"Successfully generated {len(samples)} samples for {category}")
        return samples

    def write_jsonl_file(self, samples: List[Dict[str, Any]], output_file: Path):
        """
        Write samples to JSONL file.

        Args:
            samples: List of conversation samples
            output_file: Output file path
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for sample in samples:
                    json_line = json.dumps(sample, ensure_ascii=False)
                    f.write(json_line + '\n')

            print(
                f"Successfully wrote {len(samples)} samples to {output_file}")

        except Exception as e:
            print(f"Error writing to {output_file}: {e}")

    def generate_all_datasets(self, output_dir: Path):
        """
        Generate datasets for all categories.

        Args:
            output_dir: Output directory for JSONL files
        """
        print("Starting dataset generation...")
        print(f"Bucket: {self.bucket_name}")
        print(f"Prefix: {self.s3_prefix}")
        print(f"Output directory: {output_dir}")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        total_samples = 0

        for category in CATEGORIES:
            # Generate samples for this category
            samples = self.generate_category_dataset(category)

            if samples:
                # Write to JSONL file
                output_file = output_dir / f"{category}.jsonl"
                self.write_jsonl_file(samples, output_file)
                total_samples += len(samples)
            else:
                print(f"No samples generated for {category}")

        print(f"\nDataset generation completed!")
        print(f"Total samples generated: {total_samples}")
        print(f"Output files saved in: {output_dir}")


def main():
    """Main function to run dataset generation."""
    print("Nova Content Moderation Dataset Generator")
    print("=" * 50)

    # Initialize generator
    generator = DatasetGenerator(
        bucket_name=BUCKET_NAME,
        bucket_owner_id=BUCKET_OWNER_ID,
        s3_prefix=S3_PREFIX
    )

    # Generate all datasets
    generator.generate_all_datasets(OUTPUT_DIR)


if __name__ == "__main__":
    main()

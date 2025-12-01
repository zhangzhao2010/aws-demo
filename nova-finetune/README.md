# Nova Dataset Generator

Generate training datasets from S3 stored images for Nova content moderation fine-tuning.

## Features

- Automatically lists images from S3 bucket by category
- Generates Bedrock conversation format (bedrock-conversation-2024)
- Creates separate JSONL files for each category
- Random prompt variation for better model generalization
- Progress tracking and error handling

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials (one of the following):
```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## Usage

Run the script to generate datasets:
```bash
python generate_dataset.py
```

This will create three JSONL files:
- `neutral.jsonl` - Neutral content samples
- `porn.jsonl` - Pornographic content samples  
- `sexy.jsonl` - Sexual/suggestive content samples

## Configuration

The script uses the following default configuration:
- **Bucket**: `sagemaker-us-east-1-xxxx`
- **Bucket Owner**: `xxxx`
- **S3 Prefix**: `nova-finetune`
- **Categories**: `neutral`, `porn`, `sexy`

To modify these settings, edit the constants at the top of `generate_dataset.py`.

## Output Format

Each line in the JSONL files contains a conversation sample in Bedrock format:

```json
{
  "schemaVersion": "bedrock-conversation-2024",
  "system": [
    {
      "text": "You are a content moderation classifier that determines if an image is porn, sexy, or neutral."
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "text": "Classify this image into one of the categories: porn, sexy, neutral."
        },
        {
          "image": {
            "format": "jpg",
            "source": {
              "s3Location": {
                "uri": "s3://sagemaker-us-east-1-xxxx/nova-finetune/sexy/sexy_0001.jpg",
                "bucketOwner": "xxxx"
              }
            }
          }
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "text": "sexy"
        }
      ]
    }
  ]
}
```

## Expected Output

For 1000 images per category, you should get:
- `neutral.jsonl`: ~1000 samples
- `porn.jsonl`: ~1000 samples
- `sexy.jsonl`: ~1000 samples
- **Total**: ~3000 training samples
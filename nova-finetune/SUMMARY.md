# Dataset Generation & Splitting Summary

## 🎯 Task Completed Successfully

Generated and split training datasets for Nova content moderation fine-tuning from S3 stored images.

## 📊 Results

### Original Dataset Generation
- **Total Samples**: 3,000
- **Categories**: 3 (neutral, porn, sexy)
- **Samples per Category**: 1,000
- **Format**: Bedrock conversation format (bedrock-conversation-2024)
- **Validation**: 100% success rate

### Dataset Splitting
- **Sampling Strategy**: 200 samples per category (600 total)
- **Train Set**: 300 samples (100 per category)
- **Validation Set**: 60 samples (20 per category)
- **Test Set**: 240 samples (80 per category)
- **Random Seed**: 42 (for reproducible results)

## 📁 Generated Files

```
nova_dataset_new/
├── neutral.jsonl          # 1,000 neutral content samples
├── porn.jsonl            # 1,000 pornographic content samples
├── sexy.jsonl            # 1,000 sexual/suggestive content samples
├── train_dataset/        # Split dataset directory
│   ├── train.jsonl       # 300 training samples
│   ├── validation.jsonl  # 60 validation samples
│   └── test.jsonl        # 240 test samples
├── generate_dataset.py   # Main generation script
├── split_dataset.py      # Dataset splitting script
├── validate_dataset.py   # Original dataset validation
├── validate_split.py     # Split dataset validation
├── requirements.txt      # Dependencies
├── README.md            # Usage instructions
└── SUMMARY.md           # This summary
```

## ✅ Key Features Implemented

1. **S3 Integration**: Automatically lists and processes images from S3 bucket
2. **Format Compliance**: Generates proper Bedrock conversation format
3. **Prompt Variation**: Uses 5 different user prompt templates for better generalization
4. **Error Handling**: Robust error handling and progress tracking
5. **Validation**: Built-in validation to ensure data quality

## 🔧 Configuration Used

- **S3 Bucket**: `sagemaker-us-east-1-xxxx`
- **Bucket Owner**: `xxxxx`
- **S3 Prefix**: `nova-finetune`
- **Image Format**: Auto-detected (JPG/PNG)
- **System Message**: Content moderation classifier role

## 📋 Sample Format

Each JSONL line contains a conversation sample:

```json
{
  "schemaVersion": "bedrock-conversation-2024",
  "system": [{"text": "You are a content moderation classifier..."}],
  "messages": [
    {
      "role": "user",
      "content": [
        {"text": "Classify this image..."},
        {"image": {"format": "jpg", "source": {"s3Location": {...}}}}
      ]
    },
    {
      "role": "assistant", 
      "content": [{"text": "category_label"}]
    }
  ]
}
```

## 🚀 Ready for Fine-tuning

The split dataset files in `train_dataset/` are ready to be used for Amazon Nova model fine-tuning in Amazon Bedrock:

- **train.jsonl**: 300 samples for model training
- **validation.jsonl**: 60 samples for validation during training
- **test.jsonl**: 240 samples for final model evaluation

## 📈 Dataset Split Strategy

1. **Random Sampling**: From each category (neutral, porn, sexy), randomly selected 200 samples
2. **Stratified Splitting**: 
   - Train: 100 samples per category (300 total)
   - Validation: 20 samples per category (60 total)  
   - Test: 80 samples per category (240 total)
3. **Balanced Distribution**: Each split maintains equal representation across all categories
4. **Reproducible**: Uses random seed 42 for consistent results

## 📈 Next Steps

1. Upload the split JSONL files (`train_dataset/*.jsonl`) to your training environment
2. Configure Bedrock fine-tuning job with:
   - Training data: `train.jsonl`
   - Validation data: `validation.jsonl`
3. Monitor training progress and adjust hyperparameters as needed
4. Evaluate final model performance using `test.jsonl`
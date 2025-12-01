# Nova 数据集生成器

为 Nova 内容审核微调生成来自 S3 存储图像的训练数据集。

## 功能特性

- 自动按类别列出 S3 存储桶中的图像
- 生成 Bedrock 对话格式 (bedrock-conversation-2024)
- 为每个类别创建单独的 JSONL 文件
- 随机提示变化以提高模型泛化能力
- 进度跟踪和错误处理

## 环境设置

1. 安装依赖项：
```bash
pip install -r requirements.txt
```

2. 配置 AWS 凭证（以下任选一种方式）：
```bash
# 使用 AWS CLI
aws configure

# 或设置环境变量
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## 使用方法

运行脚本生成数据集：
```bash
python generate_dataset.py
```

这将创建三个 JSONL 文件：
- `neutral.jsonl` - 中性内容样本
- `porn.jsonl` - 色情内容样本  
- `sexy.jsonl` - 性感/暗示性内容样本

## 配置参数

脚本使用以下默认配置：
- **存储桶**: `sagemaker-us-east-1-096331270838`
- **存储桶所有者**: `096331270838`
- **S3 前缀**: `nova-finetune`
- **类别**: `neutral`, `porn`, `sexy`

要修改这些设置，请编辑 `generate_dataset.py` 顶部的常量。

## 输出格式

JSONL 文件中的每一行都包含 Bedrock 格式的对话样本：

```json
{
  "schemaVersion": "bedrock-conversation-2024",
  "system": [
    {
      "text": "你是一个内容审核分类器，用于判断图像是色情、性感还是中性内容。"
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "text": "将此图像分类为以下类别之一：色情、性感、中性。"
        },
        {
          "image": {
            "format": "jpg",
            "source": {
              "s3Location": {
                "uri": "s3://sagemaker-us-east-1-096331270838/nova-finetune/sexy/sexy_0001.jpg",
                "bucketOwner": "096331270838"
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
          "text": "性感"
        }
      ]
    }
  ]
}
```

## 预期输出

对于每个类别 1000 张图像，您应该得到：
- `neutral.jsonl`: ~1000 个样本
- `porn.jsonl`: ~1000 个样本
- `sexy.jsonl`: ~1000 个样本
- **总计**: ~3000 个训练样本
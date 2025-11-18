# SES 事件转发 Lambda 函数

## 📋 项目简介

这是一个用于接收 AWS SNS 推送的 SES 邮件事件，并转发到自建 API 的 Lambda 函数。

## 🏗️ 架构说明

```
SES 事件 → SNS Topic → Lambda (VPC) → NAT Gateway → 自建 API
```

该 Lambda 函数部署在 VPC 私有子网中，通过 NAT Gateway 以固定出口 IP 访问自建 API。

## 📦 项目结构

```
lambda/
├── src/
│   ├── handler.py       # Lambda 主函数
│   └── config.py        # 环境变量配置
├── tests/
│   └── test_event.json  # 测试事件示例
├── requirements.txt     # Python 依赖
├── README.md           # 项目说明
└── DEPLOYMENT.md       # 部署指南
```

## 🔧 环境变量配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `API_ENDPOINT` | ✅ | - | 自建 API 地址（如：https://your-api.com/ses/webhook） |
| `API_TIMEOUT` | ❌ | 5 | API 请求超时时间（秒） |
| `LOG_LEVEL` | ❌ | INFO | 日志级别（DEBUG/INFO/WARNING/ERROR） |

## 🚀 快速开始

### 1. 安装依赖

```bash
cd lambda
pip install -r requirements.txt -t ./package
```

### 2. 本地测试

```bash
# 设置环境变量
export API_ENDPOINT="https://your-api.com/ses/webhook"
export API_TIMEOUT="5"

# 使用测试事件
python -c "
import json
from src.handler import lambda_handler

with open('tests/test_event.json') as f:
    event = json.load(f)
    result = lambda_handler(event, None)
    print(result)
"
```

## 📝 支持的消息类型

### SNS 消息类型
- ✅ **SubscriptionConfirmation** - 自动确认 SNS 订阅
- ✅ **Notification** - 处理 SES 事件通知
- ✅ **UnsubscribeConfirmation** - 取消订阅确认（仅记录）

### SES 事件类型
- ✅ **Delivery** - 邮件投递成功
- ✅ **Bounce** - 邮件退信
- ✅ **Complaint** - 用户投诉
- ✅ **Reject** - SES 拒信
- ✅ **Open** - 用户打开邮件（需启用跟踪）
- ✅ **Click** - 用户点击链接（需启用跟踪）

## 🔍 日志示例

**成功转发**：
```
[INFO] API Endpoint: https://api.example.com/ses/webhook, Timeout: 5s
[INFO] 收到 SES 事件 - Type: Delivery, MessageId: abc123, Timestamp: 2025-01-18T10:30:00Z
[INFO] 成功转发事件到 API - Type: Delivery, Status: 200
```

**失败重试**：
```
[ERROR] API 请求超时 (5s): HTTPSConnectionPool(host='api.example.com', port=443)
[ERROR] Lambda 处理失败: ...
```

## ⚠️ 注意事项

1. **SNS 自动重试**：Lambda 失败时会抛出异常，SNS 会自动重试
2. **VPC 配置**：必须部署在私有子网，通过 NAT Gateway 出网
3. **超时设置**：建议 Lambda 超时时间设置为至少 10 秒
4. **Python 版本**：需要 Python 3.13 运行时

## 📚 相关文档

- [部署指南](./DEPLOYMENT.md) - 详细的部署步骤
- [AWS Lambda 文档](https://docs.aws.amazon.com/lambda/)
- [AWS SES 事件格式](https://docs.aws.amazon.com/ses/latest/dg/event-publishing-retrieving-sns.html)

## 🆘 故障排查

### Lambda 超时
- 检查 VPC 路由表是否正确配置
- 确认 NAT Gateway 是否正常运行
- 增加 Lambda 超时时间

### API 请求失败
- 验证 `API_ENDPOINT` 环境变量是否正确
- 检查自建 API 的白名单配置
- 查看 CloudWatch Logs 获取详细错误信息

### SNS 无法触发 Lambda
- 确认 SNS Subscription 状态为 "Confirmed"
- 检查 Lambda 执行角色是否有 SNS 调用权限

## 📄 许可证

MIT License

# Lambda 部署指南

## 📦 部署前准备

### 1. VPC 配置检查

确保已完成以下 VPC 配置：

- ✅ VPC 已创建
- ✅ 私有子网已创建（至少 2 个，跨 AZ）
- ✅ NAT Gateway 已创建并分配 Elastic IP
- ✅ 私有子网路由表指向 NAT Gateway

### 2. 获取 NAT Gateway 出口 IP

```bash
# 在 AWS Console 查看 NAT Gateway 的 Elastic IP
# 或使用 CLI
aws ec2 describe-nat-gateways --nat-gateway-ids nat-xxxxxx
```

记录该 IP，需要添加到自建 API 的白名单中。

## 🚀 部署步骤

### 方式 1：手动打包部署（推荐用于测试）

#### 1. 创建部署包

```bash
cd lambda

# 创建打包目录
mkdir -p package

# 安装依赖到 package 目录
pip install -r requirements.txt -t ./package

# 复制源代码
cp -r src/* package/

# 打包
cd package
zip -r ../lambda-deployment.zip .
cd ..
```

#### 2. 创建 Lambda 函数

```bash
# 创建 IAM 角色（如果还没有）
aws iam create-role \
  --role-name ses-lambda-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# 附加基本执行权限
aws iam attach-role-policy \
  --role-name ses-lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# 附加 VPC 执行权限
aws iam attach-role-policy \
  --role-name ses-lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

# 创建 Lambda 函数
aws lambda create-function \
  --function-name ses-event-forwarder \
  --runtime python3.13 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/ses-lambda-execution-role \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 10 \
  --memory-size 256 \
  --environment Variables="{API_ENDPOINT=https://your-api.com/ses/webhook,API_TIMEOUT=5}" \
  --vpc-config SubnetIds=subnet-xxx,subnet-yyy,SecurityGroupIds=sg-zzz
```

#### 3. 更新 Lambda 代码

```bash
# 重新打包
cd package
zip -r ../lambda-deployment.zip .
cd ..

# 更新函数代码
aws lambda update-function-code \
  --function-name ses-event-forwarder \
  --zip-file fileb://lambda-deployment.zip
```

### 方式 2：使用 AWS CDK 部署（推荐用于生产）

参考项目根目录的 CDK 配置文件。

### 方式 3：使用 AWS SAM 部署

创建 `template.yaml`：

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  ApiEndpoint:
    Type: String
    Description: 自建 API 地址
  VpcId:
    Type: AWS::EC2::VPC::Id
  PrivateSubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
  SecurityGroupId:
    Type: AWS::EC2::SecurityGroup::Id

Resources:
  SesEventForwarderFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: ses-event-forwarder
      Runtime: python3.13
      Handler: handler.lambda_handler
      CodeUri: ./package
      Timeout: 10
      MemorySize: 256
      VpcConfig:
        SubnetIds: !Ref PrivateSubnetIds
        SecurityGroupIds:
          - !Ref SecurityGroupId
      Environment:
        Variables:
          API_ENDPOINT: !Ref ApiEndpoint
          API_TIMEOUT: "5"
      Policies:
        - VPCAccessPolicy: {}

Outputs:
  FunctionArn:
    Value: !GetAtt SesEventForwarderFunction.Arn
```

部署：

```bash
sam build
sam deploy --guided
```

## 🔗 配置 SNS 订阅

### 1. 添加 Lambda 订阅到 SNS Topic

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:ses-events-topic \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:ses-event-forwarder
```

### 2. 授权 SNS 调用 Lambda

```bash
aws lambda add-permission \
  --function-name ses-event-forwarder \
  --statement-id sns-invoke \
  --action lambda:InvokeFunction \
  --principal sns.amazonaws.com \
  --source-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:ses-events-topic
```

## ✅ 验证部署

### 1. 测试 Lambda 函数

创建测试事件 `test_event.json`：

```json
{
  "Records": [
    {
      "Sns": {
        "MessageId": "test-123",
        "Timestamp": "2025-01-18T10:00:00Z",
        "Message": "{\"notificationType\":\"Delivery\",\"mail\":{\"messageId\":\"test-mail-123\",\"timestamp\":\"2025-01-18T09:59:00Z\"},\"delivery\":{\"timestamp\":\"2025-01-18T10:00:00Z\",\"recipients\":[\"test@example.com\"]}}"
      }
    }
  ]
}
```

使用 AWS CLI 测试：

```bash
aws lambda invoke \
  --function-name ses-event-forwarder \
  --payload file://tests/test_event.json \
  response.json

# 查看响应
cat response.json
```

### 2. 查看日志

```bash
# 获取最新日志
aws logs tail /aws/lambda/ses-event-forwarder --follow

# 或在 AWS Console 查看
# Lambda → ses-event-forwarder → Monitor → View logs in CloudWatch
```

### 3. 发送测试邮件

通过 SES 发送测试邮件，观察事件是否成功转发到自建 API。

## 🔧 配置更新

### 更新环境变量

```bash
aws lambda update-function-configuration \
  --function-name ses-event-forwarder \
  --environment Variables="{API_ENDPOINT=https://new-api.com/webhook,API_TIMEOUT=10}"
```

### 更新超时时间

```bash
aws lambda update-function-configuration \
  --function-name ses-event-forwarder \
  --timeout 15
```

## 📊 监控配置

### 创建 CloudWatch 告警

```bash
# 错误率告警
aws cloudwatch put-metric-alarm \
  --alarm-name ses-lambda-errors \
  --alarm-description "Lambda 执行错误" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=ses-event-forwarder

# 超时告警
aws cloudwatch put-metric-alarm \
  --alarm-name ses-lambda-timeouts \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 9000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=ses-event-forwarder
```

## 🛡️ 安全配置

### Security Group 配置

Lambda 的 Security Group 需要允许出站 HTTPS：

```bash
# 允许出站 443 端口
aws ec2 authorize-security-group-egress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### IAM 最小权限原则

Lambda 执行角色应该包含：
- `AWSLambdaBasicExecutionRole` - CloudWatch Logs 写入
- `AWSLambdaVPCAccessExecutionRole` - VPC 网络接口管理

## 🚨 故障排查

### 问题 1：Lambda 超时
**症状**：CloudWatch 显示 "Task timed out after 10.00 seconds"

**解决方案**：
1. 增加超时时间到 15-30 秒
2. 检查 NAT Gateway 状态
3. 确认私有子网路由表配置

### 问题 2：无法访问外网
**症状**：`[Errno -3] Temporary failure in name resolution`

**解决方案**：
1. 确认 Lambda 在私有子网
2. 检查路由表：`0.0.0.0/0` → NAT Gateway
3. 检查 NAT Gateway 是否在公有子网
4. 确认公有子网路由到 Internet Gateway

### 问题 3：API 返回 403
**症状**：API 返回 "IP not whitelisted"

**解决方案**：
1. 确认 NAT Gateway 的 Elastic IP
2. 将该 IP 添加到自建 API 白名单
3. 在自建 API 端记录请求来源 IP 进行验证

## 📚 相关资源

- [AWS Lambda VPC 配置](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)
- [SNS Lambda 订阅](https://docs.aws.amazon.com/sns/latest/dg/sns-lambda-as-subscriber.html)
- [SES 事件发布](https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-using-event-publishing.html)

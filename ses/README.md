# AWS SES REST API 邮件发送程序

这是一个使用Java调用AWS SES REST API发送邮件的示例程序。该程序使用JDK 8，并使用AWS签名V4认证机制。

## 文件结构

- `AWSSESSender.java` - 主程序类
- `AWSSESRequest.java` - AWS SES请求实现类
- `config.properties` - 配置文件
- `build_and_run.sh` - 编译和运行脚本

## 功能特点

1. **发送电子邮件** - 使用AWS SES API发送文本格式的电子邮件
2. **邮箱验证** - 支持验证发件人和收件人邮箱
3. **AWS签名V4认证** - 完整实现AWS SIG4签名算法
4. **详细调试输出** - 提供详细的请求和响应信息，方便排错
5. **命令行参数支持** - 支持通过命令行指定参数

## 使用方法

### 1. 配置

创建 `config.properties` 文件，填入您的AWS凭证和邮件信息：

```properties
# AWS认证信息
aws.accessKey=YOUR_ACCESS_KEY
aws.secretKey=YOUR_SECRET_KEY
aws.region=us-east-1  # 默认使用us-east-1区域

# 邮件信息
email.from=sender@example.com  # 发件人邮箱，必须是AWS SES验证过的邮箱
email.to=recipient@example.com  # 收件人邮箱
email.subject=Test email from AWS SES  # 邮件主题
email.body=This is a test email sent using AWS SES REST API  # 邮件内容
```

### 2. 编译

使用提供的脚本编译：

```bash
./build_and_run.sh
```

或者手动编译：

```bash
javac AWSSESSender.java AWSSESRequest.java
```

### 3. 运行

程序支持以下命令行操作：

#### 发送邮件

默认模式，使用配置文件中的设置发送邮件：

```bash
java AWSSESSender
```

或者指定发件人、收件人和主题：

```bash
java AWSSESSender send sender@example.com recipient@example.com "邮件主题"
```

#### 验证邮箱

在使用SES发送邮件之前，必须先验证邮箱地址：

```bash
java AWSSESSender verify your@email.com
```

验证成功后，AWS会向指定邮箱发送一封包含验证链接的邮件，点击链接完成验证。

## AWS SES沙箱模式说明

新创建的AWS账户的SES服务默认处于沙箱模式，有以下限制：

1. 只能向已验证的邮箱地址发送邮件
2. 每24小时最多发送200封邮件
3. 每秒最多发送1封邮件

要移出沙箱模式，需要向AWS提交申请，请参阅AWS文档。

## 排错指南

如果遇到`InvalidClientTokenId`错误，可能的原因包括：

1. **访问密钥无效** - 确保您的ACCESS KEY和SECRET KEY正确无误
2. **区域不匹配** - 确保指定的区域与您的SES服务区域相符
3. **IAM权限不足** - 确保IAM用户/角色有`ses:SendEmail`和`ses:VerifyEmailIdentity`权限
4. **账户未激活SES** - 确保您的AWS账户已在指定区域激活了SES服务

如遇其他错误，程序会提供详细的调试信息，包括：
- 请求参数和签名计算过程
- HTTP状态码和响应头
- AWS错误代码和错误消息
- 针对常见错误的诊断提示

## 高级配置

如果您需要调整程序的高级配置，可以编辑代码中的以下部分：

- `AWSSESRequest.java`中的`DEBUG_MODE`变量控制调试输出
- 请求超时和重试机制可以在HTTP连接部分调整
- 如需添加HTML格式邮件支持，需要修改请求参数结构
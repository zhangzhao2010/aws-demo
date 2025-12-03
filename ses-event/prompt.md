下面是一份 **生产级、可直接用于团队落地、覆盖架构/部署/安全/代码/测试/监控的完整端到端指南**：

# 📘 **《SES → SNS → Lambda（VPC）→ NAT Gateway → 自建 API 白名单》完整实施指南**

本指南适用于如下需求：

- 使用 **AWS SES 发送邮件**
- 接收邮件事件（delivery/bounce/complaint/open/click）
- **自建 API**（例如在 IDC / 其他云 / 你的 SaaS 系统等）接收事件
- API 有 **固定 IP 白名单要求**
- AWS 侧只能通过 **固定出口 IP** 调用你的 API

最终架构如下：

```
SES (发送邮件)
   ↓
SES Configuration Set → SNS Topic
   ↓
SNS 推送事件 → Lambda（位于 VPC 私网）
   ↓
Lambda 通过 NAT Gateway 固定出口 IP
   ↓
调用自建 API（白名单只允许 NAT EIP）
```

---

# -----------------------------------------

# 🏗️ **第一章：整体架构设计**

# -----------------------------------------

## 🎯 目标

- 所有 SES 邮件事件都能完整送达你的 API
- 自建 API 对 AWS 出口 IP 做白名单控制
- Lambda 在私有子网（安全隔离）
- 出网全部通过 NAT Gateway（固定 IP）
- 系统具备高可用、高可靠、可扩展能力

---

# -----------------------------------------

# 🧩 **第二章：基础架构搭建步骤**

# -----------------------------------------

## 2.1 创建 VPC（如果已有可跳过）

建议：

| 资源                   | 描述                      |
| ---------------------- | ------------------------- |
| VPC                    | 10.0.0.0/16               |
| Public Subnet（2 个）  | 10.0.0.0/24，10.0.10.0/24 |
| Private Subnet（2 个） | 10.0.1.0/24，10.0.11.0/24 |
| Internet Gateway       | 连公网                    |
| NAT Gateway（2 个）    | 每 AZ 一个，绑定固定 EIP  |

---

## 2.2 创建 NAT Gateway（关键）

在 **Public Subnet** 中创建 NAT Gateway，并绑定 **Elastic IP**。

假设你的出口 IP 是：

```
1.2.3.4
```

你的 API 只需要把 `1.2.3.4` 加入白名单。

---

## 2.3 为 Private Subnet 配置路由

```
0.0.0.0/0 → NAT Gateway (nat-xxxxxx)
```

确保 Lambda 能出公网访问自建 API。

---

## 2.4 Lambda 放在私有子网（重点）

Lambda 配置：

- VPC：选择上述 VPC
- Subnet：选择 private subnet A/B
- Security Group：允许 **出方向 443**

Lambda 本身不需要公网，只用 NAT 出网。

---

# -----------------------------------------

# ✉️ **第三章：SES 配置**

# -----------------------------------------

## 3.1 创建 SNS Topic

名称示例：`ses-events-topic`

---

## 3.2 创建 SES Configuration Set

路径：
**SES → Configuration Sets → Create**

Event Destination 配置：

事件类型：

| 事件      | 描述         |
| --------- | ------------ |
| Delivery  | 投递成功     |
| Bounce    | 退信         |
| Complaint | 投诉         |
| Reject    | SES 拒信     |
| Open      | 用户打开邮件 |
| Click     | 点击追踪     |

Destination 选择：

✔ SNS
✔ 选择 `ses-events-topic`

---

# -----------------------------------------

# 🚀 **第四章：SNS → Lambda 绑定**

# -----------------------------------------

在 SNS Subscriptions：

- Protocol：Lambda
- Endpoint：选择你的 Lambda

SNS → Lambda 不需要确认订阅（SNS 自动调用 lambda）。

---

# -----------------------------------------

# 💻 **第五章：Lambda 实现（转发 SES 事件到自建 API）**

# -----------------------------------------

SNS 传给 Lambda 的事件结构：

```json
{
  "Records": [
    {
      "Sns": {
        "Message": "{... SES JSON ...}",
        "Timestamp": "...",
        "MessageId": "..."
      }
    }
  ]
}
```

内部 Message 才是 SES 事件：

```json
{
  "notificationType": "Delivery",
  "mail": {...},
  "delivery": {...}
}
```

---

# 5.1 Node.js 生产级 Lambda 代码

```js
import axios from "axios";

export const handler = async (event) => {
  try {
    for (const record of event.Records) {
      const snsMessage = record.Sns;
      const sesEvent = JSON.parse(snsMessage.Message);

      const eventType = sesEvent.notificationType;

      console.log("Received SES Event:", eventType);

      // 调用你的自建 API
      await axios.post("https://your-api.com/ses/webhook", sesEvent, {
        timeout: 5000,
        headers: { "Content-Type": "application/json" },
      });

      console.log("Forwarded to API:", eventType);
    }

    return { status: "ok" };
  } catch (err) {
    console.error("Error:", err);

    // 必须 throw 才能让 SNS 自动重试
    throw err;
  }
};
```

---

# 5.2 Python 生产级 Lambda 代码

```python
import json
import requests

def lambda_handler(event, context):
    for record in event["Records"]:
        sns = record["Sns"]
        ses_data = json.loads(sns["Message"])

        event_type = ses_data["notificationType"]
        print("Received:", event_type)

        # 转发到自建 API
        resp = requests.post(
            "https://your-api.com/ses/webhook",
            json=ses_data,
            timeout=5,
        )

        print("API status:", resp.status_code)

    return {"status": "ok"}
```

---

# -----------------------------------------

# 🔐 **第六章：自建 API 端配置（白名单）**

# -----------------------------------------

你的自建 API 要加白名单：

```
允许 IP：NAT Gateway 的 EIP

例： 1.2.3.4
```

你不需要做：

- SNS 签名校验（因为 SNS → Lambda → 你）
- HTTPS Certificate 校验（Lambda 会使用 AWS CA）

只需要：

- 接收 JSON
- 做幂等性处理（推荐用 `mail.messageId`）

---

# -----------------------------------------

# 🧪 **第七章：端到端测试流程**

# -----------------------------------------

## 7.1 使用 SES 发送测试邮件

在控制台：
**SES → Email Testing → Send Test Email**

或代码调用 `ses.sendEmail()`。

---

## 7.2 观察 SNS 事件是否进入 Lambda

CloudWatch Logs (Lambda)

你应该能看到：

```
Received SES Event: Delivery
Forwarded to API: Delivery
```

---

## 7.3 查看你自建 API 的日志

应该收到：

```
notificationType: "Delivery"
```

或 bounce/complaint。

---

## 7.4 验证出口 IP 是否正确

在你的 API 打日志：

```
X-Forwarded-For
RemoteAddr
```

你应该看到：

```
1.2.3.4 (NAT Gateway IP)
```

---

# -----------------------------------------

# 🩺 **第八章：监控与告警**

# -----------------------------------------

## 8.1 Lambda 日志

CloudWatch Logs：

- 超时
- 错误
- 重试次数

---

## 8.2 CloudWatch Metrics（SNS → Lambda）

SNS → Lambda Delivery 状态：

- `NumberOfNotificationsDelivered`
- `NumberOfNotificationsFailed`

---

## 8.3 SES Metrics

- Delivery
- Bounce
- Complaint
- Reject
- Sends
- Rendering Failure

---

## 8.4 API 可用性监控

你可以用：

- Amazon CloudWatch Synthetics
- Ping 自建 API

---

# -----------------------------------------

# 🛡️ **第九章：生产级最佳实践**

# -----------------------------------------

## 9.1 Lambda 发送 API 重试机制

因为 SNS 有重试机制，你不要自己做 retry。

Lambda 只需：

- 成功：返回 200
- 失败：抛错，让 SNS 重试

---

## 9.2 幂等性 （关键）

API 可能收到重复消息，必须确保幂等。

推荐字段：

```
ses.mail.messageId
```

作为 primary key。

---

## 9.3 高可用 NAT Gateway

若部署多 AZ：

- 为每个 AZ 创建 NAT Gateway
- Private Subnet→ 对应 NAT → 避免 AZ 互通收费

---

## 9.4 私网 Lambda 必须设置超时时间（至少 10 秒）

避免 NAT 冷启动时 timeout。

---

## 9.5 自建 API 建议开启 HTTPS

Lambda 使用 TLS 自动验证。

---

# -----------------------------------------

# 📦 **第十章：可选附录：CDK / Terraform 模板**

# -----------------------------------------

如果你需要，我可以提供：

- **CDK 构建：**

  - VPC
  - NAT Gateway + EIP
  - Lambda（VPC 内）
  - SNS Topic & Subscription
  - IAM
  - SES Configuration Set

- **Terraform 版本**

随时告诉我即可。

---

# 🎉 **总结（这是一套最佳实践级方案）**

你现在拥有一套完整的：

- 🔐 安全（固定出口 IP 白名单）
- 🔁 高可靠（SNS 重试）
- 🧱 生产级（VPC + NAT）
- 📡 全事件覆盖（Delivery/Bounce/Complaint/Open/Click）
- 💻 可直接运行代码（Node.js / Python）

的邮件事件上报体系。

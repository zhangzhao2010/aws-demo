# SES Webhook API（Java 8）

## 📋 项目简介

这是一个使用 **原生 Servlet + Jetty** 构建的轻量级 API 服务器，用于接收 AWS Lambda 转发的 SES 邮件事件。

## 🏗️ 技术栈

- **Java 8** - 运行环境
- **Servlet 3.1** - 原生 Servlet API
- **Jetty 9.4** - 嵌入式 Web 服务器
- **Gson** - JSON 解析
- **SLF4J + Logback** - 日志框架
- **Maven** - 构建工具

## 📦 项目结构

```
java/
├── src/
│   └── main/
│       ├── java/com/example/sesapi/
│       │   ├── SesWebhookServer.java      # 主启动类
│       │   ├── SesWebhookServlet.java     # Servlet 处理类
│       └── resources/
│           ├── application.properties      # 应用配置
│           └── logback.xml                # 日志配置
├── pom.xml                                # Maven 配置
├── README.md                              # 项目说明
└── DEPLOYMENT.md                          # 部署指南
```

## 🔧 配置说明

### application.properties

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `server.port` | 8080 | 服务器端口 |
| `server.host` | 0.0.0.0 | 监听地址（0.0.0.0 表示所有网卡） |
| `log.file.path` | ./logs/ses-events.log | 日志文件路径 |
| `log.max.history` | 30 | 日志保留天数（logback.xml 配置） |
| `log.max.file.size` | 100MB | 单个日志文件最大大小（logback.xml 配置） |

### 日志输出

系统会生成两个日志文件：

1. **logs/ses-events.log** - 包含所有系统日志
2. **logs/ses-events-only.log** - 只包含 SES 事件的 JSON 数据（方便分析）

## 🚀 快速开始

### 1. 环境要求

- Java 8+
- Maven 3.6+

### 2. 编译打包

```bash
cd java
mvn clean package
```

打包后会生成：
- `target/ses-webhook-api-1.0.0.jar` - 可执行 JAR 文件

### 3. 运行服务器

```bash
java -jar target/ses-webhook-api-1.0.0.jar
```

**指定配置文件运行**：

```bash
java -Dconfig.file=/path/to/application.properties \
     -jar target/ses-webhook-api-1.0.0.jar
```

**自定义端口运行**：

```bash
# 方式 1：修改配置文件
# 方式 2：覆盖系统属性
java -Dserver.port=9090 -jar target/ses-webhook-api-1.0.0.jar
```

### 4. 验证服务

**检查服务状态**：

```bash
curl http://localhost:8080/ses/webhook
# 响应：SES Webhook API is running. Please use POST method.
```

**测试接收事件**：

```bash
curl -X POST http://localhost:8080/ses/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "notificationType": "Delivery",
    "mail": {
      "messageId": "test-123",
      "timestamp": "2025-01-18T10:00:00Z"
    }
  }'
```

## 📝 API 接口说明

### POST /ses/webhook

接收 SES 事件数据。

**请求头**：
- `Content-Type: application/json`

**请求体**（Lambda 转发的 SES 事件）：

```json
{
  "notificationType": "Delivery",
  "mail": {
    "messageId": "abc123",
    "timestamp": "2025-01-18T10:00:00Z",
    "source": "sender@example.com",
    "destination": ["recipient@example.com"]
  },
  "delivery": {
    "timestamp": "2025-01-18T10:00:01Z",
    "recipients": ["recipient@example.com"],
    "smtpResponse": "250 2.0.0 OK"
  }
}
```

**成功响应**（200 OK）：

```json
{
  "status": "success",
  "message": "SES event received",
  "eventType": "Delivery",
  "messageId": "abc123"
}
```

**失败响应**（400 Bad Request）：

```json
{
  "status": "error",
  "message": "请求体为空"
}
```

## 🔍 日志示例

### 控制台日志

```
2025-01-18 10:00:00.456 [main] INFO  c.e.sesapi.SesWebhookServer - ✅ SES Webhook API 启动成功！
2025-01-18 10:00:10.789 [qtp123-56] INFO  c.e.sesapi.SesWebhookServlet - 收到 SES 事件 - Type: Delivery, MessageId: abc123, RemoteIP: 1.2.3.4
```

### 事件日志文件（logs/ses-events-only.log）

```
2025-01-18 10:00:10.789 | SES Event [Delivery] - MessageId: abc123
{
  "notificationType": "Delivery",
  "mail": {
    "messageId": "abc123",
    "timestamp": "2025-01-18T10:00:00Z",
    ...
  },
  "delivery": {
    ...
  }
}
```

## ⚠️ 注意事项

1. **日志文件权限**：确保应用有权限创建 `./logs` 目录
2. **端口占用**：确保 8080 端口未被占用（或修改配置）
3. **生产环境部署**：建议使用 systemd/supervisor 管理进程
4. **网络安全**：生产环境建议配置防火墙或使用 Nginx 反向代理进行访问控制

## 🐛 故障排查

### 问题 1：启动失败 - 端口被占用

```
java.net.BindException: Address already in use
```

**解决方案**：
```bash
# 查看端口占用
lsof -i :8080

# 修改端口
vim src/main/resources/application.properties
# 或运行时指定
java -Dserver.port=9090 -jar target/ses-webhook-api-1.0.0.jar
```

### 问题 2：日志文件未生成

**原因**：没有创建日志目录的权限

**解决方案**：
```bash
mkdir -p logs
chmod 755 logs
```

### 问题 3：Lambda 请求超时

**原因**：
- API 服务器未启动
- 防火墙阻止
- 网络不通

**解决方案**：
```bash
# 检查服务是否运行
curl http://localhost:8080/ses/webhook

# 检查防火墙（CentOS/RHEL）
sudo firewall-cmd --zone=public --add-port=8080/tcp --permanent
sudo firewall-cmd --reload

# 或使用 iptables
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

## 📚 相关文档

- [部署指南](./DEPLOYMENT.md) - 详细的部署和运维指南
- [Servlet API 文档](https://docs.oracle.com/javaee/7/api/javax/servlet/package-summary.html)
- [Jetty 文档](https://www.eclipse.org/jetty/documentation/)

## 🔗 与 Lambda 集成

确保 Lambda 的环境变量 `API_ENDPOINT` 设置为：

```
https://your-domain.com/ses/webhook
```

或者如果是内网部署：

```
http://your-server-ip:8080/ses/webhook
```

## 📄 许可证

MIT License

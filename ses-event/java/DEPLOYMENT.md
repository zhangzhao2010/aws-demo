# Java API 部署指南

## 📦 部署方式概览

支持以下几种部署方式：

1. **直接运行 JAR**（推荐用于开发/测试）
2. **systemd 服务**（推荐用于生产环境）
3. **Docker 容器**（可选）
4. **云服务器部署**（AWS EC2 / 阿里云 ECS）

---

## 🚀 方式 1：直接运行 JAR

### 1. 编译打包

```bash
cd java
mvn clean package

# 打包完成后会生成
# target/ses-webhook-api-1.0.0.jar
```

### 2. 配置白名单 IP

编辑配置文件（两种方式）：

**方式 A：修改 JAR 内配置（打包前）**

```bash
vim src/main/resources/application.properties
```

```properties
whitelist.ip=YOUR_NAT_GATEWAY_IP
```

重新打包：

```bash
mvn clean package
```

**方式 B：使用外部配置文件（打包后）**

```bash
# 复制配置文件到当前目录
cp src/main/resources/application.properties ./

# 修改配置
vim application.properties

# 运行时指定配置文件
java -Dconfig.file=./application.properties \
     -jar target/ses-webhook-api-1.0.0.jar
```

### 3. 启动服务

```bash
# 前台运行（用于测试）
java -jar target/ses-webhook-api-1.0.0.jar

# 后台运行
nohup java -jar target/ses-webhook-api-1.0.0.jar > server.log 2>&1 &

# 查看进程
ps aux | grep ses-webhook-api

# 停止服务
kill $(ps aux | grep ses-webhook-api | grep -v grep | awk '{print $2}')
```

### 4. 验证服务

```bash
# 本地测试
curl http://localhost:8080/ses/webhook

# 远程测试（替换为实际 IP）
curl http://YOUR_SERVER_IP:8080/ses/webhook
```

---

## 🛠️ 方式 2：systemd 服务（生产推荐）

### 1. 创建应用目录

```bash
sudo mkdir -p /opt/ses-webhook-api
sudo mkdir -p /opt/ses-webhook-api/logs
sudo mkdir -p /opt/ses-webhook-api/config

# 复制 JAR 文件
sudo cp target/ses-webhook-api-1.0.0.jar /opt/ses-webhook-api/

# 复制配置文件
sudo cp src/main/resources/application.properties /opt/ses-webhook-api/config/
```

### 2. 配置白名单 IP

```bash
sudo vim /opt/ses-webhook-api/config/application.properties
```

修改：

```properties
whitelist.ip=YOUR_NAT_GATEWAY_IP
log.file.path=/opt/ses-webhook-api/logs/ses-events.log
```

### 3. 创建 systemd 服务

```bash
sudo vim /etc/systemd/system/ses-webhook-api.service
```

写入以下内容：

```ini
[Unit]
Description=SES Webhook API Service
After=network.target

[Service]
Type=simple
User=nobody
Group=nobody
WorkingDirectory=/opt/ses-webhook-api
ExecStart=/usr/bin/java -Dconfig.file=/opt/ses-webhook-api/config/application.properties \
          -jar /opt/ses-webhook-api/ses-webhook-api-1.0.0.jar
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# 资源限制（可选）
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

### 4. 设置权限

```bash
# 设置目录权限
sudo chown -R nobody:nobody /opt/ses-webhook-api

# 重新加载 systemd
sudo systemctl daemon-reload
```

### 5. 启动和管理服务

```bash
# 启动服务
sudo systemctl start ses-webhook-api

# 查看状态
sudo systemctl status ses-webhook-api

# 开机自启动
sudo systemctl enable ses-webhook-api

# 停止服务
sudo systemctl stop ses-webhook-api

# 重启服务
sudo systemctl restart ses-webhook-api

# 查看日志
sudo journalctl -u ses-webhook-api -f
```

---

## 🐳 方式 3：Docker 部署（可选）

### 1. 创建 Dockerfile

```bash
cd java
vim Dockerfile
```

```dockerfile
FROM openjdk:8-jre-alpine

# 设置工作目录
WORKDIR /app

# 复制 JAR 和配置文件
COPY target/ses-webhook-api-1.0.0.jar /app/app.jar
COPY src/main/resources/application.properties /app/config/

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["java", "-Dconfig.file=/app/config/application.properties", "-jar", "/app/app.jar"]
```

### 2. 构建镜像

```bash
mvn clean package
docker build -t ses-webhook-api:1.0.0 .
```

### 3. 运行容器

```bash
# 运行容器
docker run -d \
  --name ses-webhook-api \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  -e "whitelist.ip=YOUR_NAT_GATEWAY_IP" \
  ses-webhook-api:1.0.0

# 查看日志
docker logs -f ses-webhook-api

# 停止容器
docker stop ses-webhook-api
```

### 4. 使用 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  ses-webhook-api:
    build: .
    container_name: ses-webhook-api
    ports:
      - "8080:8080"
    volumes:
      - ./logs:/app/logs
      - ./config/application.properties:/app/config/application.properties
    environment:
      - JAVA_OPTS=-Xmx512m -Xms256m
    restart: unless-stopped
```

启动：

```bash
docker-compose up -d
```

---

## ☁️ 方式 4：云服务器部署

### AWS EC2 部署

#### 1. 启动 EC2 实例

```bash
# 选择 Amazon Linux 2 或 Ubuntu 20.04
# 实例类型：t3.small（推荐）
# 安全组规则：
#   - 允许入站：TCP 8080（来源：0.0.0.0/0 或特定 CIDR）
#   - 允许出站：所有流量
```

#### 2. SSH 连接到实例

```bash
ssh -i your-key.pem ec2-user@YOUR_EC2_IP
```

#### 3. 安装 Java 8

**Amazon Linux 2**：

```bash
sudo yum update -y
sudo yum install java-1.8.0-openjdk -y
java -version
```

**Ubuntu**：

```bash
sudo apt update
sudo apt install openjdk-8-jre -y
java -version
```

#### 4. 上传应用

```bash
# 在本地打包
mvn clean package

# 上传到 EC2
scp -i your-key.pem target/ses-webhook-api-1.0.0.jar ec2-user@YOUR_EC2_IP:/home/ec2-user/
scp -i your-key.pem src/main/resources/application.properties ec2-user@YOUR_EC2_IP:/home/ec2-user/
```

#### 5. 配置和启动

```bash
# 修改配置
vim application.properties

# 运行服务
nohup java -Dconfig.file=./application.properties \
           -jar ses-webhook-api-1.0.0.jar > server.log 2>&1 &
```

#### 6. 配置防火墙（如果需要）

```bash
# Amazon Linux 2
sudo firewall-cmd --zone=public --add-port=8080/tcp --permanent
sudo firewall-cmd --reload

# Ubuntu
sudo ufw allow 8080/tcp
sudo ufw reload
```

---

## 🔒 使用 HTTPS（生产环境推荐）

### 方式 1：在 Nginx 前端配置 SSL

#### 1. 安装 Nginx

```bash
# CentOS/Amazon Linux
sudo yum install nginx -y

# Ubuntu
sudo apt install nginx -y
```

#### 2. 申请 SSL 证书

使用 **Let's Encrypt** 免费证书：

```bash
# 安装 Certbot
sudo yum install certbot python3-certbot-nginx -y  # CentOS
sudo apt install certbot python3-certbot-nginx -y  # Ubuntu

# 申请证书
sudo certbot --nginx -d your-domain.com
```

#### 3. 配置 Nginx 反向代理

```bash
sudo vim /etc/nginx/conf.d/ses-webhook-api.conf
```

```nginx
upstream ses_backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # IP 白名单（可选 - 在 Nginx 层再次验证）
    # allow 1.2.3.4;
    # deny all;

    location /ses/webhook {
        proxy_pass http://ses_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
}
```

#### 4. 启动 Nginx

```bash
# 测试配置
sudo nginx -t

# 启动服务
sudo systemctl start nginx
sudo systemctl enable nginx

# 重新加载
sudo systemctl reload nginx
```

#### 5. 更新 Lambda 环境变量

```bash
# 将 API_ENDPOINT 改为 HTTPS 地址
API_ENDPOINT=https://your-domain.com/ses/webhook
```

---

## 📊 监控和日志管理

### 1. 日志滚动策略

Logback 已配置自动滚动：

- 每天生成新文件
- 保留 30 天
- 单文件最大 100MB
- 总大小上限 3GB

### 2. 查看实时日志

```bash
# 查看所有日志
tail -f /opt/ses-webhook-api/logs/ses-events.log

# 只查看 SES 事件
tail -f /opt/ses-webhook-api/logs/ses-events-only.log

# 过滤错误日志
tail -f /opt/ses-webhook-api/logs/ses-events.log | grep ERROR
```

### 3. 日志分析

```bash
# 统计事件类型
grep "notificationType" logs/ses-events-only.log | \
  sed 's/.*notificationType": "\([^"]*\).*/\1/' | \
  sort | uniq -c

# 查找特定 messageId
grep "abc123" logs/ses-events-only.log
```

### 4. 监控脚本

创建 `monitor.sh`：

```bash
#!/bin/bash

# 检查服务是否运行
if ! pgrep -f ses-webhook-api > /dev/null; then
    echo "[ERROR] Service is down!"
    # 自动重启
    sudo systemctl restart ses-webhook-api
    # 发送告警（可选）
    # send_alert "SES Webhook API is down and restarted"
else
    echo "[OK] Service is running"
fi

# 检查日志文件大小
LOG_SIZE=$(du -m /opt/ses-webhook-api/logs/ses-events.log | cut -f1)
if [ $LOG_SIZE -gt 500 ]; then
    echo "[WARN] Log file size: ${LOG_SIZE}MB"
fi
```

设置 cron 定时任务：

```bash
crontab -e
```

添加：

```
# 每 5 分钟检查一次
*/5 * * * * /path/to/monitor.sh >> /var/log/ses-webhook-monitor.log 2>&1
```

---

## 🆘 故障排查清单

### 检查服务状态

```bash
# systemd 服务状态
sudo systemctl status ses-webhook-api

# 查看进程
ps aux | grep ses-webhook-api

# 查看端口监听
netstat -tlnp | grep 8080
# 或
ss -tlnp | grep 8080
```

### 检查日志

```bash
# systemd 日志
sudo journalctl -u ses-webhook-api -n 100

# 应用日志
tail -n 100 /opt/ses-webhook-api/logs/ses-events.log
```

### 测试网络连通性

```bash
# 本地测试
curl -v http://localhost:8080/ses/webhook

# 远程测试（从 Lambda 所在的 VPC 测试）
curl -v http://YOUR_SERVER_IP:8080/ses/webhook

# 测试 POST 请求
curl -X POST http://localhost:8080/ses/webhook \
  -H "Content-Type: application/json" \
  -d '{"notificationType":"Delivery","mail":{"messageId":"test"}}'
```

### 常见错误和解决方案

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `Address already in use` | 端口被占用 | 修改端口或关闭占用进程 |
| `Permission denied` | 权限不足 | 使用 `sudo` 或修改目录权限 |
| `Connection refused` | 服务未启动 | 启动服务并检查防火墙 |
| `403 Forbidden` | IP 不在白名单 | 添加 IP 到白名单 |

---

## 📚 性能优化建议

### JVM 参数调优

```bash
java -Xmx1024m \
     -Xms512m \
     -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -Dconfig.file=./application.properties \
     -jar ses-webhook-api-1.0.0.jar
```

### Jetty 线程池调优（需修改代码）

在 `SesWebhookServer.java` 中添加：

```java
// 设置线程池
QueuedThreadPool threadPool = new QueuedThreadPool(200, 10, 60000);
server.setThreadPool(threadPool);
```

---

## 🎉 部署完成验证

完成部署后，依次验证：

1. ✅ 服务正常启动
2. ✅ 端口正常监听
3. ✅ 日志文件正常生成
4. ✅ GET 请求返回提示信息
5. ✅ POST 请求（白名单 IP）正常处理
6. ✅ POST 请求（非白名单 IP）返回 403
7. ✅ Lambda 能够成功调用

---

## 📞 技术支持

如有问题，请检查：

1. 应用日志：`logs/ses-events.log`
2. systemd 日志：`sudo journalctl -u ses-webhook-api`
3. 网络连通性：`curl` 测试
4. 防火墙规则：`iptables -L` 或 `firewall-cmd --list-all`

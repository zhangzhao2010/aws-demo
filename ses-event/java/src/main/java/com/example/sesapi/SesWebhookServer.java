package com.example.sesapi;

import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * SES Webhook API 服务器
 * 使用 Jetty Embedded Server 运行
 */
public class SesWebhookServer {

    private static final Logger logger = LoggerFactory.getLogger(SesWebhookServer.class);
    private static final String DEFAULT_CONFIG_FILE = "application.properties";

    public static void main(String[] args) {
        try {
            // 加载配置
            Properties config = loadConfiguration();

            // 读取配置参数
            int port = Integer.parseInt(config.getProperty("server.port", "8080"));
            String host = config.getProperty("server.host", "0.0.0.0");
            String logFile = config.getProperty("log.file.path", "./logs/ses-events.log");

            // 设置日志文件路径（供 Logback 使用）
            System.setProperty("LOG_FILE", logFile);

            logger.info("========================================");
            logger.info("  SES Webhook API 启动中...");
            logger.info("========================================");
            logger.info("服务器地址: {}:{}", host, port);
            logger.info("日志文件: {}", logFile);
            logger.info("========================================");

            // 创建 Jetty 服务器
            Server server = new Server(port);

            // 创建 Servlet 上下文
            ServletContextHandler context = new ServletContextHandler(ServletContextHandler.SESSIONS);
            context.setContextPath("/");
            server.setHandler(context);

            // 注册 Servlet
            ServletHolder servletHolder = new ServletHolder(new SesWebhookServlet());
            context.addServlet(servletHolder, "/ses/webhook");

            // 启动服务器
            server.start();
            logger.info("✅ SES Webhook API 启动成功！");
            logger.info("访问地址: http://{}:{}/ses/webhook", host.equals("0.0.0.0") ? "localhost" : host, port);
            logger.info("按 Ctrl+C 停止服务器");

            // 等待服务器结束
            server.join();

        } catch (Exception e) {
            logger.error("❌ 服务器启动失败", e);
            System.exit(1);
        }
    }

    /**
     * 加载配置文件
     */
    private static Properties loadConfiguration() {
        Properties props = new Properties();

        // 尝试从多个位置加载配置文件
        String[] configPaths = {
                System.getProperty("config.file"),  // 命令行参数
                "./application.properties",          // 当前目录
                "./config/application.properties",   // config 目录
                DEFAULT_CONFIG_FILE                  // classpath
        };

        for (String configPath : configPaths) {
            if (configPath == null) {
                continue;
            }

            try {
                // 尝试从文件系统加载
                try (InputStream input = new FileInputStream(configPath)) {
                    props.load(input);
                    logger.info("成功加载配置文件: {}", configPath);
                    return props;
                } catch (IOException e) {
                    // 文件不存在，尝试从 classpath 加载
                    try (InputStream input = SesWebhookServer.class.getClassLoader()
                            .getResourceAsStream(configPath)) {
                        if (input != null) {
                            props.load(input);
                            logger.info("成功加载配置文件（classpath）: {}", configPath);
                            return props;
                        }
                    }
                }
            } catch (IOException e) {
                // 继续尝试下一个路径
            }
        }

        logger.warn("未找到配置文件，使用默认配置");
        return props;
    }
}

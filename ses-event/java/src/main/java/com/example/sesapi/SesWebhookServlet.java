package com.example.sesapi;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.stream.Collectors;

/**
 * SES 事件接收 Servlet
 * 接收 Lambda 转发的 SES 事件并记录到日志
 */
public class SesWebhookServlet extends HttpServlet {

    private static final Logger logger = LoggerFactory.getLogger(SesWebhookServlet.class);
    private static final Logger sesEventLogger = LoggerFactory.getLogger("SES_EVENT_LOGGER");
    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        // 设置响应类型
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        try {
            // 读取请求体
            String requestBody = readRequestBody(request);

            if (requestBody == null || requestBody.trim().isEmpty()) {
                sendErrorResponse(response, HttpServletResponse.SC_BAD_REQUEST, "请求体为空");
                return;
            }

            // 解析 JSON
            JsonObject sesEvent = JsonParser.parseString(requestBody).getAsJsonObject();

            // 提取关键信息
            String notificationType = sesEvent.has("notificationType")
                    ? sesEvent.get("notificationType").getAsString()
                    : "UNKNOWN";

            String messageId = "UNKNOWN";
            if (sesEvent.has("mail")) {
                JsonObject mail = sesEvent.getAsJsonObject("mail");
                if (mail.has("messageId")) {
                    messageId = mail.get("messageId").getAsString();
                }
            }

            // 记录到控制台日志
            logger.info("收到 SES 事件 - Type: {}, MessageId: {}, RemoteIP: {}",
                    notificationType, messageId, getClientIp(request));

            // 记录完整事件到专用日志文件
            String prettyJson = gson.toJson(sesEvent);
            sesEventLogger.info("SES Event [{}] - MessageId: {}\n{}",
                    notificationType, messageId, prettyJson);

            // 返回成功响应
            sendSuccessResponse(response, notificationType, messageId);

        } catch (Exception e) {
            logger.error("处理 SES 事件失败", e);
            sendErrorResponse(response, HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
                    "服务器内部错误: " + e.getMessage());
        }
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/plain");
        response.getWriter().write("SES Webhook API is running. Please use POST method.");
    }

    /**
     * 读取请求体内容
     */
    private String readRequestBody(HttpServletRequest request) throws IOException {
        try (BufferedReader reader = request.getReader()) {
            return reader.lines().collect(Collectors.joining(System.lineSeparator()));
        }
    }

    /**
     * 获取客户端真实 IP（支持代理）
     */
    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        // 如果有多个 IP（经过多层代理），取第一个
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip;
    }

    /**
     * 发送成功响应
     */
    private void sendSuccessResponse(HttpServletResponse response, String eventType, String messageId)
            throws IOException {
        response.setStatus(HttpServletResponse.SC_OK);
        JsonObject responseJson = new JsonObject();
        responseJson.addProperty("status", "success");
        responseJson.addProperty("message", "SES event received");
        responseJson.addProperty("eventType", eventType);
        responseJson.addProperty("messageId", messageId);

        PrintWriter out = response.getWriter();
        out.print(gson.toJson(responseJson));
        out.flush();
    }

    /**
     * 发送错误响应
     */
    private void sendErrorResponse(HttpServletResponse response, int statusCode, String errorMessage)
            throws IOException {
        response.setStatus(statusCode);
        JsonObject errorJson = new JsonObject();
        errorJson.addProperty("status", "error");
        errorJson.addProperty("message", errorMessage);

        PrintWriter out = response.getWriter();
        out.print(gson.toJson(errorJson));
        out.flush();
    }
}

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.Base64;
import java.util.Date;
import java.util.TimeZone;
import java.util.TreeMap;

/**
 * AWS SES REST API请求类，实现AWS签名V4认证和邮件发送功能
 */
public class AWSSESRequest {
    private static final String ALGORITHM = "AWS4-HMAC-SHA256";
    private static final String SERVICE = "ses";
    private static final String ENDPOINT_FORMAT = "https://email.%s.amazonaws.com/";
    private static final String API_VERSION = "2010-12-01";

    // 添加调试模式标志
    private static final boolean DEBUG_MODE = true;

    private final String accessKey;
    private final String secretKey;
    private final String region;
    private final String endpoint;

    public AWSSESRequest(String accessKey, String secretKey, String region) {
        this.accessKey = accessKey;
        this.secretKey = secretKey;
        this.region = region;
        this.endpoint = String.format(ENDPOINT_FORMAT, region);
    }

    /**
     * 验证邮箱身份
     *
     * @param emailAddress 要验证的邮箱地址
     * @return 验证请求是否成功发送
     */
    public boolean verifyEmailIdentity(String emailAddress) {
        try {
            // 构建请求参数
            TreeMap<String, String> params = new TreeMap<>();
            params.put("Action", "VerifyEmailIdentity");
            params.put("EmailAddress", emailAddress);
            params.put("Version", API_VERSION);

            if (DEBUG_MODE) {
                System.out.println("===== 验证邮箱请求 =====");
                System.out.println("邮箱地址: " + emailAddress);
            }

            // 发送请求并获取响应
            return sendRequest(params);
        } catch (Exception e) {
            System.err.println("验证邮箱请求异常: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    /**
     * 发送请求到AWS SES API
     *
     * @param params 请求参数
     * @return 请求是否成功
     */
    private boolean sendRequest(TreeMap<String, String> params) throws Exception {
        // 获取当前时间
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyyMMdd'T'HHmmss'Z'");
        dateFormat.setTimeZone(TimeZone.getTimeZone("UTC"));
        Date now = new Date();
        String amzDate = dateFormat.format(now);
        String dateStamp = amzDate.substring(0, 8);

        if (DEBUG_MODE) {
            System.out.println("===== 请求信息 =====");
            System.out.println("Access Key: " + accessKey);
            System.out.println("Region: " + region);
            System.out.println("Endpoint: " + endpoint);
            System.out.println("Date: " + amzDate);
            System.out.println("Date Stamp: " + dateStamp);
            System.out.println("Parameters: " + params);
        }

        // 构建HTTP请求
        URL url = new URL(endpoint);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");

        // 构建标准的请求参数
        String payload = buildPayload(params);

        // 计算签名
        String canonicalRequest = buildCanonicalRequest(params, amzDate, payload);
        if (DEBUG_MODE) {
            System.out.println("Canonical Request: \n" + canonicalRequest);
        }

        String stringToSign = buildStringToSign(canonicalRequest, amzDate, dateStamp);
        if (DEBUG_MODE) {
            System.out.println("String to Sign: \n" + stringToSign);
        }

        byte[] signature = calculateSignature(stringToSign, dateStamp);
        String signatureHex = bytesToHex(signature);
        if (DEBUG_MODE) {
            System.out.println("Signature: " + signatureHex);
        }

        // 设置请求头
        String host = "email." + region + ".amazonaws.com";
        connection.setRequestProperty("Host", host);
        connection.setRequestProperty("X-Amz-Date", amzDate);
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");

        // 设置授权头
        String authorizationHeader = ALGORITHM + " " +
                "Credential=" + accessKey + "/" + dateStamp + "/" + region + "/" + SERVICE + "/aws4_request, " +
                "SignedHeaders=content-type;host;x-amz-date, " +
                "Signature=" + signatureHex;
        connection.setRequestProperty("Authorization", authorizationHeader);

        if (DEBUG_MODE) {
            System.out.println("Authorization Header: " + authorizationHeader);
        }

        // 设置请求体
        connection.setDoOutput(true);
        try (DataOutputStream wr = new DataOutputStream(connection.getOutputStream())) {
            wr.write(payload.getBytes(StandardCharsets.UTF_8));
            if (DEBUG_MODE) {
                System.out.println("Request Payload: " + payload);
            }
        }

        // 获取响应
        int responseCode = connection.getResponseCode();
        StringBuilder response = new StringBuilder();
        try (BufferedReader in = new BufferedReader(
                new InputStreamReader(
                        responseCode >= 400 ? connection.getErrorStream() : connection.getInputStream()))) {
            String line;
            while ((line = in.readLine()) != null) {
                response.append(line);
            }
        }

        if (DEBUG_MODE) {
            System.out.println("===== 响应信息 =====");
            System.out.println("HTTP 状态码: " + responseCode);

            // 打印所有响应头
            System.out.println("响应头:");
            for (String key : connection.getHeaderFields().keySet()) {
                if (key != null) {
                    System.out.println(key + ": " + connection.getHeaderField(key));
                }
            }
        }

        if (responseCode >= 200 && responseCode < 300) {
            System.out.println("请求成功!");
            System.out.println("AWS SES响应: " + response.toString());
            return true;
        } else {
            System.err.println("请求失败!");
            System.err.println("HTTP错误码: " + responseCode);
            System.err.println("错误响应: " + response.toString());

            // 根据错误代码提供更详细的诊断信息
            if (responseCode == 403) {
                if (response.toString().contains("InvalidClientTokenId")) {
                    System.err.println("诊断: 您的AWS访问密钥无效或不存在。请检查访问密钥是否正确。");
                } else if (response.toString().contains("SignatureDoesNotMatch")) {
                    System.err.println("诊断: 签名计算错误。请检查您的密钥是否正确，并确认没有多余的空格。");
                } else {
                    System.err.println("诊断: 权限不足。请确认IAM用户/角色具有所需权限。");
                }
            } else if (responseCode == 400) {
                System.err.println("诊断: 请求格式错误。请检查参数格式。");
            }

            return false;
        }
    }

    /**
     * 发送邮件
     *
     * @param from 发件人邮箱
     * @param to 收件人邮箱
     * @param subject 邮件主题
     * @param body 邮件内容
     * @return 是否发送成功
     */
    public boolean sendEmail(String from, String to, String subject, String body) {
        try {
            // 构建请求参数
            TreeMap<String, String> params = new TreeMap<>();
            params.put("Action", "SendEmail");
            params.put("Source", from);
            params.put("Destination.ToAddresses.member.1", to);
            params.put("Message.Subject.Data", subject);
            params.put("Message.Body.Text.Data", body);
            params.put("Version", API_VERSION);

            if (DEBUG_MODE) {
                System.out.println("===== 发送邮件请求 =====");
                System.out.println("发件人: " + from);
                System.out.println("收件人: " + to);
                System.out.println("主题: " + subject);
                System.out.println("内容: " + body);
            }

            // 发送请求并获取响应
            return sendRequest(params);

        } catch (Exception e) {
            System.err.println("发送邮件请求异常: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    /**
     * 构建规范请求
     */
    private String buildCanonicalRequest(TreeMap<String, String> params, String amzDate, String payload) throws Exception {
        StringBuilder canonicalRequest = new StringBuilder();
        canonicalRequest.append("POST\n");                  // HTTP方法
        canonicalRequest.append("/\n");                     // URI
        canonicalRequest.append("\n");                      // 查询字符串(没有)

        // 规范化请求头 - 按字母顺序排列
        canonicalRequest.append("content-type:application/x-www-form-urlencoded\n");
        canonicalRequest.append("host:email.").append(region).append(".amazonaws.com\n");
        canonicalRequest.append("x-amz-date:").append(amzDate).append("\n");
        canonicalRequest.append("\n");                      // 结束请求头

        // 签名的请求头 - 按字母顺序排列
        canonicalRequest.append("content-type;host;x-amz-date\n");

        // 请求体的哈希值
        canonicalRequest.append(sha256Hex(payload));

        return canonicalRequest.toString();
    }

    /**
     * 构建签名字符串
     */
    private String buildStringToSign(String canonicalRequest, String amzDate, String dateStamp) throws Exception {
        StringBuilder stringToSign = new StringBuilder();
        stringToSign.append(ALGORITHM).append("\n");
        stringToSign.append(amzDate).append("\n");
        stringToSign.append(dateStamp).append("/").append(region).append("/").append(SERVICE).append("/aws4_request\n");
        stringToSign.append(sha256Hex(canonicalRequest));

        return stringToSign.toString();
    }

    /**
     * 计算签名
     */
    private byte[] calculateSignature(String stringToSign, String dateStamp) throws Exception {
        byte[] kSecret = ("AWS4" + secretKey).getBytes(StandardCharsets.UTF_8);
        byte[] kDate = hmacSha256(kSecret, dateStamp);
        byte[] kRegion = hmacSha256(kDate, region);
        byte[] kService = hmacSha256(kRegion, SERVICE);
        byte[] kSigning = hmacSha256(kService, "aws4_request");

        return hmacSha256(kSigning, stringToSign);
    }

    /**
     * 构建请求负载
     */
    private String buildPayload(TreeMap<String, String> params) throws Exception {
        StringBuilder payload = new StringBuilder();
        boolean first = true;

        for (String key : params.keySet()) {
            if (!first) {
                payload.append("&");
            }
            payload.append(URLEncoder.encode(key, "UTF-8"))
                   .append("=")
                   .append(URLEncoder.encode(params.get(key), "UTF-8"));
            first = false;
        }

        return payload.toString();
    }

    /**
     * 计算字符串的SHA-256哈希值
     */
    private String sha256Hex(String data) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] digest = md.digest(data.getBytes(StandardCharsets.UTF_8));
        return bytesToHex(digest);
    }

    /**
     * 计算HMAC SHA-256
     */
    private byte[] hmacSha256(byte[] key, String data) throws Exception {
        String algorithm = "HmacSHA256";
        Mac mac = Mac.getInstance(algorithm);
        mac.init(new SecretKeySpec(key, algorithm));
        return mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
    }

    /**
     * 将字节数组转换为十六进制字符串
     */
    private String bytesToHex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes) {
            result.append(String.format("%02x", b));
        }
        return result.toString();
    }
}
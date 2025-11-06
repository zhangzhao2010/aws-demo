import java.util.Properties;
import java.io.FileInputStream;
import java.io.IOException;

/**
 * AWS SES REST API邮件发送主类
 */
public class AWSSESSender {
    public static void main(String[] args) {
        try {
            // 解析命令行参数
            String command = args.length > 0 ? args[0] : "send";

            // 加载配置文件
            Properties props = new Properties();
            try {
                props.load(new FileInputStream("config.properties"));
                System.out.println("配置文件加载成功");
            } catch (IOException e) {
                System.out.println("配置文件未找到，将使用代码中的默认配置");
            }

            // AWS认证信息
            String accessKey = props.getProperty("aws.accessKey", "YOUR_ACCESS_KEY");
            String secretKey = props.getProperty("aws.secretKey", "YOUR_SECRET_KEY");
            String region = props.getProperty("aws.region", "us-east-1");

            // 创建SES请求对象
            AWSSESRequest request = new AWSSESRequest(accessKey, secretKey, region);

            // 根据命令执行不同操作
            if ("verify".equalsIgnoreCase(command)) {
                // 从命令行或配置获取要验证的邮箱
                String email = args.length > 1 ? args[1] : props.getProperty("email.verify");
                if (email == null || email.trim().isEmpty()) {
                    System.out.println("请指定要验证的邮箱地址，例如: java AWSSESSender verify your@email.com");
                    return;
                }

                System.out.println("正在验证邮箱: " + email);
                boolean success = request.verifyEmailIdentity(email);
                if (success) {
                    System.out.println("验证邮件已发送！请检查您的邮箱并点击验证链接。");
                } else {
                    System.out.println("验证请求失败，请查看错误日志。");
                }
            } else {
                // 发送邮件
                // 邮件信息
                String from = props.getProperty("email.from", "sender@example.com");
                String to = props.getProperty("email.to", "recipient@example.com");
                String subject = props.getProperty("email.subject", "Test email from AWS SES");
                String body = props.getProperty("email.body", "This is a test email sent using AWS SES REST API");

                // 如果命令行提供了参数，则覆盖配置文件的值
                if (args.length > 1) from = args[1];
                if (args.length > 2) to = args[2];
                if (args.length > 3) subject = args[3];

                System.out.println("发件人: " + from);
                System.out.println("收件人: " + to);
                System.out.println("主题: " + subject);

                boolean success = request.sendEmail(from, to, subject, body);

                if (success) {
                    System.out.println("邮件发送成功！");
                } else {
                    System.out.println("邮件发送失败，请查看错误日志。");
                    System.out.println("\n提示: 如果您的AWS账户在SES沙箱模式中，必须先验证发件人和收件人邮箱。");
                    System.out.println("您可以使用以下命令验证邮箱: java AWSSESSender verify your@email.com");
                }
            }

        } catch (Exception e) {
            System.err.println("执行过程中出现异常：" + e.getMessage());
            e.printStackTrace();
        }
    }
}
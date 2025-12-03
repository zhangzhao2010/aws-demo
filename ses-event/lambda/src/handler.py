"""
SES 事件转发 Lambda 函数
接收 SNS 推送的 SES 事件，并转发到自建 API
"""
import json
import logging
import requests
from config import Config

# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda 入口函数

    Args:
        event: SNS 事件对象，包含 SES 事件数据
        context: Lambda 运行时上下文

    Returns:
        dict: 处理结果

    Raises:
        Exception: 处理失败时抛出异常，触发 SNS 重试
    """
    try:
        # 验证配置
        Config.validate()
        logger.info(
            f"API Endpoint: {Config.API_ENDPOINT}, Timeout: {Config.API_TIMEOUT}s")

        # 处理 SNS 记录
        for record in event.get('Records', []):
            process_sns_record(record)

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok', 'message': 'Events forwarded successfully'})
        }

    except Exception as e:
        logger.error(f"Lambda 处理失败: {str(e)}", exc_info=True)
        # 抛出异常让 SNS 重试
        raise


def process_sns_record(record):
    """
    处理单条 SNS 记录
    支持两种消息类型：
    1. SubscriptionConfirmation - 订阅确认
    2. Notification - SES 事件通知

    Args:
        record: SNS 记录对象
    """
    try:
        # 提取 SNS 消息
        sns_message = record.get('Sns', {})
        message_type = sns_message.get('Type', 'Notification')
        message_id = sns_message.get('MessageId', 'unknown')
        timestamp = sns_message.get('Timestamp', 'unknown')

        logger.info(
            f"收到 SNS 消息 - Type: {message_type}, MessageId: {message_id}")

        # 处理订阅确认
        if message_type == 'SubscriptionConfirmation':
            handle_subscription_confirmation(sns_message)
            return

        # 处理取消订阅确认
        if message_type == 'UnsubscribeConfirmation':
            logger.info(f"收到取消订阅确认 - MessageId: {message_id}")
            return

        # 处理正常的通知消息（SES 事件）
        if message_type == 'Notification':
            # 解析 SES 事件数据
            ses_event = json.loads(sns_message.get('Message', '{}'))
            event_type = ses_event.get('notificationType', 'unknown')

            logger.info(
                f"收到 SES 事件 - Type: {event_type}, MessageId: {message_id}, Timestamp: {timestamp}")

            # 转发到自建 API
            forward_to_api(ses_event, event_type)
        else:
            logger.warning(f"未知的 SNS 消息类型: {message_type}")

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"处理 SNS 记录失败: {str(e)}")
        raise


def handle_subscription_confirmation(sns_message):
    """
    处理 SNS 订阅确认
    通过访问 SubscribeURL 来确认订阅

    Args:
        sns_message: SNS 消息对象
    """
    subscribe_url = sns_message.get('SubscribeURL')
    topic_arn = sns_message.get('TopicArn', 'unknown')

    if not subscribe_url:
        logger.error("SubscriptionConfirmation 缺少 SubscribeURL")
        return

    logger.info(f"正在确认 SNS 订阅 - TopicArn: {topic_arn}")

    try:
        # 访问 SubscribeURL 来确认订阅
        response = requests.get(subscribe_url, timeout=10)
        response.raise_for_status()

        logger.info(f"✅ SNS 订阅确认成功 - TopicArn: {topic_arn}")

    except requests.exceptions.RequestException as e:
        logger.error(f"SNS 订阅确认失败: {str(e)}")
        # 不抛出异常，避免影响其他消息处理
        # AWS 会在 Lambda 订阅时自动确认，这里只是备用机制


def forward_to_api(ses_event, event_type):
    """
    将 SES 事件转发到自建 API

    Args:
        ses_event: SES 事件数据
        event_type: 事件类型（Delivery/Bounce/Complaint 等）
    """
    try:
        # 发送 POST 请求
        response = requests.post(
            Config.API_ENDPOINT,
            json=ses_event,
            timeout=Config.API_TIMEOUT,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'AWS-Lambda-SES-Forwarder/1.0'
            }
        )

        # 检查响应状态
        response.raise_for_status()

        logger.info(
            f"成功转发事件到 API - Type: {event_type}, Status: {response.status_code}")

    except requests.exceptions.Timeout as e:
        logger.error(f"API 请求超时 ({Config.API_TIMEOUT}s): {str(e)}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"API 请求失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(
                f"响应状态码: {e.response.status_code}, 响应内容: {e.response.text}")
        raise


if __name__ == '__main__':
    with open('../tests/test_event.json') as f:
        event = json.load(f)
        result = lambda_handler(event, None)
        print(result)

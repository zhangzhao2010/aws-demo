"""
Lambda 配置模块
从环境变量读取配置参数
"""
import os


class Config:
    """Lambda 运行配置"""

    # 自建 API 配置
    API_ENDPOINT = os.environ.get('API_ENDPOINT')

    # 请求超时配置（秒）
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', '5'))

    # 日志级别
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """验证必要的配置项是否存在"""
        if not cls.API_ENDPOINT:
            raise ValueError("环境变量 API_ENDPOINT 未设置")

        if cls.API_TIMEOUT <= 0:
            raise ValueError(f"API_TIMEOUT 必须大于 0，当前值: {cls.API_TIMEOUT}")

        return True

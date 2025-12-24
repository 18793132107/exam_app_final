import os
from kivy.metrics import dp


class AppConfig:
    """应用配置常量"""

    # 应用设置
    APP_NAME = "智能试题练习系统"
    VERSION = "1.0.0"

    # 窗口设置
    WINDOW_SIZE = (360, 640)
    WINDOW_BG_COLOR = (0.95, 0.95, 0.95, 1)

    # 练习设置
    DEFAULT_QUESTION_COUNT = 50
    DEFAULT_AUTO_NEXT_DELAY = 3

    # 考试设置
    EXAM_DURATION = 3600  # 60分钟
    EXAM_SINGLE_COUNT = 20
    EXAM_MULTI_COUNT = 20
    EXAM_JUDGMENT_COUNT = 10

    # 字体设置
    DEFAULT_FONT_SIZE = 16
    FONT_PATHS = [
        'fonts/simhei.ttf',
        'simhei.ttf',
        'fonts/msyh.ttf',
        'msyh.ttf',
        # 系统字体路径...
    ]

    # 文件路径
    USER_DATA_FILE = "user_data.json"
    APP_SETTINGS_FILE = "app_settings.json"
    QUESTION_BANK_PATH = "题库"

    # UI常量
    BUTTON_HEIGHT = dp(50)
    OPTION_BUTTON_HEIGHT = dp(45)
    PADDING = dp(15)
    SPACING = dp(10)

    # 颜色配置
    COLOR_PRIMARY = (0.2, 0.6, 0.8, 1)  # 主色调
    COLOR_SUCCESS = (0.2, 0.8, 0.2, 1)  # 成功色
    COLOR_DANGER = (0.8, 0.2, 0.2, 1)  # 危险色
    COLOR_WARNING = (1.0, 0.8, 0.0, 1)  # 警告色

    # 重复题型处理
    DUPLICATE_THRESHOLD = 3

    @classmethod
    def get_default_settings(cls):
        """获取默认设置"""
        return {
            'question_count': cls.DEFAULT_QUESTION_COUNT,
            'exam_single_count': cls.EXAM_SINGLE_COUNT,
            'exam_multi_count': cls.EXAM_MULTI_COUNT,
            'exam_judgment_count': cls.EXAM_JUDGMENT_COUNT,
            'font_size': cls.DEFAULT_FONT_SIZE,
            'save_interval': 5,
            'auto_next_delay': cls.DEFAULT_AUTO_NEXT_DELAY
        }
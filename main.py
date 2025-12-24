import os
import platform
import json
import random
import hashlib
import re
import warnings
import time
from kivy.clock import Clock
from threading import Thread
from base_screen import BaseQuestionScreen, QuestionStatistics
from config import AppConfig
from datetime import datetime

# 设置环境变量
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

# 屏蔽openpyxl的数据验证警告
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import get_color_from_hex
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.animation import Animation
from kivy.uix.widget import Widget
import pandas as pd


# 统一的字体加载函数
def load_chinese_font():
    """加载中文字体，返回字体名称"""
    system = platform.system()
    
    # 字体搜索路径
    font_paths = [
        'fonts/simhei.ttf',
        'simhei.ttf',
        'fonts/msyh.ttf',
        'msyh.ttf',
    ]
    
    # 添加系统字体路径
    if system == "Windows":
        font_paths.extend([
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
        ])
    elif system == "Darwin":  # macOS
        font_paths.extend([
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
        ])
    elif system == "Linux":
        font_paths.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        ])
    else:  # Android或其他系统
        # 在Android上尝试使用系统字体
        font_paths.extend([
            "/system/fonts/DroidSansFallback.ttf",
            "/system/fonts/NotoSansCJK-Regular.ttc",
        ])
        
    # 尝试加载字体
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                # 注册字体
                LabelBase.register(name='chinese_font', fn_regular=font_path)
                print(f"✅ 成功加载字体: {font_path}")
                return "chinese_font"
            except Exception as e:
                print(f"❌ 字体加载失败 {font_path}: {e}")
                
    print("⚠️ 未找到可用的中文字体，使用默认字体Roboto")
    return "Roboto"

# 只加载一次字体
FONT_NAME = load_chinese_font()
print(f"最终使用的字体名称: {FONT_NAME}")

# 注意：Kivy会自动加载mobileexam.kv文件

from kivy.animation import Animation
from kivy.properties import NumericProperty
import hashlib
import pandas as pd
import re
from kivy.uix.button import Button
from kivy.properties import NumericProperty
from kivy.animation import Animation


class CustomButton(Button):
    scale = NumericProperty(1.0)  # 添加scale属性

    def on_press(self):
        # 按压时缩小到90%
        anim = Animation(scale=0.9, duration=0.1)
        anim.start(self)

    def on_release(self):
        # 释放时恢复原大小
        anim = Animation(scale=1.0, duration=0.1)
        anim.start(self)


class Question:
    def __init__(self, row, source_file=""):
        try:
            # 获取题型（索引1，兼容空值）
            if len(row) > 1 and pd.notna(row.iloc[1]):
                self.q_type = str(row.iloc[1]).strip()
            else:
                self.q_type = ""

            # 获取题目内容（索引2，兼容空值）
            if len(row) > 2 and pd.notna(row.iloc[2]):
                self.question = str(row.iloc[2]).strip()
            else:
                self.question = ""

            # 获取选项（索引3-6，兼容空值和非字符串）
            self.options = {}
            option_letters = ["A", "B", "C", "D"]
            for i, letter in enumerate(option_letters, start=3):
                if i < len(row) and pd.notna(row.iloc[i]):
                    option_text = str(row.iloc[i]).strip()
                    if option_text and option_text.lower() != "nan":
                        self.options[letter] = option_text

            # 特殊处理判断题
            if self.q_type == "判断题" and not self.options:
                self.options = {"A": "正确", "B": "错误"}

            # 获取正确答案
            if len(row) > 7 and pd.notna(row.iloc[7]):
                raw_answer = str(row.iloc[7]).strip()
            else:
                raw_answer = ""

            # 处理判断题答案
            if self.q_type == "判断题":
                correct_symbols = ["正确", "对", "√", "✓", "T", "t", "是", "Y", "y", "1", "A"]
                wrong_symbols = ["错误", "错", "×", "✗✗", "F", "f", "否", "N", "n", "0", "B"]
                if raw_answer in correct_symbols:
                    self.correct_answer = "A"
                elif raw_answer in wrong_symbols:
                    self.correct_answer = "B"
                else:
                    self.correct_answer = raw_answer.upper()
            else:
                self.correct_answer = raw_answer.upper()

            # 获取解析
            if len(row) > 8 and pd.notna(row.iloc[8]):
                self.analysis = str(row.iloc[8]).strip()
            else:
                self.analysis = ""

            # 生成唯一ID
            question_str = f"{self.q_type}_{self.question}_{self.correct_answer}"
            self.id = f"{source_file}_{hashlib.md5(question_str.encode('utf-8')).hexdigest()[:8]}"
            self.source_file = source_file

        except Exception as e:
            # 统一异常处理：记录详细错误信息
            error_info = f"创建题目对象失败: {e}\n行数据: {row.tolist() if hasattr(row, 'tolist') else '无数据'}"
            print(error_info)
            raise ValueError(error_info)  # 统一抛出ValueError

    def is_correct(self, user_answer):
        """检查用户答案是否正确"""
        if self.q_type == "多选题":
            return set(user_answer.upper()) == set(self.correct_answer.upper())
        else:
            return user_answer.upper() == self.correct_answer.upper()


# QuestionStatistics类已移至base_screen.py

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.buttons_created = False

    def on_enter(self, *args):
        super().on_enter(*args)
        if not self.buttons_created:
            self.buttons_created = True
            print("主屏幕按钮已创建")

    def load_user_data(self):
        pass  # 主屏幕不需要加载用户数据

    def start_practice(self):
        """切换到练习模式"""
        app = App.get_running_app()
        app.show_loading("准备练习模式...")
        Clock.schedule_once(lambda dt: [app.hide_loading(), app.switch_to_practice()], 1.0)

    def start_exam(self):
        """切换到模拟考试"""
        app = App.get_running_app()
        app.show_loading("准备模拟考试...")
        Clock.schedule_once(lambda dt: [app.hide_loading(), app.switch_to_exam()], 1.5)

    def review_mistakes(self):
        """切换到错题复习"""
        app = App.get_running_app()
        app.show_loading("加载错题...")
        Clock.schedule_once(lambda dt: [app.hide_loading(), app.switch_to_review()], 1.5)

    def show_stats(self):
        """切换到统计页面"""
        app = App.get_running_app()
        app.switch_to_stats()

    def system_settings(self):
        """切换到系统设置"""
        app = App.get_running_app()
        app.switch_to_settings()

    def exit_app(self):
        """退出应用"""
        app = App.get_running_app()
        app.stop()

class PracticeScreen(BaseQuestionScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_question_index = 0
        self.selected_options = []
        self.questions = []
        self.correct_count = 0
        self.total_questions = 0
        self.loading_popup = self.create_loading_popup()

    def create_loading_popup(self):
        """创建加载提示弹窗"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        label = Label(text="正在加载题库...", color=(0, 0, 0, 1))
        content.add_widget(label)
        spinner = ProgressBar()
        spinner.value = 50
        content.add_widget(spinner)
        
        popup = Popup(
            title='请稍候',
            content=content,
            size_hint=(0.8, 0.3),
            background_color=(1, 1, 1, 1)
        )
        return popup

    def on_pre_enter(self):
        # 进入练习屏幕时加载题目
        self.load_user_data()
        # 异步加载题目
        self.load_questions_async()
        self.correct_count = 0

    def on_questions_loaded(self):
        """题目加载完成后的回调"""
        self.loading_popup.dismiss()
        self.total_questions = len(self.questions)
        if self.total_questions > 0:
            self.load_question(0)
        else:
            # 如果没有题目，显示提示信息
            self.ids.question_label.text = "题库中没有题目\n请在应用目录下创建'题库'文件夹，并将Excel题库文件放入其中。"
            self.ids.progress_label.text = "无题目"
            self.ids.options_container.clear_widgets()

    def load_questions(self):
        """加载题目数据 - 统一异常处理版本"""
        self.questions = []
        question_bank_path = "题库"

        try:
            if not os.path.exists(question_bank_path):
                question_bank_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "题库")
                if not os.path.exists(question_bank_path):
                    os.makedirs(question_bank_path)
                    return

            excel_files = []
            for f in os.listdir(question_bank_path):
                if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$'):
                    excel_files.append(f)

            if not excel_files:
                print("题库文件夹中没有找到Excel文件！")
                return

            all_questions = []
            for file in excel_files:
                try:
                    file_path = os.path.join(question_bank_path, file)
                    df_dict = pd.read_excel(file_path, sheet_name=None, header=None)

                    for sheet_name, df in df_dict.items():
                        for index, row in df.iterrows():
                            try:
                                question = Question(row, file)
                                if (question.q_type and question.question and
                                        question.correct_answer and
                                        question.q_type in ["单选题", "多选题", "判断题"]):
                                    all_questions.append(question)

                                    if question.id not in self.user_data:
                                        self.user_data[question.id] = {
                                            "total_count": 0,
                                            "correct_count": 0,
                                            "wrong_count": 0,
                                            "last_answer": "",
                                            "is_wrong": False
                                        }
                            except ValueError as e:
                                # 记录但跳过无效题目
                                print(f"跳过无效题目: {e}")
                                continue
                            except Exception as e:
                                print(f"解析题目时出现意外错误: {e}")
                                continue

                except Exception as e:
                    print(f"读取文件{file}时出错: {e}")
                    continue

            # 根据设置选择题目数量
            app = App.get_running_app()
            question_count = app.settings.get('question_count', 50)

            if len(all_questions) > question_count:
                self.questions = random.sample(all_questions, question_count)
            else:
                self.questions = all_questions

            print(f"成功加载了 {len(self.questions)} 道题目")

        except Exception as e:
            print(f"加载题目过程中出现严重错误: {e}")
            self.questions = []  # 确保返回空列表而不是None

    def _show_no_questions_message(self, dt):
        """显示没有题目提示信息"""
        if hasattr(self, 'ids') and self.ids:
            self.ids.question_label.text = "题库中没有题目\n请在应用目录下创建'题库'文件夹，并将Excel题库文件放入其中。"
            self.ids.progress_label.text = "无题目"
            self.ids.options_container.clear_widgets()

    def load_question(self, index):
        """加载指定索引的题目"""
        if index < 0 or index >= len(self.questions):
            self.show_final_result()
            return

        self.current_question_index = index
        question = self.questions[index]

        # 更新题目
        question_text = f"{question.q_type}\n\n{question.question}"
        self.ids.question_label.text = question_text

        # 更新进度
        self.ids.progress_label.text = f"第{index + 1}题/共{len(self.questions)}题"

        # 清空选项容器
        options_container = self.ids.options_container
        options_container.clear_widgets()

        # 添加选项
        sorted_options = sorted(question.options.items())
        for letter, option_text in sorted_options:
            # 使用ToggleButton作为选项按钮
            btn = ToggleButton(
                text=f"{letter}. {option_text}",
                font_size='16sp',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.9, 0.9, 0.9, 1),
                background_normal='',
                color=(0, 0, 0, 1),
                group='options' if question.q_type != "多选题" else None,
                halign='left',
                text_size=(self.width - dp(20), None),
                padding=[dp(10), 0]
            )
            btn.option_letter = letter
            btn.bind(on_press=self.select_option)
            options_container.add_widget(btn)

        # 重置选择
        self.selected_options = []

    def load_questions_async(self):
        """异步加载题目 - 线程安全版本"""
        # 显示加载动画
        self.loading_popup.open()

        def load_in_background():
            try:
                self.load_questions()  # 原加载逻辑
                # 安全地回到主线程更新UI
                Clock.schedule_once(lambda dt: self.safe_on_questions_loaded(), 0)
            except Exception as e:
                # 错误处理也必须在主线程
                Clock.schedule_once(lambda dt: self.safe_on_questions_error(e), 0)

        Thread(target=load_in_background, daemon=True).start()

    def safe_on_questions_loaded(self):
        """线程安全的题目加载完成回调"""
        try:
            # 安全检查所有UI组件是否存在
            if not hasattr(self, 'ids') or not self.ids:
                return

            if hasattr(self, 'loading_popup') and self.loading_popup:
                self.loading_popup.dismiss()

            self.total_questions = len(self.questions)
            if self.total_questions > 0:
                self.load_question(0)
            else:
                # 使用安全的方式更新UI
                if 'question_label' in self.ids:
                    self.ids.question_label.text = "题库中没有题目\n请在应用目录下创建'题库'文件夹，并将Excel题库文件放入其中。"
                if 'progress_label' in self.ids:
                    self.ids.progress_label.text = "无题目"
                if 'options_container' in self.ids:
                    self.ids.options_container.clear_widgets()

        except Exception as e:
            print(f"更新UI时出错: {e}")

    def on_questions_loaded(self):
        """题目加载完成后的回调"""
        self.loading_popup.dismiss()
        self.total_questions = len(self.questions)
        if self.total_questions > 0:
            self.load_question(0)
        else:
            # 如果没有题目，显示提示信息
            self.ids.question_label.text = "题库中没有题目\n请在应用目录下创建'题库'文件夹，并将Excel题库文件放入其中。"
            self.ids.progress_label.text = "无题目"
            self.ids.options_container.clear_widgets()

    def select_option(self, instance):
        """选择选项"""
        question = self.questions[self.current_question_index]

        if question.q_type == "多选题":
            # 多选题：可以选中多个选项
            if instance.option_letter in self.selected_options:
                # 取消选中
                self.selected_options.remove(instance.option_letter)
                instance.background_color = (0.9, 0.9, 0.9, 1)
            else:
                # 选中
                self.selected_options.append(instance.option_letter)
                instance.background_color = (0.2, 0.6, 0.8, 1)
        else:
            # 单选题和判断题：只能选中一个选项
            # 清除之前的选择
            for child in self.ids.options_container.children:
                child.background_color = (0.9, 0.9, 0.9, 1)
                child.state = 'normal'

            # 标记当前选择
            self.selected_options = [instance.option_letter]
            instance.background_color = (0.2, 0.6, 0.8, 1)
            instance.state = 'down'

    def safe_on_questions_error(self, error):
        """线程安全的错误处理"""
        try:
            if hasattr(self, 'loading_popup') and self.loading_popup:
                self.loading_popup.dismiss()

            # 显示错误信息
            if hasattr(self, 'ids') and self.ids and 'question_label' in self.ids:
                self.ids.question_label.text = f"加载题目时出错: {str(error)}"

        except Exception as e:
            print(f"处理错误时出错: {e}")

    def submit_answer(self):
        """提交答案"""
        if not self.selected_options:
            app = App.get_running_app()
            app.show_message("请先选择一个答案")
            return

        # 检查答案
        question = self.questions[self.current_question_index]
        user_answer = "".join(sorted(self.selected_options))  # 对多选题排序以保证一致性

        is_correct = question.is_correct(user_answer)

        if is_correct:
            self.correct_count += 1

        # 记录答题情况
        self.record_answer(question, user_answer, is_correct)

        # 显示结果
        app = App.get_running_app()
        app.show_answer_result(is_correct, user_answer, question)

        # 2秒后自动下一题
        Clock.schedule_once(lambda dt: self.next_question(), 2)

    def next_question(self):
        """下一题"""
        self.load_question(self.current_question_index + 1)

    def show_final_result(self):
        """显示练习最终结果弹窗"""
        accuracy = (self.correct_count / self.total_questions * 100) if self.total_questions > 0 else 0

        # 弹窗内容布局（增大padding-top避免标题遮挡）
        content = BoxLayout(orientation='vertical', padding=[dp(30), dp(20), dp(30), dp(20)], spacing=dp(15))

        # 标题
        title_label = Label(
            text="练习完成！",
            font_size='20sp',
            color=(0.2, 0.4, 0.6, 1)
        )
        content.add_widget(title_label)

        # 统计数据
        stats_text = f"总题数: {self.total_questions} 道\n"
        stats_text += f"答对题数: {self.correct_count} 道\n"
        stats_text += f"正确率: {accuracy:.1f}%"
        stats_label = Label(text=stats_text, color=(0, 0, 0, 1))
        content.add_widget(stats_label)

        # 返回主菜单按钮
        btn = Button(
            text='返回主菜单',
            size_hint=(1, 0.3),
            background_color=(0.2, 0.6, 0.8, 1),
            background_normal='',
            color=(1, 1, 1, 1)
        )

        def go_to_main(instance):
            popup.dismiss()
            app = App.get_running_app()
            app.switch_to_main()

        btn.bind(on_press=go_to_main)
        content.add_widget(btn)

        # 创建弹窗（标题已通过KV全局设置字体）
        popup = Popup(
            title='练习完成！',  # 修正错别字
            content=content,
            size_hint=(0.8, 0.5),
            background_color=(1, 1, 1, 1)
        )
        popup.open()

    def go_back(self):
        """返回主菜单"""
        app = App.get_running_app()
        app.switch_to_main()

class ExamScreen(BaseQuestionScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_question_index = 0
        self.selected_options = []
        self.exam_questions = []
        self.exam_answers = {}
        self.exam_start_time = None
        self.exam_duration = 3600  # 60分钟考试时间
        self.exam_timer = None

    def on_pre_enter(self):
        """进入屏幕时调用"""
        super().on_pre_enter()
        self._is_active = True
        self.load_user_data()
        self.start_exam()

    def on_leave(self):
        """离开屏幕时清理资源"""
        super().on_leave()
        self._is_active = False

        # 停止并清理计时器
        if hasattr(self, 'exam_timer') and self.exam_timer:
            self.exam_timer.cancel()
            self.exam_timer = None

        # 清理事件绑定
        self.cleanup_event_bindings()

    def cleanup_event_bindings(self):
        """清理事件绑定"""
        try:
            # 清理选项按钮的事件绑定
            if hasattr(self, 'ids') and self.ids and 'options_container' in self.ids:
                for child in self.ids.options_container.children:
                    if hasattr(child, 'unbind'):
                        # 尝试解绑常见的事件
                        child.unbind(on_press=self.select_option)
        except Exception as e:
            print(f"清理事件绑定时出错: {e}")

    def start_timer(self):
        """开始考试计时 - 安全版本"""
        if not self._is_active:
            return

        def update_timer(dt):
            # 检查屏幕是否仍然活跃
            if not self._is_active or not hasattr(self, 'exam_start_time') or not self.exam_start_time:
                return

            try:
                elapsed = time.time() - self.exam_start_time
                remaining = max(0, self.exam_duration - elapsed)

                minutes = int(remaining // 60)
                seconds = int(remaining % 60)

                if hasattr(self, 'ids') and self.ids and 'timer_label' in self.ids:
                    self.ids.timer_label.text = f"剩余时间: {minutes:02d}:{seconds:02d}"

                if remaining <= 0:
                    self.submit_exam()

            except Exception as e:
                print(f"更新计时器时出错: {e}")

        # 取消之前的计时器（如果存在）
        if hasattr(self, 'exam_timer') and self.exam_timer:
            self.exam_timer.cancel()

        self.exam_timer = Clock.schedule_interval(update_timer, 1)

    def load_user_data(self):
        """加载用户数据"""
        self.user_data_file = "user_data.json"
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, 'r', encoding='utf-8') as f:
                    self.user_data = json.load(f)
            except Exception as e:
                print(f"加载用户数据时出错: {e}")
                self.user_data = {}
        else:
            self.user_data = {}

    def save_user_data(self):
        """保存用户数据"""
        try:
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户数据时出错: {e}")

    def start_exam(self):
        """开始考试"""
        app = App.get_running_app()

        # 加载所有题目
        all_questions = self.load_all_questions()
        if not all_questions:
            app.show_message("题库中没有足够的题目进行考试")
            self.go_back()
            return

        # 按题型分类
        single_questions = [q for q in all_questions if q.q_type == "单选题"]
        multi_questions = [q for q in all_questions if q.q_type == "多选题"]
        judgment_questions = [q for q in all_questions if q.q_type == "判断题"]

        # 检查题目数量
        if len(single_questions) < 20 or len(multi_questions) < 20 or len(judgment_questions) < 10:
            app.show_message("题库题目数量不足，无法开始考试")
            self.go_back()
            return

        # 随机选择题目
        exam_single = random.sample(single_questions, 20)
        exam_multi = random.sample(multi_questions, 20)
        exam_judgment = random.sample(judgment_questions, 10)

        self.exam_questions = exam_single + exam_multi + exam_judgment
        random.shuffle(self.exam_questions)

        self.current_question_index = 0
        self.exam_answers = {}
        self.exam_start_time = time.time()

        # 开始计时
        self.start_timer()
        self.load_question(0)

    def load_all_questions(self):
        """加载所有题目"""
        questions = []
        question_bank_path = "题库"
        if not os.path.exists(question_bank_path):
            return questions

        excel_files = []
        for f in os.listdir(question_bank_path):
            if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$'):
                excel_files.append(f)

        for file in excel_files:
            try:
                file_path = os.path.join(question_bank_path, file)
                df_dict = pd.read_excel(file_path, sheet_name=None, header=None)

                for sheet_name, df in df_dict.items():
                    for index, row in df.iterrows():
                        try:
                            question = Question(row, file)
                            if (question.q_type and question.question and
                                    question.correct_answer and
                                    question.q_type in ["单选题", "多选题", "判断题"]):
                                questions.append(question)
                        except:
                            continue
            except:
                continue

        return questions

    def load_question(self, index):
        if index < 0 or index >= len(self.exam_questions):
            return

        self.current_question_index = index
        question = self.exam_questions[index]

        question_text = f"{question.q_type}\n\n{question.question}"
        self.ids.question_label.text = question_text
        self.ids.progress_label.text = f"第{index + 1}题/共{len(self.exam_questions)}题"

        options_container = self.ids.options_container
        options_container.clear_widgets()
        self.selected_options = []

        sorted_options = sorted(question.options.items())
        for letter, option_text in sorted_options:
            # 使用格式化文本确保左对齐
            formatted_text = f"{letter}. {option_text}"
            btn = ToggleButton(
                text=formatted_text,
                font_size='16sp',
                size_hint_y=None,
                height=dp(60),
                background_color=(0.9, 0.9, 0.9, 1),
                background_normal='',
                color=(0, 0, 0, 1),
                group='options' if question.q_type != "多选题" else None,
                halign='left',
                text_size=(self.width - dp(20), None),
                padding=[dp(10), 0],
                size_hint_x=1,
                valign='middle',
                shorten=False
            )
            btn.option_letter = letter
            btn.bind(on_press=self.select_option)
            options_container.add_widget(btn)

        # 恢复之前的选择
        if question.id in self.exam_answers:
            previous_answer = self.exam_answers[question.id]
            for child in options_container.children:
                if child.option_letter in previous_answer:
                    child.state = 'down'
                    child.background_color = (0.2, 0.6, 0.8, 1)
                    if child.option_letter not in self.selected_options:
                        self.selected_options.append(child.option_letter)

    def select_option(self, instance):
        question = self.exam_questions[self.current_question_index]

        if question.q_type == "多选题":
            if instance.state == 'down':
                if instance.option_letter not in self.selected_options:
                    self.selected_options.append(instance.option_letter)
                instance.background_color = (0.2, 0.6, 0.8, 1)
            else:
                if instance.option_letter in self.selected_options:
                    self.selected_options.remove(instance.option_letter)
                instance.background_color = (0.9, 0.9, 0.9, 1)
        else:
            for child in self.ids.options_container.children:
                child.state = 'normal'
                child.background_color = (0.9, 0.9, 0.9, 1)

            instance.state = 'down'
            instance.background_color = (0.2, 0.6, 0.8, 1)
            self.selected_options = [instance.option_letter]

        # 保存答案
        self.save_answer()

    def save_answer(self):
        """保存当前题目的答案"""
        if self.selected_options:
            question = self.exam_questions[self.current_question_index]
            user_answer = "".join(sorted(self.selected_options))
            self.exam_answers[question.id] = user_answer

    def submit_answer(self):
        """提交答案"""
        if not self.selected_options:
            app = App.get_running_app()
            app.show_message("请先选择一个答案")
            return

        # 保存当前答案
        self.save_answer()

        # 提交考试
        self.submit_exam()

    def prev_question(self):
        if self.current_question_index > 0:
            self.save_answer()
            self.load_question(self.current_question_index - 1)

    def next_question(self):
        if self.current_question_index < len(self.exam_questions) - 1:
            self.save_answer()
            self.load_question(self.current_question_index + 1)

    def submit_exam(self):
        """提交考试"""
        self.save_answer()

        # 停止计时器
        if self.exam_timer:
            self.exam_timer.cancel()

        # 计算成绩
        total_score = 0
        correct_count = 0

        for question in self.exam_questions:
            if question.id in self.exam_answers:
                user_answer = self.exam_answers[question.id]
                is_correct = question.is_correct(user_answer)

                # 记录答题情况
                self.record_answer(question, user_answer, is_correct)

                if is_correct:
                    correct_count += 1
                    if question.q_type == "单选题":
                        total_score += 1
                    elif question.q_type == "多选题":
                        total_score += 2
                    elif question.q_type == "判断题":
                        total_score += 0.5

        # 显示考试结果
        self.show_exam_result(total_score, correct_count)

    def record_answer(self, question, user_answer, is_correct):
        """记录答题情况"""
        if question.id not in self.user_data:
            self.user_data[question.id] = {
                "total_count": 0,
                "correct_count": 0,
                "wrong_count": 0,
                "last_answer": "",
                "is_wrong": False
            }

        data = self.user_data[question.id]
        data["total_count"] = data.get("total_count", 0) + 1
        data["last_answer"] = user_answer

        if is_correct:
            data["correct_count"] = data.get("correct_count", 0) + 1
            data["is_wrong"] = False
        else:
            data["wrong_count"] = data.get("wrong_count", 0) + 1
            data["is_wrong"] = True

        self.save_user_data()

    def show_exam_result(self, total_score, correct_count):
        """显示考试结果弹窗"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        content.add_widget(Label(text="考试完成！", font_size='24sp', color=(0.2, 0.4, 0.6, 1)))

        # 成绩统计
        stats_text = f"考试成绩: {total_score} 分\n\n"
        stats_text += f"单选题: 20题 × 1分 = 20分\n"
        stats_text += f"多选题: 20题 × 2分 = 40分\n"
        stats_text += f"判断题: 10题 × 0.5分 = 5分\n"
        stats_text += f"满分: 65分\n\n"
        stats_text += f"答对题数: {correct_count}/{len(self.exam_questions)}"
        stats_label = Label(text=stats_text, font_size='18sp', color=(0, 0, 0, 1))
        content.add_widget(stats_label)

        # 按钮布局
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.3)
        retry_btn = Button(text='重新考试', background_color=(0.2, 0.6, 0.8, 1), background_normal='',
                           color=(1, 1, 1, 1))
        menu_btn = Button(text='返回主菜单', background_color=(0.8, 0.2, 0.2, 1), background_normal='',
                          color=(1, 1, 1, 1))

        def go_to_retry(instance):
            popup.dismiss()
            self.start_exam()

        def go_to_menu(instance):
            popup.dismiss()
            App.get_running_app().switch_to_main()

        retry_btn.bind(on_press=go_to_retry)
        menu_btn.bind(on_press=go_to_menu)
        btn_layout.add_widget(retry_btn)
        btn_layout.add_widget(menu_btn)
        content.add_widget(btn_layout)

        # 创建弹窗（删除重复的background_color）
        popup = Popup(
            title='考试结果',
            content=content,
            size_hint=(0.85, 0.7),
            background_color=(1, 1, 1, 1)  # 仅保留一个background_color
        )
        popup.open()

    def go_back(self):
        # 确认是否退出考试
        app = App.get_running_app()

        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text='确定要退出考试吗？\n当前进度将不会保存。'))

        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.3)

        confirm_btn = Button(text='确定退出', background_color=(0.8, 0.2, 0.2, 1))
        cancel_btn = Button(text='继续考试', background_color=(0.2, 0.6, 0.8, 1))

        def confirm_exit(instance):
            popup.dismiss()
            if self.exam_timer:
                self.exam_timer.cancel()
            app.switch_to_main()

        def cancel_exit(instance):
            popup.dismiss()

        confirm_btn.bind(on_press=confirm_exit)
        cancel_btn.bind(on_press=cancel_exit)

        btn_layout.add_widget(confirm_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='退出确认', content=content, size_hint=(0.7, 0.4))
        popup.open()


class ReviewScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_question_index = 0
        self.wrong_questions = []
        self.selected_options = []

    def on_pre_enter(self):
        self.load_wrong_questions()
        if self.wrong_questions:
            self.load_question(0)
        else:
            self.ids.question_label.text = "目前没有错题需要复习"
            self.ids.progress_label.text = "无错题"
            self.ids.options_container.clear_widgets()

    def update_option_text_size(self, instance, value):
        """更新选项按钮的文本尺寸，确保左对齐"""
        # 设置文本尺寸，留出左边距
        instance.text_size = (instance.width - dp(20), instance.height)
        instance.halign = 'left'
        instance.valign = 'middle'

    def load_wrong_questions(self):
        """加载错题"""
        user_data_file = "user_data.json"
        if not os.path.exists(user_data_file):
            return

        try:
            with open(user_data_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
        except:
            return

        # 加载所有题目
        all_questions = self.load_all_questions()
        self.wrong_questions = []

        for question in all_questions:
            if question.id in user_data and user_data[question.id].get("is_wrong", False):
                self.wrong_questions.append(question)

    def load_all_questions(self):
        """加载所有题目"""
        questions = []
        question_bank_path = "题库"
        if not os.path.exists(question_bank_path):
            return questions

        excel_files = []
        for f in os.listdir(question_bank_path):
            if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$'):
                excel_files.append(f)

        for file in excel_files:
            try:
                file_path = os.path.join(question_bank_path, file)
                df_dict = pd.read_excel(file_path, sheet_name=None, header=None)

                for sheet_name, df in df_dict.items():
                    for index, row in df.iterrows():
                        try:
                            question = Question(row, file)
                            if (question.q_type and question.question and
                                    question.correct_answer and
                                    question.q_type in ["单选题", "多选题", "判断题"]):
                                questions.append(question)
                        except:
                            continue
            except:
                continue

        return questions

    def load_question(self, index):
        """加载指定索引的题目 - 修复文字对齐问题"""
        if index < 0 or index >= len(self.wrong_questions):
            self.show_complete_message()
            return

        self.current_question_index = index
        question = self.wrong_questions[index]
        self.selected_options = []  # 重置选择

        # 更新题目
        question_text = f"{question.q_type}\n\n{question.question}"
        self.ids.question_label.text = question_text
        self.ids.progress_label.text = f"错题复习 第{index + 1}题/共{len(self.wrong_questions)}题"

        # 清空选项容器
        options_container = self.ids.options_container
        options_container.clear_widgets()

        # 添加选项 - 使用专门的选项按钮样式
        sorted_options = sorted(question.options.items())
        for letter, option_text in sorted_options:
            # 创建选项按钮，确保文字左对齐且在同一行
            btn = ToggleButton(
                text=f"{letter}. {option_text}",
                font_size='16sp',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.9, 0.9, 0.9, 1),
                background_normal='',
                color=(0, 0, 0, 1),
                group='options' if question.q_type != "多选题" else None,
                # 关键修改：确保左对齐和单行显示
                halign='left',
                valign='middle',
                text_size=(None, None),  # 不限制文本大小，让文本自然显示
                size_hint_x=1,  # 确保按钮占满宽度
                padding=[dp(10), dp(5)],  # 调整内边距
                shorten=False,  # 禁止文本缩短
                max_lines=1  # 限制为单行
            )

            # 手动设置文本尺寸，确保左对齐
            btn.bind(texture_size=self.update_option_text_size)
            btn.bind(size=self.update_option_text_size)

            btn.option_letter = letter
            btn.bind(on_press=self.select_option)
            options_container.add_widget(btn)

        # 显示解析区域
        if question.analysis:
            # 创建解析容器
            analysis_container = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(80),
                padding=[dp(5), dp(5)]
            )

            # 解析标题
            analysis_title = Label(
                text="解析:",
                font_size='14sp',
                color=(0.2, 0.2, 0.8, 1),
                size_hint_y=None,
                height=dp(20),
                halign='left',
                text_size=(None, None)
            )
            analysis_container.add_widget(analysis_title)

            # 解析内容
            analysis_content = Label(
                text=question.analysis,
                font_size='14sp',
                color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(60),
                text_size=(Window.width - dp(40), None),
                halign='left',
                valign='top'
            )
            analysis_container.add_widget(analysis_content)

            options_container.add_widget(analysis_container)

    def select_option(self, instance):
        """选择选项 - 修复选择功能"""
        question = self.wrong_questions[self.current_question_index]

        if question.q_type == "多选题":
            # 多选题：可以选中多个选项
            if instance.option_letter in self.selected_options:
                # 取消选中
                self.selected_options.remove(instance.option_letter)
                instance.background_color = (0.9, 0.9, 0.9, 1)  # 灰色
            else:
                # 选中
                self.selected_options.append(instance.option_letter)
                instance.background_color = (0.2, 0.6, 0.8, 1)  # 蓝色
        else:
            # 单选题和判断题：只能选中一个选项
            # 清除之前的选择
            for child in self.ids.options_container.children:
                if hasattr(child, 'option_letter'):  # 只处理选项按钮，不处理解析区域
                    child.background_color = (0.9, 0.9, 0.9, 1)  # 灰色
                    child.state = 'normal'

            # 标记当前选择
            self.selected_options = [instance.option_letter]
            instance.background_color = (0.2, 0.6, 0.8, 1)  # 蓝色
            instance.state = 'down'

    def next_question(self):
        """下一题 - 添加答案检查功能"""
        if not self.selected_options:
            app = App.get_running_app()
            app.show_message("请先选择一个答案")
            return

        # 检查当前题目的答案
        question = self.wrong_questions[self.current_question_index]
        user_answer = "".join(sorted(self.selected_options))
        is_correct = question.is_correct(user_answer)

        # 显示答题结果
        app = App.get_running_app()

        # 创建结果弹窗内容
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))

        result_text = "✅ 回答正确！" if is_correct else "❌ 回答错误"
        result_label = Label(text=result_text, font_size='16sp',
                             color=(0, 0.6, 0, 1) if is_correct else (0.8, 0, 0, 1))
        content.add_widget(result_label)

        # 显示正确答案
        if question.q_type == "多选题":
            correct_answer_text = '、'.join(list(question.correct_answer))
        else:
            correct_answer_text = question.correct_answer

        correct_label = Label(text=f"正确答案: {correct_answer_text}",
                              color=(0, 0, 0, 1), font_size='14sp')
        content.add_widget(correct_label)

        # 显示解析（如果有）
        if question.analysis:
            analysis_container = ScrollView(size_hint_y=None, height=dp(160))
            analysis_label = Label(
                text=f"解析: {question.analysis}",
                font_size='14sp',
                color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                text_size=(Window.width - dp(100), None),
                halign='left',
                valign='top',
                padding=[dp(10), dp(5)],
                max_lines=12
            )
            analysis_container.add_widget(analysis_label)
            content.add_widget(analysis_container)

        # 添加继续按钮
        continue_btn = Button(
            text='继续下一题',
            size_hint_y=0.3,
            background_color=(0.2, 0.6, 0.8, 1),
            background_normal='',
            color=(1, 1, 1, 1)
        )

        def continue_to_next(instance):
            popup.dismiss()
            # 延迟加载下一题，确保弹窗完全关闭
            Clock.schedule_once(lambda dt: self.load_next_question_after_answer(), 0.1)

        continue_btn.bind(on_press=continue_to_next)
        content.add_widget(continue_btn)

        popup = Popup(
            title='答题结果',
            content=content,
            size_hint=(0.8, 0.6),
            background_color=(1, 1, 1, 1)
        )
        popup.open()

    def load_next_question_after_answer(self):
        """在回答后加载下一题"""
        self.load_question(self.current_question_index + 1)

    def show_complete_message(self):
        """显示复习完成消息"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content.add_widget(Label(text="错题复习完成！", font_size='24sp', color=(0.2, 0.6, 0.2, 1)))

        if len(self.wrong_questions) > 0:
            content.add_widget(Label(
                text=f"本次共复习了 {len(self.wrong_questions)} 道错题",
                font_size='18sp',
                color=(0, 0, 0, 1)
            ))
        else:
            content.add_widget(Label(
                text="暂无错题需要复习",
                font_size='18sp',
                color=(0, 0, 0, 1)
            ))

        btn = Button(
            text='返回主菜单',
            size_hint_y=0.3,
            background_color=(0.2, 0.6, 0.8, 1),
            background_normal='',
            color=(1, 1, 1, 1)
        )
        btn.bind(on_press=lambda x: self.go_back())
        content.add_widget(btn)

        popup = Popup(
            title='复习完成',
            content=content,
            size_hint=(0.8, 0.5),
            background_color=(1, 1, 1, 1)
        )
        popup.open()

    def go_back(self):
        """返回主菜单"""
        app = App.get_running_app()
        app.switch_to_main()

class StatsScreen(Screen):
    def on_pre_enter(self):
        self.update_stats()

    def update_stats(self):
        stats = QuestionStatistics()
        file_stats, total_sheets, total_questions = stats.get_statistics()

        stats_text = "📊 题库统计信息\n\n"

        if not file_stats:
            stats_text += "暂无题库数据\n\n"
            stats_text += "请在应用目录下创建'题库'文件夹，\n并将Excel题库文件放入其中。"
        else:
            stats_text += f"总题数: {total_questions} 道\n"
            stats_text += f"文件数: {len(file_stats)} 个\n"
            stats_text += f"工作表数: {total_sheets} 个\n\n"

            total_single = sum(s['single'] for s in file_stats.values())
            total_multi = sum(s['multi'] for s in file_stats.values())
            total_judgment = sum(s['judgment'] for s in file_stats.values())

            stats_text += f"单选题: {total_single} 道\n"
            stats_text += f"多选题: {total_multi} 道\n"
            stats_text += f"判断题: {total_judgment} 道\n\n"

            stats_text += "📁 文件详情:\n\n"
            for file_name, stat in file_stats.items():
                stats_text += f"📄 {file_name}:\n"
                stats_text += f"  总题数: {stat['total']} 道\n"
                stats_text += f"  单选题: {stat['single']} 道\n"
                stats_text += f"  多选题: {stat['multi']} 道\n"
                stats_text += f"  判断题: {stat['judgment']} 道\n\n"

        # 安全地更新标签文本
        if hasattr(self, 'ids') and 'stats_label' in self.ids:
            self.ids.stats_label.text = stats_text
        else:
            print("警告: stats_label 不存在")

    def go_back(self):
        app = App.get_running_app()
        app.switch_to_main()

class ProgressScreen(Screen):
    def on_pre_enter(self):
        self.update_progress()

    def update_progress(self):
        user_data_file = "user_data.json"
        if not os.path.exists(user_data_file):
            progress_text = "暂无学习进度数据\n\n开始练习后将会记录您的学习进度"
            if hasattr(self, 'ids') and 'progress_label' in self.ids:
                self.ids.progress_label.text = progress_text
            return

        try:
            with open(user_data_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
        except:
            progress_text = "加载学习进度失败"
            if hasattr(self, 'ids') and 'progress_label' in self.ids:
                self.ids.progress_label.text = progress_text
            return

        # 统计学习进度
        all_questions = self.load_all_questions()
        total_questions = len(all_questions)
        practiced_questions = len([qid for qid, data in user_data.items() if data.get("total_count", 0) > 0])

        total_count = sum(data.get("total_count", 0) for data in user_data.values())
        correct_count = sum(data.get("correct_count", 0) for data in user_data.values())
        wrong_count = sum(data.get("wrong_count", 0) for data in user_data.values())

        wrong_questions = len([qid for qid, data in user_data.items() if data.get("is_wrong", False)])

        progress_text = "📈 学习进度统计\n\n"
        progress_text += f"题库总量: {total_questions} 道\n"
        progress_text += f"已练习题: {practiced_questions} 道\n"
        progress_text += f"未练习题: {total_questions - practiced_questions} 道\n\n"

        progress_text += f"总答题次数: {total_count} 次\n"
        progress_text += f"答对次数: {correct_count} 次\n"
        progress_text += f"答错次数: {wrong_count} 次\n\n"

        if total_count > 0:
            accuracy = correct_count / total_count * 100
            progress_text += f"总体正确率: {accuracy:.1f}%\n\n"
        else:
            progress_text += f"总体正确率: 0%\n\n"

        progress_text += f"当前错题数: {wrong_questions} 道\n"

        if wrong_questions > 0:
            progress_text += "\n建议重点复习错题，提高学习效果！"

        if hasattr(self, 'ids') and 'progress_label' in self.ids:
            self.ids.progress_label.text = progress_text

    def load_all_questions(self):
        """加载所有题目 - 使用基类实现"""
        # 从base_screen导入ProgressScreenBase类
        from base_screen import ProgressScreenBase
        base = ProgressScreenBase()
        return base.load_all_questions()

    def go_back(self):
        app = App.get_running_app()
        app.switch_to_main()

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = {}
        self.setting_inputs = {}

    def on_pre_enter(self):
        self.load_settings()
        self.create_settings_ui()

    def load_settings(self):
        """加载设置 - 使用基类实现"""
        from base_screen import SettingsScreenBase
        base = SettingsScreenBase()
        base.load_settings()
        self.settings = base.settings

    def create_settings_ui(self):
        """创建设置界面"""
        container = self.ids.settings_container
        container.clear_widgets()

        # 练习设置
        title1 = Label(text='练习设置', font_size='20sp', color=(0.2, 0.4, 0.6, 1),
                       size_hint_y=None, height=dp(40))
        container.add_widget(title1)

        # 每次练习题目数量
        label1 = Label(text='每次练习题目数量:', size_hint_y=None, height=dp(30))
        container.add_widget(label1)

        question_count_input = TextInput(
            text=str(self.settings.get('question_count', 50)),
            multiline=False,
            input_type='number',
            size_hint_y=None,
            height=dp(40)
        )
        self.setting_inputs['question_count'] = question_count_input
        container.add_widget(question_count_input)

        # 自动下一题延迟
        label_delay = Label(text='自动下一题延迟(秒):', size_hint_y=None, height=dp(30))
        container.add_widget(label_delay)

        delay_input = TextInput(
            text=str(self.settings.get('auto_next_delay', 3)),
            multiline=False,
            input_type='number',
            size_hint_y=None,
            height=dp(40)
        )
        self.setting_inputs['auto_next_delay'] = delay_input
        container.add_widget(delay_input)

        # 考试设置
        title2 = Label(text='考试设置', font_size='20sp', color=(0.2, 0.4, 0.6, 1),
                       size_hint_y=None, height=dp(40))
        container.add_widget(title2)

        # 单选题数量
        label2 = Label(text='单选题数量:', size_hint_y=None, height=dp(30))
        container.add_widget(label2)

        single_count_input = TextInput(
            text=str(self.settings.get('exam_single_count', 20)),
            multiline=False,
            input_type='number',
            size_hint_y=None,
            height=dp(40)
        )
        self.setting_inputs['exam_single_count'] = single_count_input
        container.add_widget(single_count_input)

        # 多选题数量
        label3 = Label(text='多选题数量:', size_hint_y=None, height=dp(30))
        container.add_widget(label3)

        multi_count_input = TextInput(
            text=str(self.settings.get('exam_multi_count', 20)),
            multiline=False,
            input_type='number',
            size_hint_y=None,
            height=dp(40)
        )
        self.setting_inputs['exam_multi_count'] = multi_count_input
        container.add_widget(multi_count_input)

        # 判断题数量
        label4 = Label(text='判断题数量:', size_hint_y=None, height=dp(30))
        container.add_widget(label4)

        judgment_count_input = TextInput(
            text=str(self.settings.get('exam_judgment_count', 10)),
            multiline=False,
            input_type='number',
            size_hint_y=None,
            height=dp(40)
        )
        self.setting_inputs['exam_judgment_count'] = judgment_count_input
        container.add_widget(judgment_count_input)

        # 界面设置
        title3 = Label(text='界面设置', font_size='20sp', color=(0.2, 0.4, 0.6, 1),
                       size_hint_y=None, height=dp(40))
        container.add_widget(title3)

        # 字体大小
        label5 = Label(text='字体大小:', size_hint_y=None, height=dp(30))
        container.add_widget(label5)

        font_size_input = TextInput(
            text=str(self.settings.get('font_size', 16)),
            multiline=False,
            input_type='number',
            size_hint_y=None,
            height=dp(40)
        )
        self.setting_inputs['font_size'] = font_size_input
        container.add_widget(font_size_input)

    def save_settings(self):
        """保存设置 - 使用基类实现"""
        from base_screen import SettingsScreenBase
        base = SettingsScreenBase()
        base.settings_file = "app_settings.json"
        success = base.save_settings(self.setting_inputs)
        
        if success:
            app = App.get_running_app()
            app.show_message("设置已保存！")
        else:
            app = App.get_running_app()
            app.show_message("保存设置时出错")

    def go_back(self):
        app = App.get_running_app()
        app.switch_to_main()

class MobileExamApp(App):
    font_loaded = False
    chinese_font_name = "Roboto"
    QuestionClass = Question  # 为base_screen.py提供Question类引用

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = {}
        self.load_app_settings()
        self.init_font()

    def build(self):
        # 先初始化字体，确保在KV加载前完成
        self.init_font()
        self.title = "智能试题练习系统"
        print(f"应用字体: {self.chinese_font_name}, 加载状态: {self.font_loaded}")

        # 创建屏幕管理器
        self.screen_manager = ScreenManager()

        # 创建各个屏幕
        self.main_screen = MainScreen(name='main')
        self.practice_screen = PracticeScreen(name='practice')
        self.exam_screen = ExamScreen(name='exam')
        self.review_screen = ReviewScreen(name='review')
        self.stats_screen = StatsScreen(name='stats')
        self.progress_screen = ProgressScreen(name='progress')
        self.settings_screen = SettingsScreen(name='settings')

        # 添加到屏幕管理器
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.practice_screen)
        self.screen_manager.add_widget(self.exam_screen)
        self.screen_manager.add_widget(self.review_screen)
        self.screen_manager.add_widget(self.stats_screen)
        self.screen_manager.add_widget(self.progress_screen)
        self.screen_manager.add_widget(self.settings_screen)

        return self.screen_manager

    def init_font(self):
        """初始化字体"""
        # 尝试加载中文字体
        font_name = load_chinese_font()

        if font_name == "Roboto":
            # 如果Roboto字体也无法显示中文，使用内置字体
            print("⚠️ 使用系统默认字体，可能无法显示中文")

            # 在Android上尝试使用Droid Sans Fallback
            if platform.system().lower() == 'android':
                self.chinese_font_name = 'Droid Sans Fallback'
            else:
                self.chinese_font_name = 'Roboto'
        else:
            self.chinese_font_name = font_name
            self.font_loaded = True

        print(f"最终使用的字体: {self.chinese_font_name}")

    # 在MobileExamApp类中
    def load_app_settings(self):
        """加载应用设置 - 使用配置常量"""
        from config import AppConfig

        if os.path.exists(AppConfig.APP_SETTINGS_FILE):
            try:
                with open(AppConfig.APP_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                # 确保所有设置项都存在
                default_settings = AppConfig.get_default_settings()
                for key, value in default_settings.items():
                    if key not in self.settings:
                        self.settings[key] = value
            except:
                self.settings = AppConfig.get_default_settings()
        else:
            self.settings = AppConfig.get_default_settings()

    # 在窗口设置部分
    from config import AppConfig

    # 替换原来的设置
    if platform.system() != 'Android':
        Window.size = AppConfig.WINDOW_SIZE
    Window.clearcolor = AppConfig.WINDOW_BG_COLOR

    def switch_to_main(self):
        """切换到主屏幕"""
        self.screen_manager.current = 'main'

    def switch_to_practice(self):
        """切换到练习屏幕"""
        self.screen_manager.current = 'practice'

    def switch_to_exam(self):
        """切换到考试屏幕"""
        self.screen_manager.current = 'exam'

    def switch_to_review(self):
        """切换到复习屏幕"""
        self.screen_manager.current = 'review'

    def switch_to_stats(self):
        """切换到统计屏幕"""
        self.screen_manager.current = 'stats'

    def switch_to_progress(self):
        """切换到进度屏幕"""
        self.screen_manager.current = 'progress'

    def switch_to_settings(self):
        """切换到设置屏幕"""
        self.screen_manager.current = 'settings'

    def show_loading(self, message):
        """显示加载提示"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        label = Label(text=message, color=(0, 0, 0, 1))
        content.add_widget(label)

        content.add_widget(ProgressBar())

        self.loading_popup = Popup(
            title='请稍候',
            content=content,
            size_hint=(0.8, 0.3),
            background_color=(1, 1, 1, 1)
        )
        self.loading_popup.open()

    def hide_loading(self):
        """隐藏加载提示"""
        if hasattr(self, 'loading_popup'):
            self.loading_popup.dismiss()

    def show_message(self, message):
        """显示消息提示"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        label = Label(text=message, color=(0, 0, 0, 1))
        content.add_widget(label)

        btn = Button(
            text='确定',
            size_hint=(1, 0.3),
            background_color=(0.2, 0.6, 0.8, 1),
            background_normal='',
            color=(1, 1, 1, 1)
        )

        popup = Popup(
            title='提示',
            content=content,
            size_hint=(0.8, 0.4),
            background_color=(1, 1, 1, 1)
        )

        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def show_answer_result(self, is_correct, user_answer, question):
        """显示答题结果"""
        result_text = "✅ 回答正确！" if is_correct else "❌❌ 回答错误"

        # 处理用户答案显示
        if question.q_type == "多选题":
            user_answer_text = '、'.join(list(user_answer))
        else:
            user_answer_text = user_answer

        # 处理正确答案显示
        if question.q_type == "多选题":
            correct_answer_text = '、'.join(list(question.correct_answer))
        else:
            correct_answer_text = question.correct_answer

        # 创建内容布局
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        # 结果标签
        result_label = Label(
            text=result_text,
            font_size='18sp',
            color=(0, 0.6, 0, 1) if is_correct else (0.8, 0, 0, 1),
            bold=True
        )
        content.add_widget(result_label)

        # 正确答案标签
        correct_label = Label(
            text=f"正确答案: {correct_answer_text}",
            font_size='16sp',
            color=(0, 0, 0, 1)
        )
        content.add_widget(correct_label)

        # 用户答案标签
        user_label = Label(
            text=f"你的答案: {user_answer_text}",
            font_size='16sp',
            color=(0, 0, 0, 1)
        )
        content.add_widget(user_label)

        # 解析标签 - 使用ScrollView确保长文本可滚动
        if question.analysis:
            analysis_container = ScrollView(size_hint_y=None, height=dp(120))
            analysis_label = Label(
                text=f"解析: {question.analysis}",
                font_size='14sp',
                color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                text_size=(Window.width - dp(60), None),
                halign='left',
                valign='top',
                padding=[dp(10), dp(5)]
            )
            analysis_container.add_widget(analysis_label)
            content.add_widget(analysis_container)

        # 按钮布局
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint=(1, 0.25))

        next_btn = Button(
            text='下一题',
            background_color=(0.2, 0.8, 0.2, 1),
            background_normal='',
            color=(1, 1, 1, 1),
            font_size='16sp',
            size_hint_x=0.5
        )

        menu_btn = Button(
            text='返回菜单',
            background_color=(0.8, 0.2, 0.2, 1),
            background_normal='',
            color=(1, 1, 1, 1),
            font_size='16sp',
            size_hint_x=0.5
        )

        def go_to_next_question(instance):
            self.hide_result()
            # 直接调用练习屏幕的next_question方法
            practice_screen = self.screen_manager.get_screen('practice')
            Clock.schedule_once(lambda dt: practice_screen.next_question(), 0.1)

        def go_to_menu(instance):
            self.hide_result()
            self.switch_to_main()

        next_btn.bind(on_press=go_to_next_question)
        menu_btn.bind(on_press=go_to_menu)

        btn_layout.add_widget(next_btn)
        btn_layout.add_widget(menu_btn)
        content.add_widget(btn_layout)

        # 创建弹窗 - 增大尺寸并使用更明亮的背景色
        self.result_popup = Popup(
            title='答题结果',
            content=content,
            size_hint=(0.95, 0.7),
            background_color=(0.98, 0.98, 0.98, 1),
            auto_dismiss=False
        )
        self.result_popup.open()

    def hide_result(self):
        """隐藏结果提示"""
        if hasattr(self, 'result_popup'):
            self.result_popup.dismiss()


if __name__ == '__main__':
    # 检查并创建必要的目录
    if not os.path.exists('题库'):
        os.makedirs('题库')

    if not os.path.exists('fonts'):
        os.makedirs('fonts')
        print("⚠️ 请将中文字体文件（如simhei.ttf）放入fonts文件夹中")

    # 运行应用
    MobileExamApp().run()
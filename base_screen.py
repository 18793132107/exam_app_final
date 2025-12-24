import os
import json
import pandas as pd
import re
from kivy.uix.screenmanager import Screen
from kivy.app import App
from config import AppConfig


class BaseQuestionScreen(Screen):
    """题目屏幕基类，包含共用功能"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_data = {}
        self.user_data_file = "user_data.json"

    def load_user_data(self):
        """加载用户数据 - 共用实现"""
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, 'r', encoding='utf-8') as f:
                    self.user_data = json.load(f)
            except Exception as e:
                print(f"加载用户数据时出错: {e}")
                self.user_data = {}
        else:
            self.user_data = {}
        return self.user_data

    def save_user_data(self):
        """保存用户数据 - 共用实现"""
        try:
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存用户数据时出错: {e}")
            return False

    def load_all_questions(self):
        """加载所有题目 - 共用实现"""
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
                            # 通过App实例获取Question类
                            app = App.get_running_app()
                            question = app.QuestionClass(row, file)
                            if (question.q_type and question.question and
                                    question.correct_answer and
                                    question.q_type in ["单选题", "多选题", "判断题"]):
                                questions.append(question)
                        except Exception as e:
                            print(f"解析题目时出错: {e}")
                            continue
            except Exception as e:
                print(f"读取文件{file}时出错: {e}")
                continue

        return questions

    def record_answer(self, question, user_answer, is_correct):
        """记录答题情况 - 共用实现"""
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

        return self.save_user_data()


class ProgressScreenBase(Screen):
    """进度屏幕基类"""
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
                            # 通过App实例获取Question类
                            app = App.get_running_app()
                            question = app.QuestionClass(row, file)
                            if (question.q_type and question.question and
                                    question.correct_answer and
                                    question.q_type in ["单选题", "多选题", "判断题"]):
                                questions.append(question)
                        except Exception as e:
                            print(f"加载题目时出错: {e}")
                            continue
            except Exception as e:
                print(f"读取文件{file}时出错: {e}")
                continue

        return questions


class QuestionStatistics:
    def __init__(self, folder_path="题库"):
        self.folder_path = folder_path
        self.file_stats = {}
        self.total_questions = 0
        self.total_sheets = 0

    def extract_number_from_sheet_name(self, sheet_name):
        """从工作表名称中提取数字"""
        if not sheet_name or pd.isna(sheet_name):
            return 0

        sheet_name = str(sheet_name).strip()
        match = re.search(r'(\d+)$', sheet_name)
        if match:
            return int(match.group(1))

        matches = re.findall(r'\d+', sheet_name)
        if matches:
            return max(int(m) for m in matches)

        return 0

    def count_questions_by_type(self, df):
        """统计工作表中各题型的数量"""
        single_count = 0
        multi_count = 0
        judgment_count = 0
        total_rows = len(df)

        for index, row in df.iterrows():
            if len(row) > 0 and pd.notna(row.iloc[0]):
                cell_value = str(row.iloc[0]).strip()
                if cell_value == "单选题":
                    single_count += 1
                elif cell_value == "多选题":
                    multi_count += 1
                elif cell_value == "判断题":
                    judgment_count += 1

            if len(row) > 1 and pd.notna(row.iloc[1]):
                cell_value = str(row.iloc[1]).strip()
                if cell_value == "单选题":
                    single_count += 1
                elif cell_value == "多选题":
                    multi_count += 1
                elif cell_value == "判断题":
                    judgment_count += 1

        total_questions = single_count + multi_count + judgment_count

        # 校准逻辑
        if total_rows > 0 and abs(total_rows - 1 - total_questions) <= AppConfig.DUPLICATE_THRESHOLD:
            if total_questions > 0:
                ratio = (total_rows - 1) / total_questions
                single_count = int(single_count * ratio)
                multi_count = int(multi_count * ratio)
                judgment_count = (total_rows - 1) - single_count - multi_count

            else:
                single_count = total_rows - 1

        return single_count, multi_count, judgment_count, total_rows

    def get_statistics(self):
        """获取题库统计信息"""
        # 确保题库目录存在
        question_bank_path = "题库"
        if not os.path.exists(question_bank_path):
            # 尝试使用绝对路径
            question_bank_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "题库")
            if not os.path.exists(question_bank_path):
                # 如果都不存在则创建文件夹
                os.makedirs(question_bank_path)
                return {}, 0, 0

        excel_files = [f for f in os.listdir(question_bank_path)
                       if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$')]

        if not excel_files:
            return {}, 0, 0

        self.file_stats = {}
        self.total_sheets = 0
        self.total_questions = 0

        for file in excel_files:
            try:
                file_path = os.path.join(question_bank_path, file)
                self.file_stats[file] = {
                    'total': 0,
                    'single': 0,
                    'multi': 0,
                    'judgment': 0,
                    'sheets_checked': 0,
                    'total_rows': 0,
                    'sheets': []
                }

                df_dict = pd.read_excel(file_path, sheet_name=None, header=None)

                for sheet_name, df in df_dict.items():
                    self.file_stats[file]['sheets_checked'] += 1
                    self.total_sheets += 1

                    single, multi, judgment, rows = self.count_questions_by_type(df)
                    sheet_number = self.extract_number_from_sheet_name(sheet_name)

                    sheet_info = {
                        'name': sheet_name,
                        'rows': rows,
                        'single': single,
                        'multi': multi,
                        'judgment': judgment,
                        'total': single + multi + judgment,
                        'extracted_number': sheet_number
                    }

                    self.file_stats[file]['sheets'].append(sheet_info)
                    self.file_stats[file]['single'] += single
                    self.file_stats[file]['multi'] += multi
                    self.file_stats[file]['judgment'] += judgment
                    self.file_stats[file]['total_rows'] += rows

                self.file_stats[file]['total'] = (self.file_stats[file]['single'] +
                                                  self.file_stats[file]['multi'] +
                                                  self.file_stats[file]['judgment'])
                self.total_questions += self.file_stats[file]['total']

            except Exception as e:
                print(f"统计文件 {file} 时出错: {e}")
                continue

        return self.file_stats, self.total_sheets, self.total_questions


class SettingsScreenBase(Screen):
    """设置屏幕基类"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = {}
        self.setting_inputs = {}
        self.settings_file = "app_settings.json"

    def load_settings(self):
        """加载设置"""
        from config import AppConfig
        default_settings = AppConfig.get_default_settings()

        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                # 确保所有设置项都存在
                for key, value in default_settings.items():
                    if key not in self.settings:
                        self.settings[key] = value
            except:
                self.settings = default_settings
        else:
            self.settings = default_settings

    def save_settings(self, setting_inputs):
        """保存设置"""
        try:
            # 更新设置字典
            self.settings.update({
                'question_count': int(setting_inputs['question_count'].text),
                'exam_single_count': int(setting_inputs['exam_single_count'].text),
                'exam_multi_count': int(setting_inputs['exam_multi_count'].text),
                'exam_judgment_count': int(setting_inputs['exam_judgment_count'].text),
                'font_size': int(setting_inputs['font_size'].text),
                'auto_next_delay': int(setting_inputs['auto_next_delay'].text),
            })

            # 保存到文件
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存设置时出错：{str(e)}")
            return False
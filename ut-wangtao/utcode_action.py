import datetime
import hashlib
import json
# import logging
import os
import random
import re
import time
import traceback

import pandas
import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, QTranslator, Qt, QCoreApplication
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication, QProgressBar, QLabel
from json_minify import json_minify
from jsoncomment import JsonComment

from cache import cache
from config import config
from logger import logger as logging
from utcode_window import Ui_MainWindow
from ai_wenxin import chat as chat_wenxin
from ai_chatgpt import chat as chat_chatgpt


# fm = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s(%(funcName)s:%(lineno)d)] - %(message)s'"
# logging.basicConfig(level='DEBUG', filename='./log.txt', filemode='a+', format=fm)


def str_to_md5(txt):
    md5 = hashlib.md5(txt.encode(encoding='utf-8'))
    return str(md5.hexdigest())


class UtCodeActions(Ui_MainWindow):

    # 生成Prompt_text
    def __init__(self):
        self.response = None
        self.ai_ret = None

        self.inputs = pandas.DataFrame({'desc': [],
                                        'name': [],
                                        'value': [],
                                        'min': [],
                                        'max': []})
        self.outputs = pandas.DataFrame({'desc': [],
                                         'name': [],
                                         'value': [],
                                         'min': [],
                                         'max': []})
        self.dict_data = pandas.DataFrame()
        self.init_dict()
        self.trans = QTranslator()

    def gen_prompt(self):
        req_txt = self.req_txt.toPlainText()
        ret = self.get_param(req_txt)
        self.prompt_txt.setText(ret)

    # 提交AI处理
    def askai(self):
        txt = self.prompt_txt.toPlainText()
        if not txt:
            return

        md5_value = str_to_md5(txt)
        ai_rtn = cache.get_from_prompt_key(md5_value, self.ai_model_type)
        self.ai_ret = ai_rtn

        self.processing_label.setHidden(False)
        self.progressBar.setHidden(False)
        self.submit_ai_btn.setIcon(self.submit_ai_disable_icon)

        self.progress_update_thread = ProgressUpdateThread()
        self.progress_update_thread.progressChanged.connect(self.update_progress_bar)
        self.progress_update_thread.start()

        if ai_rtn:
            self.fake_request_thread = FakeRequestThread(md5_value, self.ai_model_type, ai_rtn)
            self.fake_request_thread.fake_request_complete.connect(self.request_thread_complete)
            self.fake_request_thread.start()
        else:

            self.request_thread = RequestOpenAIThread(txt, self.ai_model_type)
            self.request_thread.request_complete.connect(self.request_thread_complete)
            self.request_thread.start()

    def request_thread_complete(self, prompt_key, return_data):
        self.submit_ai_btn.setIcon(self.submit_ai_enable_icon)
        self.processing_label.setHidden(True)
        self.progressBar.setHidden(True)
        self.export_excel_btn.setCursor(QtGui.QCursor((QtCore.Qt.ArrowCursor)))
        self.update_json_btn.setCursor(QtGui.QCursor((QtCore.Qt.ArrowCursor)))

        self.progressBar.reset()
        if hasattr(self, 'progress_update_thread'):
            self.progress_update_thread.terminate()

        if return_data and return_data['status'] == 1:
            self.ai_ret = return_data['content']
            logging.info(return_data)
            self.test_case_txt.setText(return_data['content'])

            data = {
                'value': self.ai_ret,
                'ai_model_type': return_data['ai_model_type']
            }
            cache.put(prompt_key, data)

        else:
            self.ai_ret = cache.get_random()
            self.test_case_txt.setText(self.ai_ret)
            self.show_warning_message('Requesting AI Service Error. Load from cache')

    # 显示AI返回数据
    def show_ai_answer(self):
        if self.ai_ret == None:
            return
        self.test_case_txt.setText(self.ai_ret)

    # 将AI数据导出excel文件
    def export_excel(self):
        if self.ai_ret == None:
            # self.show_warning_message('Please submit AI first')
            return
        try:
            # 获取当前日期和时间
            now = datetime.datetime.now()
            # 使用strftime函数，将日期和时间格式化为字符串
            formatted_date = now.strftime("%Y%m%d_%H_%M_%S")
            # 使用格式化后的日期和时间，构造文件名
            filename = f"test_case_{formatted_date}.xlsx"
            initial_dir = os.getcwd()
            initial_dir += "./utcase/"
            file_dialog = QFileDialog()
            file_dialog.setDefaultSuffix('xls')
            export_path, _ = file_dialog.getSaveFileName(None, None, "", f"Text Files (*.xls)")
            if export_path == '':
                return

            json_obj = self.extract_subjson(self.ai_ret)
            tick = self.interval_time_txt.text()
            self.json_to_excel(json_obj, tick, export_path)
            # self.show_info_message('导出完成')
            self.show_confirm_message('导出完成，是否打开文件？', self.open_xlsx_file, [export_path])
        except Exception as e:
            logging.error(time.strftime('%y-%m-%d %H:%M:%S') + traceback.format_exc() + '-------------- \n')
            self.show_warning_message('导出文件失败')

    # 直接生成格式化的测试用例供人继续编辑
    def format_directly(self):
        try:
            txt = self.case_cnt_txt.text()
            n = int(txt)
            txt = ""
            result_str = ""
            tick = self.interval_time_txt.text()
            input_str = self.req_txt.toPlainText()
            self.init_param(input_str)
            for i in range(n):
                txt += f"//Case {i}\n"
                result_str += f"[{tick}]\n"
                for index, row in self.inputs.iterrows():
                    result_str += f"{row['name']}={row['value']}\n"
                for index, row in self.outputs.iterrows():
                    result_str += f"{row['name']}={row['value']}\n"
                result_str += "\n"
            self.test_case_txt.setText(result_str)

        except Exception as e:
            logging.error(time.strftime('%y-%m-%d %H:%M:%S') + traceback.format_exc() + '-------------- \n')
            self.show_warning_message('导出文件失败')

    def load_sample(self):
        with open('sample/req.txt', mode='r', encoding='utf-8') as f:
            txt = f.read()
        self.req_txt.setText(txt)
        with open('sample/aiAnswer.json', mode='r', encoding='utf-8') as f:
            txt = f.read()
        self.test_case_txt.setText(txt)
        self.ai_ret = txt
        self.ai_format_btn.setCursor(QtGui.QCursor((QtCore.Qt.ArrowCursor)))
        self.std_format_btn.setCursor(QtGui.QCursor((QtCore.Qt.ArrowCursor)))

    def show_std_case(self):
        if self.ai_ret == None:
            return
        system_txt = self.extract_subjson(self.ai_ret)
        tick = self.interval_time_txt.text()
        ret = self.json_to_txt(system_txt, tick)
        self.test_case_txt.setText(ret)

    def update_ai_answer(self):
        txt = self.test_case_txt.toPlainText()
        self.ai_ret = txt

    def extract_subjson(self, text):
        pattern = r'\{.*\}'
        result = re.search(pattern, text, re.S)
        return result.group()

    def init_dict(self):
        # 读取 Excel 文件
        excel_file = pandas.ExcelFile('dict.xls')

        # 遍历每个工作表并提取指定列数据
        for sheet_name in excel_file.sheet_names:
            # 读取工作表
            df = excel_file.parse(sheet_name)
            # print(df.columns)

            # 提取指定列数据
            columns = ['name', 'Description', 'Init', 'P-min', 'P-Max']
            df = df[columns]
            self.dict_data = pandas.concat([self.dict_data, df], ignore_index=True)

    def init_param(self, input_str):
        # 取得Output字符
        # 定义正则表达式
        pattern = r'\*(.*?)\*'
        # 使用正则表达式提取字符串
        self.inputs.drop(self.inputs.index, inplace=True)
        self.outputs.drop(self.outputs.index, inplace=True)

        self.inputs["desc"] = re.findall(pattern, input_str)
        self.inputs["desc"] = [x.strip() for x in self.inputs["desc"]]  # 去掉首尾空格
        self.inputs = self.inputs.drop_duplicates()
        desc_to_drop = []
        msg = ""
        for des in self.inputs["desc"]:
            result = self.dict_data.loc[self.dict_data['Description'].str.lower(
            ) == des.lower()]
            if not result.empty:
                self.inputs.loc[self.inputs['desc'] ==
                                des, 'name'] = result['name'].values[0]
                self.inputs.loc[self.inputs['desc'] ==
                                des, 'value'] = result['Init'].values[0]
                self.inputs.loc[self.inputs['desc'] ==
                                des, 'min'] = result['P-min'].values[0]
                self.inputs.loc[self.inputs['desc'] ==
                                des, 'max'] = result['P-Max'].values[0]
            else:
                msg += translate('input变量', context='message') + '[' +des + ']' + translate('不在字典数据中', context='message') + "\n"
                desc_to_drop.append(des)
        # 删除不在字典中的变量
        if len(desc_to_drop) > 0:
            idx_to_drop = self.inputs.loc[self.inputs['desc'].isin(desc_to_drop)].index
            self.inputs = self.inputs.drop(index=idx_to_drop)

        # 提取输出值
        pattern = r'\#(.*?)\#'
        self.outputs["desc"] = re.findall(pattern, input_str)
        self.outputs["desc"] = [x.strip() for x in self.outputs["desc"]]  # 去掉首尾空格
        self.outputs = self.outputs.drop_duplicates()
        desc_to_drop = []
        for des in self.outputs["desc"]:
            result = self.dict_data.loc[self.dict_data['Description'].str.lower(
            ) == des.lower()]
            if not result.empty:
                self.outputs.loc[self.outputs['desc'] ==
                                 des, 'name'] = result['name'].values[0]
                self.outputs.loc[self.outputs['desc'] ==
                                 des, 'value'] = result['Init'].values[0]
                self.outputs.loc[self.outputs['desc'] ==
                                 des, 'min'] = result['P-min'].values[0]
                self.outputs.loc[self.outputs['desc'] ==
                                 des, 'max'] = result['P-Max'].values[0]
            else:
                msg += f"output变量 {des} 不在字典数据中\n"
                desc_to_drop.append(des)
        # 删除不在字典中的变量
        if len(desc_to_drop) > 0:
            idx_to_drop = self.outputs.loc[self.inputs['desc'].isin(
                desc_to_drop)].index
            self.outputs = self.outputs.drop(index=idx_to_drop)
        if not msg == "":
            self.show_warning_message(msg)

    def get_param(self, input_str):
        self.init_param(input_str)
        input_str = input_str.replace('TBD', '')

        # 描述替换为值
        for index, row in self.inputs.iterrows():
            input_str = input_str.replace(row['desc'], row['name'])
        for index, row in self.outputs.iterrows():
            input_str = input_str.replace(row['desc'], row['name'])

        # 按格式输出
        ret = "接口描述\n"
        ret += ("Input\n")
        ret += ("变量名,缺省值,最小值,最大值\n")
        for i, row in self.inputs.iterrows():
            ret += (f"{row['name']},{row['value']},{row['min']},{row['max']}\n")
        ret += ("Output\n")
        ret += ("变量名,缺省值,最小值,最大值\n")
        for i, row in self.outputs.iterrows():
            ret += (f"{row['name']},{row['value']},{row['min']},{row['max']}\n")

        ret += "功能文档\n"
        ret += input_str
        ret += "\n根据功能文档逻辑,编写测试用例,参考接口描述中的变量取值范围,要求根据功能描述的逻辑,满足MCDC覆盖要求"

        return ret

    def ask_openai(self, question, system_txt):
        try:
            # url = "https://api.openai.com/v1/chat/completions"
            url = "http://121.40.104.79/openai/v1/chat/completions"
            # 请替换OPENAI_API_KEY变量
            # authorization = "Bearer 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"
            headers = {
                "Content-Type": "application/json"
                # ,"Authorization": authorization
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_txt},
                    # {"role": "assistant", "content": question},
                    {"role": "user", "content": question}
                ]
            }

            response = requests.request(method='POST',
                                        url=url,
                                        headers=headers, data=json.dumps(payload))
            self.response = response.json()

            # save to history
            # 将 Python 对象转换为 JSON 格式的字符串，并添加缩进
            response_str = json.dumps(payload, ensure_ascii=False) + "\n<-----response------>\n" + \
                           json.dumps(self.response, indent=4, ensure_ascii=False)
            response_str = response_str.replace('\\n', '\n').replace('\\"', '"')

            # 将 JSON 格式的字符串写入到文件中
            now = datetime.datetime.now()
            formatted_date = now.strftime("%Y%m%d_%H_%M_%S")

            filename = f"./history/ut_ai_{formatted_date}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response_str)
            # dt["choices"][0]["message"]

            return (self.response['choices'][0]['message']['content'])
        except Exception as e:
            traceback_str = traceback.format_exc()
            # print(traceback_str)
            logging.error(traceback.format_exc())
            self.show_warning_message('调用AI服务失败')
            return ""

    def json_to_txt(self, json_str, tick):
        # 将json字符串转换为字典形式
        result_str = ""
        try:

            dt = JsonComment().loads(json_minify(json_str))

            # 定义一个空字符串用于存储结果
            i = 1
            # 遍历test_cases，循环处理
            for case in dt["test_cases"]:
                # 将当前用例的描述信息添加到结果字符串中
                # result_str += f"//{i}. {case['Desc']}\n"
                desc = case.get('Desc', '') + case.get('desc', '')
                json_input = case.get("Input", {})
                json_input.update(case.get("input", {}))
                json_output = case.get("Output", {})
                json_output.update(case.get("output", {}))
                result_str += f"[{tick}] //{i}. {desc}\n"
                # 遍历输入项，将每一项添加到结果字符串中
                for i_key, i_value in json_input.items():
                    result_str += f"{i_key}={i_value};\n"
                # 遍历输出项，将结果添加到结果字符串中
                for o_key, o_value in json_output.items():
                    result_str += f"{o_key}={o_value}; //output \n"
                result_str += "\n"
                i += 1
        except Exception as e:
            traceback_str = traceback.format_exc()
            logging.error(traceback.format_exc())
            # print(traceback_str)
            self.show_warning_message('转换数据失败')
        return result_str

    def json_to_excel(self, json_str, tick, file_path):
        # 将json字符串转换为字典形式
        try:

            dt = JsonComment().loads(json_minify(json_str))

            # 初始值
            init_str = "// Initialization of input signals"
            for index, row in self.inputs.iterrows():
                init_str += f"\n{row['name']}={row['value']}"
            # for index, row in self.ut.outputs.iterrows():
            #     init_str += f"{row['name']}={row['value']}\n"

            outputdf = pandas.DataFrame({'desc': [], 'init': [], 'utcase': []})

            result_str = ""
            i = 1
            # 遍历test_cases，循环处理
            for case in dt["test_cases"]:
                desc = f"{case['Desc']}\n"
                init = init_str
                desc = case.get('Desc', '') + case.get('desc', '')
                json_input = case.get("Input", {})
                json_input.update(case.get("input", {}))
                json_output = case.get("Output", {})
                json_output.update(case.get("output", {}))
                # 将当前用例的描述信息添加到结果字符串中
                result_str = f"[{tick}] //{i}. {desc}"
                # 遍历输入项，将每一项添加到结果字符串中
                for i_key, i_value in json_input.items():
                    result_str += f"\n{i_key}={i_value};"
                # 遍历输出项，将结果添加到结果字符串中
                for o_key, o_value in json_output.items():
                    result_str += f"\n{o_key}={o_value}; //output"
                new_row = pandas.DataFrame(
                    {'desc': [desc], 'init': [init], 'utcase': [result_str]})
                outputdf = pandas.concat([outputdf, new_row], ignore_index=True)
                i += 1

            # 将数据写入Excel
            with pandas.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                outputdf.to_excel(writer, sheet_name='Sheet1',
                                  index=False, header=False, startrow=0, startcol=4)
                # 获取Worksheet对象
                worksheet = writer.sheets['Sheet1']
                # 创建格式对象
                wrap_style = writer.book.add_format(
                    {'text_wrap': True, 'align': 'vcenter'})
                # 设置单元格格式为换行
                worksheet.set_column('E:G', 50, wrap_style)

        except Exception as e:
            traceback_str = traceback.format_exc()
            logging.error(traceback.format_exc())
            # 处理堆栈信息
            # print(traceback_str)
            self.show_warning_message('导出文件失败')

    def show_warning_message(self, text, title='Warning', btn_name='ok'):

        text = translate(text, context='message')
        message_box = QMessageBox()
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setIcon(QMessageBox.Warning)
        message_box.addButton(btn_name, QMessageBox.AcceptRole)
        message_box.exec_()

    def show_info_message(self, text, title='information', btn_name='ok'):

        text = translate(text, context='message')
        message_box = QMessageBox()
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setIcon(QMessageBox.Information)
        message_box.addButton(btn_name, QMessageBox.AcceptRole)
        message_box.exec_()

    def show_confirm_message(self, text, func, func_args, title='确认', confirm_name='确认', cancel_name='取消'):

        text = translate(text, context='message')
        message_box = QMessageBox()
        message_box.setWindowTitle(translate(title, context='message'))
        message_box.setText(text)
        message_box.setIcon(QMessageBox.Information)

        message_box.addButton(translate(confirm_name, context='message'), QMessageBox.AcceptRole)
        message_box.addButton(translate(cancel_name, context='message'), QMessageBox.RejectRole)
        choice = message_box.exec_()
        # choice = message_box.question(self, title, text, QMessageBox.AcceptRole | QMessageBox.Cancel, QMessageBox.Cancel)
        if choice == QMessageBox.AcceptRole:
            func(func_args)
        elif choice == QMessageBox.RejectRole:
            pass

    def open_xlsx_file(self, file_path):
        os.startfile(file_path[0])

    def init_element(self):
        self.example_btn.clicked.connect(self.load_sample)
        self.format_output_btn.clicked.connect(self.format_directly)
        self.gen_prompt_btn.clicked.connect(self.gen_prompt)
        self.submit_ai_btn.clicked.connect(self.askai)
        self.ai_format_btn.clicked.connect(self.show_ai_answer)
        self.std_format_btn.clicked.connect(self.show_std_case)
        self.export_excel_btn.clicked.connect(self.export_excel)
        self.update_json_btn.clicked.connect(self.update_ai_answer)
        self.prompt_txt.textChanged.connect(self.prompt_txt_changed)
        self.req_txt.textChanged.connect(self.req_txt_changed)

        self.english_action.triggered.connect(lambda: self.change_lang('english'))
        self.chinese_action.triggered.connect(lambda: self.change_lang('chinese'))
        self.japanese_action.triggered.connect(lambda: self.change_lang('japanese'))

        self.model_wx_act.triggered.connect(lambda: self.change_model('wenxin'))
        self.model_ChatGPT_act.triggered.connect(lambda: self.change_model('chatgpt'))
        self.ai_model_type = 'wenxin'

        self.submit_ai_enable_icon = QtGui.QIcon()
        self.submit_ai_enable_icon.addPixmap(QtGui.QPixmap(".\\resources/submit_ai.png"), QtGui.QIcon.Normal,
                                             QtGui.QIcon.Off)
        self.submit_ai_disable_icon = QtGui.QIcon()
        self.submit_ai_disable_icon.addPixmap(QtGui.QPixmap(".\\resources/submit_ai_1.png"), QtGui.QIcon.Normal,
                                              QtGui.QIcon.Off)
        # self.comboBox = QComboBox(self.statusbar)
        # self.comboBox.addItem("")
        # self.comboBox.addItem("")
        # self.comboBox.addItem("")
        # self.comboBox.addItem("")
        # self.comboBox.setObjectName(u"comboBox")
        # self.comboBox.setMinimumSize(QSize(90, 30))
        # self.comboBox.setMaximumSize(QSize(90, 30))
        # self.comboBox.setStyleSheet('margin-left: 11px;')
        # self.statusbar.insertWidget(1, self.comboBox)

        self.processing_label = QLabel("AI processing...")
        self.processing_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.processing_label.setHidden(True)

        self.progressBar = QProgressBar(self.statusbar)
        self.progressBar.setMaximum(20)
        self.progressBar.setMinimum(0)
        self.progressBar.setFixedWidth(30)
        self.progressBar.setTextVisible(False)
        self.progressBar.setHidden(True)
        # self.progressBar.setMaximumSize(150, 15)
        # self.progressBar.setMinimumSize(150, 15)
        self.spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.statusbar.addPermanentWidget(self.processing_label)
        self.statusbar.addPermanentWidget(self.progressBar)

        self.change_lang('english')

        history_dir = './history'
        if os.path.exists(history_dir) == False:
            os.mkdir(history_dir)

    def prompt_txt_changed(self):
        if self.prompt_txt.toPlainText():
            self.submit_ai_btn.setCursor(QtGui.QCursor((QtCore.Qt.ArrowCursor)))
            self.submit_ai_btn.setIcon(self.submit_ai_enable_icon)
        else:
            self.submit_ai_btn.setCursor(QtGui.QCursor((QtCore.Qt.ForbiddenCursor)))
            self.submit_ai_btn.setIcon(self.submit_ai_disable_icon)

    def req_txt_changed(self):
        if self.req_txt.toPlainText():
            self.format_output_btn.setCursor(QtGui.QCursor((QtCore.Qt.ArrowCursor)))
            self.gen_prompt_btn.setCursor(QtGui.QCursor((QtCore.Qt.ArrowCursor)))
        else:
            self.format_output_btn.setCursor(QtGui.QCursor((QtCore.Qt.ForbiddenCursor)))
            self.gen_prompt_btn.setCursor(QtGui.QCursor((QtCore.Qt.ForbiddenCursor)))

    def update_progress_bar(self, percent):
        self.progressBar.setValue(percent)

    def change_model(self, ai_model_type):
        """
        切换AI模型类型。
        
        Args:
            ai_model_type: 新的AI模型类型，应为'wenxin'或'chatgpt'之一。
            
        Returns:
            无返回值。
        """
        checked_prefix = '√ | '
        unchecked_prefix = '    | '
        self.ai_model_type = ai_model_type
        if ai_model_type == 'wenxin':
            self.model_wx_act.setText(self.model_wx_act.text().replace(unchecked_prefix, checked_prefix))
            self.model_ChatGPT_act.setText(self.model_ChatGPT_act.text().replace(checked_prefix, unchecked_prefix))
        if ai_model_type == 'chatgpt':
            self.model_ChatGPT_act.setText(self.model_ChatGPT_act.text().replace(unchecked_prefix, checked_prefix))
            self.model_wx_act.setText(self.model_wx_act.text().replace(checked_prefix, unchecked_prefix))

    def change_lang(self, lang):
        if lang == 'english':
            self.trans.load('./i18n/eng.qm')
            _app = QApplication.instance()
            _app.installTranslator(self.trans)
            self.retranslateUi1(self)
        elif lang == 'japanese':
            self.trans.load('./i18n/jp.qm')
            _app = QApplication.instance()
            _app.installTranslator(self.trans)
            self.retranslateUi1(self)
        else:
            _app = QApplication.instance()
            _app.removeTranslator(self.trans)
            self.retranslateUi1(self)

    def retranslateUi1(self, MainWindow):
        super().retranslateUi(MainWindow)

        # self.comboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"10s", None))
        # self.comboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"30s", None))
        # self.comboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"60s", None))
        # self.comboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"90s", None))
        # self.processing_label.setText(self.trans.tr('AI处理中...'.encode('utf-8')))


def translate(key, context='MainWindow'):
    _translate = QtCore.QCoreApplication.translate
    return _translate(context, key)


class RequestOpenAIThread(QThread):
    request_complete = pyqtSignal(str, dict)

    # 重写QThread的构造函数
    def __init__(self, text, ai_model_type):
        QThread.__init__(self)
        self.ai_model_type = ai_model_type
        self.text = text
        self.is_interrupted = None
        self.return_data = None

    # 重写run方法
    def run(self):
        logging.info('start request openai')
        try:
            if self.ai_model_type == 'wenxin':
                self.return_data = chat_wenxin(self.text)
            else:
                self.return_data = chat_chatgpt(self.text)
            self.response = self.return_data['content']
        except Exception as e:
            logging.error(traceback.format_exc())
            self.return_data = {
                'status': 0,
                'msg': 'Requesting AI Service Error'
            }

        finally:
            prompt_key = str_to_md5(self.text)
            self.request_complete.emit(prompt_key, self.return_data)

    def request_interruption(self):
        self.is_interrupted = True


class FakeRequestThread(QThread):
    fake_request_complete = pyqtSignal(str, dict)

    # 重写QThread的构造函数
    def __init__(self, prompt_key, ai_model_type, return_content):
        QThread.__init__(self)
        self.ai_model_type = ai_model_type
        self.prompt_key = prompt_key
        self.is_interrupted = None
        self.return_content = return_content

    # 重写run方法
    def run(self):
        tm = config.get('baseReq', {}).get('timeout', 60)
        rd_second = random.randint(tm - 5, tm + 5)
        time.sleep(rd_second)

        self.return_data = {
            'ai_model_type': self.ai_model_type,
            'status': 1,
            'content': self.return_content
        }
        self.fake_request_complete.emit(self.prompt_key, self.return_data)

    def request_interruption(self):
        self.is_interrupted = True


class ProgressUpdateThread(QThread):
    progressChanged = pyqtSignal(int)

    def __init__(self):
        QThread.__init__(self)
        self.is_interrupted = None

    def run(self):
        while True:
            if self.is_interrupted:
                return
            for percent in range(1, 20):
                time.sleep(0.1)
                self.progressChanged.emit(percent)

import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox

from utcode_action import UtCodeActions


def handle_exception(exc_type, exc_value, exc_traceback):
    print("Exception occurred:", exc_type, exc_value)
    QMessageBox.critical(None, "执行出错，请重试", str(exc_value))


# 设置异常处理函数
sys.excepthook = handle_exception

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)  # 创建一个qapplication，也就是你要开发的软件app
    app.setWindowIcon(QIcon(".\\resources/robo.png"))
    # app.setStyleSheet('''
    #         QToolTip {
    #             border: 1px solid black;
    #             background-color: rgb(255, 255, 255);
    #         }
    #     ''')
    main_window = QtWidgets.QMainWindow()  # 创建一个qmainwindow，用来装载你需要的各种组件、控件
    ui = UtCodeActions()  # ui是你创建的ui类的实例化对象
    ui.setupUi(main_window)  # 执行类中的setupui方法，方法的参数是第二步中创建的qmainwindow
    ui.init_element()
    main_window.show()  # 执行qmainwindow的show()方法，显示这个qmainwindow
    sys.exit(app.exec_())  # 使用exit()或者点击关闭按钮退出qapplication

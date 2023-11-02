import logging
import os

# 创建一个logger对象
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fm = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s(%(funcName)s:%(lineno)d)] - %(message)s'"

# 向控制台输出日志的handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter(fm)
console_handler.setFormatter(console_formatter)

# 向文件输出日志的handler
log_file = os.path.join(os.getcwd(), 'log.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(fm)
file_handler.setFormatter(file_formatter)

# 把两个handler添加到logger对象中
logger.addHandler(console_handler)
logger.addHandler(file_handler)
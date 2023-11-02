import sqlite3

from json_minify import json_minify
from jsoncomment import JsonComment

conn = sqlite3.connect('cache.db')


# c = conn.cursor()
# c.execute('''CREATE TABLE OPENAI_CACHE
#        (PROMPT_KEY VARCHAR(50) PRIMARY KEY     NOT NULL,
#        VALUE           TEXT    NOT NULL);''')
# print ("数据表创建成功")
# conn.commit()

# with open('cache.json', mode='r', encoding='utf-8') as f:
#     cache_txt = f.read()
#     cache_json = JsonComment().loads(json_minify(cache_txt))
#     f.close()
#     c = conn.cursor()
#     for key, value in cache_json.items():
#         conn.execute("INSERT INTO OPENAI_CACHE (PROMPT_KEY, VALUE) \
#               VALUES ('{}', '{}')".format(key, value))
#
#     conn.commit()


c = conn.cursor()
cursor = conn.execute("select PROMPT_KEY, PROMPT, VALUE from OPENAI_CACHE where PROMPT_KEY = '{}'".format('fdc2c236071b941a32447a2cdf1b2620'))
cursor.rowcount
for cur in cursor:
    cur[0]
    pass
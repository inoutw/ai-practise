import json
import random
import sqlite3

from json_minify import json_minify
from jsoncomment import JsonComment

from config import config


class Cache:

    def __init__(self):
        self.__type = config.get('cache', {}).get('type', 'json')
        if self.__type == 'db':
            self.__conn = sqlite3.connect('cache.db')

    def get_from_prompt_key(self, prompt_key, ai_model_type):

        if self.__type == 'db':
            rows = self.__conn.execute(
                "select PROMPT_KEY, PROMPT, VALUE, AI_MODEL_TYPE from OPENAI_CACHE where PROMPT_KEY = '{}' and AI_MODEL_TYPE = '{}'"
                .format(prompt_key, ai_model_type))
            row = rows.fetchone()
            if row:
                return row[2]
            else:
                return None
        else:
            with open('cache.json', mode='r', encoding='utf-8') as f:
                cache_txt = f.read()
                f.close()
                cache_json = JsonComment().loads(json_minify(cache_txt))
                ai_rtn = cache_json.get(prompt_key, None)
                return ai_rtn

    def get_random(self):
        if self.__type == 'db':
            count = self.__conn.execute("select count(*) from OPENAI_CACHE")
            count_num = count.fetchone()
            key_idx = random.randint(0, count_num[0] - 1)
            rows = self.__conn.execute(
                "select PROMPT_KEY, PROMPT, VALUE, AI_MODEL_TYPE from OPENAI_CACHE limit {}, 1".format(key_idx))
            row = rows.fetchone()
            return row[2]
        else:
            with open('cache.json', mode='r', encoding='utf-8') as f:
                cache_txt = f.read()
                cache_json = JsonComment().loads(json_minify(cache_txt))
                f.close()
                keys = list(cache_json.keys())
                key_idx = random.randint(0, len(keys) - 1)
                return cache_json.get(keys[key_idx])

    def put(self, prompt_key, data):
        """
        存储缓存数据
        
        Args:
            self: 类的实例
            prompt_key: 提示键，存储的数据对应的提示键
            data: 存储的数据，存储的键值对
        
        Returns:
            None
        """
        if self.__type == 'db':
            rows = self.__conn.execute(
                "select PROMPT_KEY, PROMPT, VALUE, AI_MODEL_TYPE from OPENAI_CACHE where PROMPT_KEY = '{}' and AI_MODEL_TYPE = '{}'"
                .format(prompt_key, data.get('ai_model_type')))
            row = rows.fetchone()
            if row is None:
                self.__conn.execute("INSERT INTO OPENAI_CACHE (PROMPT_KEY, VALUE, AI_MODEL_TYPE) \
                              VALUES ('{}', '{}', '{}')".format(prompt_key, data.get('value'), data.get('ai_model_type')))
                self.__conn.commit()
        else:
            with open('cache.json', mode='r+', encoding='utf-8') as f:
                cache_txt = f.read()
                cache_json = JsonComment().loads(json_minify(cache_txt))
                cache_json.update({prompt_key: data['value']})
                f.seek(0)
                json.dump(cache_json, f, ensure_ascii=False)
                f.close()


cache = Cache()

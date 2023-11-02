import datetime
import json

import requests
from logger import logger as logging
from config import config


with open('system.txt', mode='r', encoding='utf-8') as f:
    __system_txt = f.read()


def chat(prompt):
    # url = "https://api.openai.com/v1/chat/completions"
    url = "http://121.40.104.79/openai/v1/chat/completions"
    # url = "https://121.40.104.79/v1/chat/completions"
    # 请替换OPENAI_API_KEY变量
    authorization = "Bearer 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"
    headers = {
        "Content-Type": "application/json"
        , "Authorization": config.get('openai', {}).get('authorization',
                                                        authorization)
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": __system_txt},
            # {"role": "assistant", "content": question},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.request(method='POST',
                                url=config.get('openai', {}).get('url',
                                                                 'https://121.40.104.79/v1/chat/completions'),
                                headers=headers,
                                data=json.dumps(payload),
                                verify=False,
                                timeout=config.get('openai', {}).get('timeout', 60))
    logging.info(response)
    # save to history
    # 将 Python 对象转换为 JSON 格式的字符串，并添加缩进
    response_str = json.dumps(payload, ensure_ascii=False) + "\n<-----response------>\n" + \
                   json.dumps(response.json(), indent=4, ensure_ascii=False)
    response_str = response_str.replace('\\n', '\n').replace('\\"', '"')

    # 将 JSON 格式的字符串写入到文件中
    formatted_date = datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")
    filename = f"./history/ut_ai_{formatted_date}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response_str)

    return_data = {
        'ai_model_type': 'chatgpt',
        'status': 1,
        'content': response.json()['choices'][0]['message']['content']
    }
    return return_data

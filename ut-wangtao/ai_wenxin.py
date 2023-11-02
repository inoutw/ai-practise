import datetime
import json

import requests
from logger import logger as logging
from config import config

ask1 = '''
根据文档编写测试用例。文档格式分为两部分，接口描述和功能文档
接口描述定义了用例的输入变量和输出变量，类似如下表格形式
Input
变量名,缺省值,最小值,最大值
DTCo_bEleMode,0,0.0,1.0
SDFA_TqWhlCrksftFild,0.0,-8190.0,8191.0
Output
变量名,缺省值,最小值,最大值
DTRTI_TqWhlP2ReqDeltaWoIntv,0.0,-10000.0,10000.0

INPUT部份定义输入变量，OUTPUT部份定义输出变量,
功能文档部份通过伪码的形式描述了模块的执行逻辑，其中**号中间的部份是输入参数，##号中间的部份是输出参数，测试用例只包含输出参数和输入参数
&&号，$$号，@@，!!，??中间的值不写入测试用例
功能文档
If *DTCo_bEleMode*is inactive, #DTRTI_TqWhlP2ReqDeltaWoIntv# =
*SDFA_TqWhlCrksftFild* - *SDFA_TqWhlCrksftFild* - *SDB_TqWhlP2EmWoutIntv*
Otherwise, if *DTCo_bEleMode*is active, #DTRTI_TqWhlP2ReqDeltaWoIntv#=
& Calibration for Delta Wheel Torque request for P2 Electric Motor without TCU intervention &(Initial value is 0N.m).

测试用例按照如下json格式生成，测试用例只包含输出参数和输入参数

{
"test_cases": [
{
"Desc": "条件检查电动模式为非活动状态",
"Input": {
"DTCo_bEleMode": "0",
"SDFA_TqWhlCrksftFild": "8191",
"SDFA_TqWhlCrksftFild": "200",
"SDB_TqWhlP2EmWoutIntv": "500"
},
"output": {
"DTRTI_TqWhlP2ReqDeltaWoIntv": "8191-200-500"
}
},
{
"Desc": "条件检查电动模式为活动状态",
"Input": {
"DTCo_bEleMode": "1",
"SDFA_TqWhlCrksftFild": "0",
"SDFA_TqWhlCrksftFild": "0",
"SDB_TqWhlP2EmWoutIntv": "0"
},
"output": {
"DTRTI_TqWhlP2ReqDeltaWoIntv": "0"
}
}
]
}
'''


def chat(prompt):
    WENXIN_CHAT_URL = config.get('wenxin', {}).get('url',
                                                   'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions') \
                      + '?access_token=' + get_access_token()
    # 定义请求头
    headers = {
        'Content-Type': 'application/json',
    }
    # 定义请求体 JSON 数据
    request_data = {
        "messages": [
            {"role": "user", "content": ask1},
            {"role": "assistant", "content": "ok."},
            {"role": "user", "content": prompt}
        ]
    }
    logging.info(f'do_wenxin_chat Request prompt: \n{request_data}')
    # 发送 POST 请求
    response = requests.post(WENXIN_CHAT_URL, json=request_data, headers=headers)

    # save to history
    # 将 Python 对象转换为 JSON 格式的字符串，并添加缩进
    response_str = str(json.dumps(request_data, ensure_ascii=False)) + "\n<-----response------>\n" + \
                   str(response.json())
    response_str = response_str.replace('\\n', '\n').replace('\\"', '"')

    # 将 JSON 格式的字符串写入到文件中
    formatted_date = datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")
    filename = f"./history/ut_ai_{formatted_date}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response_str)

    try:
        if response.status_code == 200:
            result = response.json().get("result", response.content)
            # 输出相关信息
            logging.info(f'do_wenxin_chat Response body:\n{result}')
            return_data = {
                'ai_model_type': 'wenxin',
                'status': 1,
                'content': result
            }
            return return_data
    except Exception as e:
        logging.error("do_wenxin_chat error", e)
    return response.json()


def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": config.get('wenxin', {}).get('api_key'), "client_secret": config.get('wenxin', {}).get('secret_key')}
    return str(requests.post(url, params=params).json().get("access_token"))
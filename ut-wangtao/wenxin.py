import requests
from logger import logger as logging

def do_wenxin_chat(ask1, ask2):
    WENXIN_CHAT_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token=24.bda37a632d09a9cb59b43f397d16352e.2592000.1688109884.282335-34009910"
    # 定义请求头
    headers = {
        'Content-Type': 'application/json',
    }
    # 定义请求体 JSON 数据
    request_data = {
        "messages": [
            {"role": "user", "content": ask1},
            {"role": "assistant", "content": "ok."},
            {"role": "user", "content": ask2}
        ]
    }
    logging.info(f'do_wenxin_chat Request prompt: \n{request_data}')
    # 发送 POST 请求
    response = requests.post(WENXIN_CHAT_URL, json=request_data, headers=headers)
    print(response)
    try:
        if response.status_code == 200:
            result = response.json().get("result", response.content)
            # 输出相关信息
            logging.info(f'do_wenxin_chat Response body:\n{result}')
            return result
    except Exception as e:
        logging.error("do_wenxin_chat error", e)
    return None


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

ask2 = '''
接口描述
Input
变量名,缺省值,最小值,最大值
DTCo_bEleMode,nan,0.0,102.0
SDFA_TqWhlCrksftFild,0.0,-8190.0,8191.0
WTC_TqEngWhlSetPah,0.0,-10000.0,10000.0
SDB_TqWhlP2EmWoutIntv,0.0,-10000.0,10000.0
Output
变量名,缺省值,最小值,最大值
DTRTI_TqWhlP2ReqDeltaWoIntv,0.0,-10000.0,10000.0
功能文档
If *DTCo_bEleMode*is inactive, #DTRTI_TqWhlP2ReqDeltaWoIntv# = 
*SDFA_TqWhlCrksftFild* - *WTC_TqEngWhlSetPah* - *SDB_TqWhlP2EmWoutIntv*
Otherwise, if *DTCo_bEleMode*is active, #DTRTI_TqWhlP2ReqDeltaWoIntv#=
& Calibration for DTRTI_TqWhlP2ReqDeltaWoIntv &(Initial value is 0N.m, ).

根据功能文档逻辑,编写测试用例,参考接口描述中的变量取值范围,要求根据功能描述的逻辑,满足MCDC覆盖要求
'''
do_wenxin_chat(ask1, ask2)

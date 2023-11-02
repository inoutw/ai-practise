import re
import json

def extract_json(text):
    # 使用正则表达式匹配{}内的JSON数据
    pattern = r'{.*}'
    match = re.search(pattern, text)

    if match is None:
        raise ValueError('JSON数据未找到')

    # 提取匹配到的JSON数据
    json_text = match.group()

    # 解析JSON
    json_data = json.loads(json_text)

    return json_data

# 示例文本包含JSON数据和其他文本
example_text = '''一些文本内容{}内的，然后下面是一个包含JSON数据的部分：
{
  "name": "John",
  "age": 30,
  "city": "New York"
}
这是一些其他文本内容。'''

# 提取JSON数据
json_data = extract_json(example_text)

# 打印提取的JSON数据
print(json_data)

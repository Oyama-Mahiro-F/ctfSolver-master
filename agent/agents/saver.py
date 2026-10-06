import re

from utils.chatbot import add_message, chat
from utils.logger import logger
from config import config
import xmltodict

# 解析失败时的兜底页面信息，保证调用方（add_page）始终拿到完整字段
_FALLBACK_RESULT = {
    'name': '未命名页面',
    'description': '',
    'key': '',
    'flag': '',
}

flag_result = """
<flag>当前页面中包含的flag的成功获取的最终信息（一长串包含{{的复杂字符，在页面上显示的内容以flag开头，格式为flag{{xxxx}}），如果没发现置空即可</flag>
""" if config.NEED_FLAG else ""

prompt = f"""
你专注于从页面请求和响应中提取关键信息
你需要仔细分析响应页面中的关键信息和请求包中的参数信息给出最终的分析结果，比如注册时提交的用户名密码等键值和页面的响应信息
你需要返回xml格式结果，格式如下：
<result>
    <name>页面简单命名（10个字以内）</name>
    <description><![CDATA[ 页面描述，描述该页面的具体功能和可以显示的信息]]></description>
    <key><![CDATA[ 需要当前页面获取的关键线索（用户名、密码、令牌等），如果没有可以不填，使用自然语言描述，越详细越好，对于令牌需要描述该令牌传入方式，是header还是cookie，并写清楚键值，尽可能详细的写]]></key>
    {flag_result}
</result>

注意：
* 当前页面关键线索必须是响应中发现的内容，而且必须是敏感信息，不是凭空猜测的内容
* 描述需要足够精炼，但具体参数值必须给出
* key中不可以携带任何关于漏洞或漏洞提示的信息
* 如果有多个set-cookie，都要写清楚
"""

message = """
你需要分析的页面如下：
请求包：
{request}
响应包：
{response}
"""


def save_page(page):
    """
    保存页面
    :param page: 页面
    :return: 动作
    """
    session_id = add_message(message.format(request=page.get("request", ""), response=page.get("response", "")))
    response = chat(prompt.format(CTF_DESC=config.CTF_DESC), session_id)
    if not response:
        logger.warning("页面信息提取失败：模型无响应，使用兜底结果")
        return dict(_FALLBACK_RESULT)
    # 模型输出不稳定，可能不含 <result>，此处必须容错，否则会 IndexError 中断页面探索
    matches = re.findall(r"(<result>.*?</result>)", response, re.DOTALL)
    if not matches:
        logger.warning("页面信息提取失败：未找到 <result> 标签，使用兜底结果")
        return dict(_FALLBACK_RESULT)
    try:
        result = xmltodict.parse(matches[0])['result']
    except Exception as e:
        logger.error(f"页面信息 XML 解析失败: {e}")
        return dict(_FALLBACK_RESULT)
    if not isinstance(result, dict):
        # 模型可能输出 <result>纯文本</result>
        logger.warning("页面信息解析结果不是字典，使用兜底结果")
        return dict(_FALLBACK_RESULT)
    # 合并兜底字段，避免模型漏字段时调用方 KeyError
    return {**_FALLBACK_RESULT, **result}

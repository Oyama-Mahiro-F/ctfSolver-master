# 漏洞利用智能体

from re import S
from config import config
from utils import chatbot
import xmltodict
import re
from addons import request

prompt_template = """
你是一个漏洞利用专家，我会给你一个页面请求和漏洞载荷，格式如下：
<request>页面请求，json格式</request>
<vuln>漏洞类型</vuln>
<desc>漏洞描述，自然语言，详细描述了漏洞需要用到的载荷<desc>

你需要调用请求工具来完成漏洞利用，调用方式如下：
<request>
{request_desc}
</request>
当漏洞利用完成后，如下总结：
<summary>
对当前漏洞利用情况与结果的总结
</summary>
"""

message_template = """
当前漏洞如下：
<request>{request}</request>
<vuln>{vuln}</vuln>
<desc>{desc}</desc>

你需要完成的漏洞利用：
{message}

请你进行漏洞利用
"""

MAX_EXPLOIT_STEPS = 30


def exploit_vuln(request_info, vuln, desc, message):
    prompt = prompt_template.format(request_desc=config.get_addon("request"))
    session_id = chatbot.add_message(message=message_template.format(request=request_info, vuln=vuln, desc=desc, message=message))

    for _ in range(MAX_EXPLOIT_STEPS):
        # 每一轮都必须重新向 LLM 索取下一步指令，否则循环永不推进
        response = chatbot.chat(prompt=prompt, session_id=session_id)
        if not response:
            break

        # 先判断总结，避免同一轮响应同时包含 request 与 summary 时丢失终止条件
        summary_xml = re.search(r"(<summary>.*?</summary>)", response, re.DOTALL)
        if summary_xml:
            return xmltodict.parse(summary_xml.group(1))["summary"]

        request_xml = re.search(r"(<request>.*?</request>)", response, re.DOTALL)
        if request_xml:
            try:
                request_json = xmltodict.parse(request_xml.group(1))["request"]
                # <request> 内部包裹 <value>，与 actioner 的解析方式保持一致
                if isinstance(request_json, dict) and "value" in request_json:
                    request_json = request_json["value"]
                result = request.run(request_json)
            except Exception as e:
                result = f"请求解析或执行失败: {e}"
            chatbot.add_message(message=f"请求响应：{result}", session_id=session_id)
        else:
            chatbot.add_message(
                message="未识别到有效指令，请重新构造 <request> 或给出 <summary> 总结",
                session_id=session_id,
            )

    return None

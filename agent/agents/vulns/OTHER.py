from addons import run_python


prompt_detect = """
该漏洞检测思路不提供标准的漏洞检测思路，请根据漏洞描述进行测试。



对于复杂的功能（查看压缩包、进行编码、解码），你可以编写python脚本进行利用，编写方式如下：
<tool>
    <code><![CDATA[需要测试的python代码]]></code>
</tool>
"""

def need_detect(request_json):
    return True

def simple_detect(request_json, response, param=None):
    if not isinstance(param, dict):
        return "工具调用格式错误：param 必须为字典"
    code = param.get('code')
    if not code:
        return "缺少 Python 代码：请在 <tool> 中提供 <code> 子标签"
    return run_python.run(code)

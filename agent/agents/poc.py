import os
import yaml
import traceback
import uuid
import json
import xmltodict
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

from utils.chatbot import add_message, chat
from utils.logger import logger
from utils import sql_helper
from config import config
from utils.agent_manager import agent_manager
from addons.request import run
from urllib.parse import urlparse


poc_prompt = """
你是一个漏洞利用专家，你需要根据我提供的漏洞文档和漏洞利用过程利用漏洞获取系统中隐藏的flag。
flag为一串复杂的字符串，并且在页面上显示以flag开头，形式为：flag{{xxxxx}}，一般存在的文件名包含flag或FLAG，通过命令执行漏洞寻找flag文件可以先进行根目录和常见目录的列目录，查询无果后再进行深入寻找。
你需要利用的漏洞如下：
{poc_file}
（后利用已全部完成）
你需要返回格式化的工具调用xml数据用以验证，格式如下：
{request_desc}
一次只构造一个响应包，你可以进行多步来尝试获取最终的flag。
如果所有漏洞利用步骤完成，你需要根据最终的结果返回本次漏洞利用总结：
<summary>
    <vuln>True/False（是否存在漏洞）</vuln>
    <findFlag>True/False（是否发现flag）</findFlag>
    <desc><![CDATA[根据之前结果进行本次漏洞检测总结，需要写出详细漏洞参数、漏洞类型、漏洞载荷，漏洞载荷使用【】包装，尽可能详细描述，把所有路径、成功的载荷信息都说明清楚，如果用到其他漏洞，需要写明用到的漏洞的id；如利用id为xxx的漏洞上传文件后进行xxx]]></desc>
    <flag>如果发现flag(一串复杂字符)，输出flag内容，否则置空</flag>
</summary>
请注意：如果漏洞说明中包含后利用过程，可以紧随后利用过程之后继续利用，一般后利用回写入shell，请利用已完成的步骤
"""

message_template = """
存在漏洞url：{url}

对漏洞url的利用过程：
请求：
{request}
响应：
{response}

"""

class Scanner:

    def poc_scan(self, page, key, task_id):
        """
        POC扫描主函数 - 并发执行所有POC并汇总结果

        Args:
            page: 目标页面URL
            key: 任务密钥
            task_id: 任务ID

        Returns:
            dict: 汇总的扫描结果 {"漏洞名称": 漏洞结果}
        """
        logger.info(f"开始POC扫描: {page['name']}")

        # 发送开始扫描的pure消息
        scan_message = agent_manager.send_pure_message_with_status(
            agent_manager.current_task_id,
            f"🔍 开始POC扫描: {page}",
            "running"
        )

        # 获取所有POC文件
        poc_files = self.get_poc_files()
        if not poc_files:
            logger.warning("未找到POC文件")
            # 更新消息状态
            if scan_message:
                agent_manager.update_pure_message_status(
                    scan_message.get('id'),
                    "finish",
                    f"❌ 未找到POC文件"
                )
            return {}

        logger.info(f"找到 {len(poc_files)} 个POC文件，开始并发测试")

        # 更新扫描进度消息
        if scan_message:
            agent_manager.update_pure_message_status(
                scan_message.get('id'),
                "running",
                f"🔍 找到 {len(poc_files)} 个POC文件，开始并发测试..."
            )

        # 并发执行POC扫描
        results = {}
        vulnerabilities = []  # 收集发现的漏洞

        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有POC任务
            future_to_poc = {
                executor.submit(self.execute_poc, poc_file, page.get("request")['url']): poc_file
                for poc_file in poc_files
            }

            # 收集结果
            for future in as_completed(future_to_poc):
                poc_file = future_to_poc[future]
                try:
                    result = future.result()
                    if result:
                        vuln_name = result.get('vuln_name', os.path.basename(poc_file))
                        results[vuln_name] = result

                        if result.get('vulnerable'):
                            logger.info(f"发现漏洞: {vuln_name}")

                            # 保存漏洞信息到数据库
                            try:
                                sql_helper_instance = sql_helper.SQLiteHelper()
                                sql_helper_instance.insert_record(
                                    table='vulns',
                                    data={
                                        'id': str(uuid.uuid4()),
                                        'task_id': task_id,
                                        'vuln_type': vuln_name,
                                        'desc': result.get('description', ''),
                                        'request_json': json.dumps(result.get('request')),
                                    }
                                )
                                logger.info(f"漏洞信息已保存到数据库: {vuln_name}")
                            except Exception as e:
                                logger.error(f"保存漏洞信息到数据库失败: {str(e)}")

                            # 创建漏洞记录
                            try:
                                last_request = result.get('request')
                                last_response = result.get('response')

                                vuln_data = {
                                    "vuln_type": vuln_name,
                                    "description": result.get('description', ''),
                                    "request": json.dumps(last_request),
                                    "response": json.dumps(last_response)
                                }
                                # 直接调用同步方法，不使用asyncio.create_task
                                created_vuln = agent_manager.create_vulnerability(agent_manager.current_task_id,
                                                                                  vuln_data)

                                # 收集漏洞信息用于发送漏洞消息
                                vuln_info = {
                                    "id": created_vuln.get('id'),
                                    "name": vuln_name,
                                    "vuln_type": vuln_name,
                                    "url": page['request']['url'],
                                    "description": result.get('description', ''),
                                    "severity": result.get('severity', 'medium'),
                                }
                                vulnerabilities.append(vuln_info)

                                logger.info(f"漏洞记录已创建: {vuln_name}")
                            except Exception as e:
                                logger.error(f"创建漏洞记录失败: {str(e)}")

                        else:
                            logger.debug(f"未发现漏洞: {vuln_name}")

                except Exception as e:
                    logger.error(f"POC {poc_file} 执行异常: {str(e)}")

        # 统计结果
        vuln_count = sum(1 for result in results.values() if result.get('vulnerable'))
        logger.info(f"POC扫描完成，共测试 {len(poc_files)} 个POC，发现 {vuln_count} 个漏洞")

        # 发送漏洞消息（如果发现漏洞）
        if vulnerabilities:
            agent_manager.send_vulnerability_message(
                agent_manager.current_task_id,
                vulnerabilities,
                f"🚨 POC扫描发现 {vuln_count} 个漏洞"
            )

        # 更新扫描完成消息状态
        if scan_message:
            if vuln_count > 0:
                status_text = f"✅ POC扫描完成，共测试 {len(poc_files)} 个POC，发现 {vuln_count} 个漏洞"
            else:
                status_text = f"✅ POC扫描完成，共测试 {len(poc_files)} 个POC，未发现漏洞"

            agent_manager.update_pure_message_status(
                scan_message.get('id'),
                "finish",
                status_text
            )

        return results

    def get_poc_files(self):
        """
        获取POC目录下的所有POC文件

        Returns:
            list: POC文件路径列表
        """
        poc_files = []
        poc_dir = config.POC_PATH

        if not os.path.exists(poc_dir):
            logger.warning(f"POC目录不存在: {poc_dir}")
            return poc_files

        for filename in os.listdir(poc_dir):
            if filename.endswith(('.yaml', '.yml')):
                poc_files.append(os.path.join(poc_dir, filename))

        return poc_files

    def execute_poc(self, poc_file, target_url):
        """
        执行单个POC文件

        Args:
            poc_file: POC文件路径
            target_url: 目标URL

        Returns:
            dict: 执行结果
        """
        try:
            with open(poc_file, 'r', encoding='utf-8') as f:
                poc_data = yaml.safe_load(f)

            poc_name = poc_data.get('name', os.path.basename(poc_file))
            poc_description = poc_data.get('description', '')
            poc_severity = poc_data.get('severity', 'medium')

            logger.debug(f"执行POC: {poc_name}")

            # 获取请求序列
            requests_list = poc_data.get('requests', [])
            if not requests_list:
                logger.warning(f"POC {poc_name} 中没有找到requests配置")
                return {
                    'vuln_name': poc_name,
                    'vulnerable': False,
                    'description': poc_description,
                    'severity': poc_severity,
                    'error': 'No requests found in POC'
                }

            # 执行每个请求序列
            for req_sequence in requests_list:
                steps = req_sequence.get('steps', [])
                if not steps:
                    continue

                # 执行步骤序列
                result = self.execute_steps(steps, target_url, poc_name)
                if result['vulnerable']:
                    # 获取最后一个请求和响应用于前端显示
                    requests_list = result.get('requests', [])
                    responses_list = result.get('responses', [])
                    last_request = requests_list[-1] if requests_list else {}
                    last_response = responses_list[-1] if responses_list else {}

                    return {
                        "poc_file": poc_file,
                        'vuln_name': poc_name,
                        'vulnerable': True,
                        'description': poc_description,
                        'severity': poc_severity,
                        'summary': {
                            'vuln_type': poc_name,
                            'desc': poc_description
                        },
                        'request': last_request,
                        'response': last_response
                    }

            # 所有序列都未发现漏洞
            return {
                'vuln_name': poc_name,
                'vulnerable': False,
                'description': poc_description,
                'severity': poc_severity
            }

        except Exception as e:
            logger.error(f"执行POC {poc_file} 时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'vuln_name': os.path.basename(poc_file),
                'vulnerable': False,
                'error': str(e)
            }

    def execute_steps(self, steps, target_url, poc_name):
        """
        执行步骤序列

        Args:
            steps: 步骤列表
            target_url: 目标URL
            poc_name: POC名称

        Returns:
            dict: 执行结果
        """
        session_data = {}
        all_requests = []
        all_responses = []

        for step_index, step in enumerate(steps):
            try:
                # 执行单个步骤
                step_result = self.execute_step(step, target_url, session_data)

                # 记录请求和响应
                all_requests.append(step_result['request'])
                all_responses.append(step_result['response'])

                # 更新会话数据
                if 'extracted_data' in step_result:
                    session_data.update(step_result['extracted_data'])

                # 检查是否匹配漏洞
                if step_result['matched']:
                    return {
                        'vulnerable': True,
                        'requests': all_requests,
                        'responses': all_responses,
                        'matched_step': step_index + 1
                    }

            except Exception as e:
                logger.error(f"执行步骤 {step_index + 1} 时出错: {str(e)}")
                continue

        return {
            'vulnerable': False,
            'requests': all_requests,
            'responses': all_responses
        }

    def execute_step(self, step_config, target_url, session_data):
        """
        执行单个步骤

        Args:
            step_config: 步骤配置
            target_url: 目标URL
            session_data: 会话数据

        Returns:
            dict: 步骤执行结果
        """
        # 获取请求参数
        method = step_config.get('method', 'GET').upper()
        path = step_config.get('path', '/')
        headers = step_config.get('headers', {})
        body = step_config.get('body', '')
        query = step_config.get('query', {})

        # 替换会话数据中的变量
        for key, value in session_data.items():
            path = path.replace(f'{{{key}}}', str(value))
            body = body.replace(f'{{{key}}}', str(value))
            for header_key, header_value in headers.items():
                headers[header_key] = str(header_value).replace(f'{{{key}}}', str(value))
            # 替换query参数中的变量
            for query_key, query_value in query.items():
                query[query_key] = str(query_value).replace(f'{{{key}}}', str(value))



        # 构建完整URL
        full_url = urljoin(target_url, path)

        # 设置默认headers
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; POC-Scanner/1.0)',
            'Accept': '*/*',
            'Connection': 'close'
        }
        default_headers.update(headers)

        # 构建request.run的参数
        request_params = {
            'url': full_url,
            'method': method,
            'header': default_headers,
            'params': query,  # 使用POC中定义的query参数
            'files': {},
            'history': False  # POC扫描不需要历史记录
        }

        # 如果有请求体数据，使用raw参数
        if body:
            request_params['raw'] = body

        # 发送HTTP请求
        try:
            response_data = run(request_params)
            
            # 检查是否有错误
            if 'error' in response_data:
                logger.error(f"请求失败: {response_data['error']}")
                raise Exception(response_data['error'])

            # 获取响应数据
            response_body = response_data.get('content', '')
            response_headers = response_data.get('header', {})
            status_code = response_data.get('status', 200)
            response_url = response_data.get('url', full_url)

            # 记录请求信息（符合前端格式）
            request_info = {
                'method': method,
                'url': full_url,
                'header': default_headers,
                'params': query,
                'files': {},
                'raw': body if method in ['POST', 'PUT', 'PATCH'] else ''
            }

            # 记录响应信息（符合前端格式）
            response_info = {
                'status': status_code,
                'header': response_headers,
                'content': response_body,
                'url': response_url
            }

            # 创建响应对象用于后续处理
            class Response:
                def __init__(self, status_code, headers, text):
                    self.status_code = status_code
                    self.headers = headers
                    self.text = text

            response = Response(status_code, response_headers, response_body)

            # 处理提取器
            extracted_data = self.process_extractors(step_config.get('extractors', []), response.text)

            # 检查匹配器
            matched = self.check_matchers(step_config.get('matchers', []), response)

            return {
                'request': request_info,
                'response': response_info,
                'extracted_data': extracted_data,
                'matched': matched
            }

        except Exception as e:
            logger.error(f"HTTP请求失败: {str(e)}")
            
            # 返回错误响应
            request_info = {
                'method': method,
                'url': full_url,
                'header': default_headers,
                'params': query,
                'files': {},
                'raw': body if method in ['POST', 'PUT', 'PATCH'] else ''
            }

            response_info = {
                'status': 0,
                'header': {},
                'content': '',
                'error': str(e)
            }

            return {
                'request': request_info,
                'response': response_info,
                'extracted_data': {},
                'matched': False
            }

    def process_extractors(self, extractors, response_text):
        """
        处理提取器，从响应中提取数据

        Args:
            extractors: 提取器配置列表
            response_text: 响应文本

        Returns:
            dict: 提取的数据
        """
        extracted_data = {}

        for extractor in extractors:
            extractor_type = extractor.get('type', 'regex')
            extractor_name = extractor.get('name', 'extracted_value')

            if extractor_type == 'regex':
                import re
                patterns = extractor.get('regex', [])
                if isinstance(patterns, str):
                    patterns = [patterns]
                try:
                    group = int(extractor.get('group', 0))
                except (TypeError, ValueError):
                    group = 0

                for pattern in patterns:
                    match = re.search(pattern, response_text, re.IGNORECASE)
                    if match:
                        try:
                            extracted_value = match.group(group)
                            extracted_data[extractor_name] = extracted_value
                            logger.debug(f"提取到 {extractor_name}: {extracted_value}")
                            break
                        except IndexError:
                            logger.warning(f"正则表达式组 {group} 不存在")

        return extracted_data

    def check_matchers(self, matchers, response):
        """
        检查匹配器，判断是否存在漏洞

        Args:
            matchers: 匹配器配置列表
            response: HTTP响应对象

        Returns:
            bool: 是否匹配所有条件
        """
        if not matchers:
            # 如果没有匹配器，默认检查状态码
            return response.status_code == 200

        # 收集所有匹配器的结果
        matcher_results = []

        for matcher in matchers:
            matcher_type = matcher.get('type', 'word').lower()
            condition = matcher.get('condition', 'and').lower()

            if matcher_type == 'word':
                words = matcher.get('words', [])
                if isinstance(words, str):
                    words = [words]
                match_result = self.check_word_matcher(response.text, words, condition)
                matcher_results.append((match_result, condition))

            elif matcher_type == 'status':
                status_codes = matcher.get('status', [])
                # YAML 里可能写成标量（status: 200），不归一化会直接 TypeError 或按字符迭代
                if isinstance(status_codes, (str, int)):
                    status_codes = [status_codes]
                normalized_codes = []
                for code in status_codes:
                    try:
                        normalized_codes.append(int(code))
                    except (TypeError, ValueError):
                        continue
                match_result = response.status_code in normalized_codes
                matcher_results.append((match_result, condition))

            elif matcher_type == 'regex':
                import re
                patterns = matcher.get('regex', [])
                if isinstance(patterns, str):
                    patterns = [patterns]
                match_result = any(
                    re.search(pattern, response.text, re.IGNORECASE)
                    for pattern in patterns
                )
                matcher_results.append((match_result, condition))

            else:
                # 未知匹配器类型
                matcher_results.append((False, condition))

        # 如果没有匹配器，返回False
        if not matcher_results:
            return False

        # matchers 列表整体语义为 AND：每个匹配器都必须满足自己的条件。
        # 原实现在 or 匹配器命中时直接 return True，会短路掉已经失败的 and 匹配器；
        # 而 or 匹配器未命中时又什么都不做，导致未命中仍然返回 True（误报漏洞并写库）。
        return all(result for result, _condition in matcher_results)

    def check_word_matcher(self, text, words, condition):
        """
        检查文本中是否包含指定的关键词

        Args:
            text: 要检查的文本
            words: 关键词列表
            condition: 匹配条件 ('and' 或 'or')

        Returns:
            bool: 是否匹配
        """
        if not words:
            return False

        if condition == 'or':
            return any(word in text for word in words)

        return all(word in text for word in words)


class Flagger:
    def hunt_flag(self, poc_file, request, response, pure_id):
        # 首先解析POC文件，检查是否有posts配置
        try:
            with open(poc_file, 'r', encoding='utf-8') as f:
                poc_data = yaml.safe_load(f)
            
            # 检查是否有posts配置
            posts_executed = False
            posts_results = []
            
            # 查找requests中的post配置
            requests_list = poc_data.get('requests', [])
            for req_sequence in requests_list:
                if 'post' in req_sequence:
                    posts_steps = req_sequence['post']
                    logger.info(f"发现posts配置，包含 {len(posts_steps)} 个步骤，开始执行...")
                    
                    # 执行posts步骤
                    target_url = request['url']
                    session_data = {}
                    
                    for step_index, step in enumerate(posts_steps):
                        if step.get('command', ""):
                            parsed = urlparse(target_url)
                            host = parsed.hostname
                            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                            command = step['command'].format(host=host, port=port)
                            result = os.popen(command).read()
                            posts_results.append({
                                'step': step_index + 1,
                                'request': step['command'],
                                'response': result,
                            })

                        else:

                            try:

                                # 使用Scanner类的execute_step方法执行步骤
                                scanner = Scanner()
                                step_result = scanner.execute_step(step, target_url, session_data)

                                posts_results.append({
                                    'step': step_index + 1,
                                    'request': step_result['request'],
                                    'response': step_result['response'],
                                    'matched': step_result['matched']
                                })

                                # 更新会话数据
                                if 'extracted_data' in step_result:
                                    session_data.update(step_result['extracted_data'])

                                logger.info(f"Posts步骤 {step_index + 1} 执行完成，状态码: {step_result['response'].get('status', 'N/A')}")

                            except Exception as e:
                                logger.error(f"执行posts步骤 {step_index + 1} 时出错: {str(e)}")
                                posts_results.append({
                                    'step': step_index + 1,
                                    'error': str(e)
                                })
                    
                    posts_executed = True
                    break
            
            # 构建消息，如果执行了posts，使用最后一次posts的request和response
            if posts_executed and posts_results:
                # 找到最后一次成功执行的posts步骤
                last_successful_result = None
                for result in reversed(posts_results):
                    if 'request' in result and 'response' in result:
                        last_successful_result = result
                        break
                
                if last_successful_result:
                    # 使用最后一次posts执行的request和response
                    poc_message = message_template.format(
                        url=request['url'], 
                        request=last_successful_result['request'], 
                        response=last_successful_result['response']
                    )
                else:
                    # 如果没有成功的posts结果，使用原始的request和response
                    poc_message = message_template.format(url=request['url'], request=request, response=response)
                
                # 添加posts执行结果摘要
                poc_message += "\n\n=== Posts执行结果 ===\n"
                for result in posts_results:
                    if 'error' in result:
                        poc_message += f"步骤 {result['step']}: 执行失败 - {result['error']}\n"
                    else:
                        poc_message += f"步骤 {result['step']}: 执行成功\n"
            else:
                # 没有执行posts，使用原始的request和response
                poc_message = message_template.format(url=request['url'], request=request, response=response)

            
            add_message(poc_message, pure_id)
            
        except Exception as e:
            logger.error(f"解析POC文件或执行posts步骤时出错: {str(e)}")
            # 如果解析失败，使用原始消息
            poc_message = message_template.format(url=request['url'], request=request, response=response)
            add_message(poc_message, pure_id)
        
        # 开始AI测试。
        # 必须先把 POC 文档与工具说明格式化进提示词，后续每一轮都复用同一个 prompt；
        # 原实现从第 2 轮起传入未格式化的 poc_prompt，字面量 {poc_file} 使模型看不到 POC 内容。
        with open(poc_file, "r", encoding="utf-8") as f:
            poc_content = f.read()
        exploit_prompt = poc_prompt.format(
            request_desc=config.get_addon('request'),
            poc_file=poc_content,
        )
        result = chat(exploit_prompt, pure_id)
        
        # 循环处理result，直到遇到summary标签
        # 使用带上限的循环，避免模型始终不产出 <summary> 时无限循环
        max_steps = 30
        for _step in range(max_steps):
            try:
                # 检查是否包含summary标签
                if '<summary>' in result and '</summary>' in result:
                    # 提取summary标签内容
                    summary_match = re.search(r'<summary>(.*?)</summary>', result, re.DOTALL)
                    if summary_match:
                        summary_xml = f"<summary>{summary_match.group(1)}</summary>"
                        # 将summary标签转换为字典
                        summary_dict = xmltodict.parse(summary_xml)['summary']
                        # 模型可能只输出纯文本 summary，规范化为 dict，避免调用方 .get 崩溃
                        if not isinstance(summary_dict, dict):
                            summary_dict = {
                                'vuln': 'False',
                                'findFlag': 'False',
                                'desc': str(summary_dict),
                                'flag': '',
                            }
                        logger.info(f"漏洞利用完成，返回summary结果: {summary_dict}")
                        return summary_dict
                
                # 检查是否包含value标签
                value_match = re.search(r'<value>(.*?)</value>', result, re.DOTALL)
                if value_match:
                    value_xml = f"<value>{value_match.group(1)}</value>"
                    try:
                        # 将value标签转换为字典
                        value_dict = xmltodict.parse(value_xml)['value']
                        
                        # 调用request.run方法，传入转换后的字典
                        request_result = run(value_dict)
                        
                        # 将request.run的结果添加到对话中
                        add_message(f"执行结果: {request_result}", pure_id)
                        
                        # 继续对话，获取下一步结果
                        result = chat(exploit_prompt, pure_id)
                        
                    except Exception as e:
                        logger.error(f"处理value标签时出错: {str(e)}")
                        # 如果处理value标签失败，直接继续对话
                        result = chat(exploit_prompt, pure_id)
                else:
                    # 如果没有value标签也没有summary标签，继续对话
                    logger.debug("未找到value或summary标签，继续对话")
                    result = chat(poc_prompt, pure_id)
                    
            except Exception as e:
                logger.error(f"处理漏洞利用结果时出错: {str(e)}")
                # 发生异常时，返回空的summary结果
                return {
                    'vuln': 'False',
                    'findFlag': 'False',
                    'desc': f'漏洞利用过程中发生错误: {str(e)}',
                    'flag': ''
                }

        logger.warning("漏洞利用达到最大步数仍未产出 <summary>，按未发现漏洞处理")
        return {
            'vuln': 'False',
            'findFlag': 'False',
            'desc': f'漏洞利用达到最大步数({max_steps})仍未产出总结',
            'flag': ''
        }
        
import os
import subprocess
import sys
import uuid

from config.config import TEMP_PATH

# 单段 Python 代码的最长执行时间（秒）
PYTHON_TIMEOUT = 40


def run(params):
    """
    执行Python代码并返回结果

    :param params: 兼容两种入参：
                   - 直接的 Python 代码字符串（addons.txt 的 <value>Python代码</value>）
                   - 含 code 字段的字典
    :return: 执行结果字符串，失败时以 "Error: " 开头
    """
    if isinstance(params, dict):
        code = params.get("code") or ""
    else:
        code = params if isinstance(params, str) else ""

    if not code.strip():
        return "Error: 未提供 Python 代码"

    temp_file = None
    try:
        os.makedirs(TEMP_PATH, exist_ok=True)
        temp_file = os.path.join(TEMP_PATH, f"{uuid.uuid4()}.py")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        # 使用当前解释器，避免在 Windows（无 python3 命令）上直接失败
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=PYTHON_TIMEOUT,
        )

        if result.returncode == 0:
            return result.stdout
        return f"Error: {result.stderr}"

    except subprocess.TimeoutExpired:
        return f"Error: 执行超时（{PYTHON_TIMEOUT}秒）"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        # 无论成功、失败还是超时都要清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

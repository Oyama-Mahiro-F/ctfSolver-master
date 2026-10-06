import os
import shutil
import subprocess
import uuid

from config.config import TEMP_PATH

# 单条 shell 命令的最长执行时间（秒）
SHELL_TIMEOUT = 30


def _build_invocation(temp_file):
    """选出当前平台真正可用的 shell 调用方式。

    注意 Windows：`C:\\Windows\\System32\\bash.exe` 只是 WSL 的启动器，
    WSL 未启用时任何脚本都会失败，而且它把 UTF-16 的报错写进 stdout、
    stderr 为空，调用方只会拿到一句空的 "Error: "。因此 Windows 上优先用 cmd。
    """
    if os.name == "nt":
        comspec = os.environ.get("COMSPEC") or shutil.which("cmd")
        if comspec:
            return [comspec, "/c", temp_file]
    shell = shutil.which("bash") or shutil.which("sh")
    if shell:
        return [shell, temp_file]
    return None


def run(params):
    """
    执行shell命令并返回结果

    :param params: 兼容三种入参：
                   - dict 且含 command 字段（历史调用约定）
                   - dict 且含 code 字段（addons.txt 文档约定）
                   - 直接的命令字符串
    :return: 执行结果字符串，失败时以 "Error: " 开头
    """
    if isinstance(params, str):
        command = params
    elif isinstance(params, dict):
        command = params.get("command") or params.get("code") or ""
    else:
        command = ""

    if not command.strip():
        return "Error: 未提供 shell 命令（需要 command 或 code 字段）"

    temp_file = None
    try:
        os.makedirs(TEMP_PATH, exist_ok=True)
        suffix = ".cmd" if os.name == "nt" else ".sh"
        temp_file = os.path.join(TEMP_PATH, f"{uuid.uuid4()}{suffix}")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(command)
        os.chmod(temp_file, 0o755)

        invocation = _build_invocation(temp_file)
        if invocation is None:
            return "Error: 未找到可用的 shell（bash/sh 或 cmd）"

        result = subprocess.run(
            invocation,
            capture_output=True,
            text=True,
            timeout=SHELL_TIMEOUT,
        )

        if result.returncode == 0:
            return result.stdout
        # stderr 可能为空（见 _build_invocation 的说明），回退到 stdout，避免空的错误信息
        detail = (result.stderr or result.stdout or "").strip()
        return f"Error: {detail}"

    except subprocess.TimeoutExpired:
        return f"Error: 执行超时（{SHELL_TIMEOUT}秒）"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        # 无论成功、失败还是超时都要清理临时脚本，避免临时文件堆积
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

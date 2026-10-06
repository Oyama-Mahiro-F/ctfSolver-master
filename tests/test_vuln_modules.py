"""漏洞检测模块的入参契约回归测试。

审计发现 simple_detect 在缺少键时抛 KeyError，而 actioner 未包裹 try，
异常会逃逸并导致整条检测思路返回 None。
"""
import base64
import json


def test_other_missing_code_returns_message(agent_path):
    from agents.vulns import OTHER
    result = OTHER.simple_detect({}, {}, {})
    assert isinstance(result, str)


def test_idor_missing_type_returns_message(agent_path):
    from agents.vulns import IDOR
    result = IDOR.simple_detect({}, {}, {})
    assert isinstance(result, str)


def test_idor_jwt_decode_missing_token_returns_message(agent_path):
    from agents.vulns import IDOR
    result = IDOR.simple_detect({}, {}, {"type": "jwt_decode"})
    assert isinstance(result, str)


def test_idor_jwt_decode_works(agent_path):
    from agents.vulns import IDOR

    def b64(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    token = f"{b64({'alg': 'none'})}.{b64({'user_id': 1})}.sig"
    result = IDOR.simple_detect({}, {}, {"type": "jwt_decode", "token": token})
    assert isinstance(result, dict)
    assert result["payload"]["user_id"] == 1


def test_lfi_missing_template_returns_message(agent_path):
    from agents.vulns import LFI
    result = LFI.simple_detect({}, {}, {})
    assert isinstance(result, str)


def test_lfi_normal_missing_value_returns_message(agent_path):
    from agents.vulns import LFI
    result = LFI.simple_detect({}, {}, {"type": "normal", "request": "{}"})
    assert isinstance(result, str)
    assert "value" in result or "缺少" in result

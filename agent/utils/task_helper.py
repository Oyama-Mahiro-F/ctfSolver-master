import json

from utils import sql_helper


def _safe_json_loads(raw):
    """request_json 可能为 NULL 或非法 JSON，不能让整条扫描因一行脏数据中断。"""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def get_all_vulns(task_id):
    sql = f"SELECT * FROM vulns WHERE task_id = '{task_id}'"
    results = sql_helper.SQLiteHelper.execute_query(sql)
    vulns = []
    for result in results:
        vulns.append({
            'id': result[0],
            'task_id': result[1],
            'vuln_type': result[2],
            'desc': result[3],
            'request_json': _safe_json_loads(result[4]),
        })
    return vulns

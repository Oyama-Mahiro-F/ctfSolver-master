import json
import os

from utils.sql_helper import SQLiteHelper


def insert_page_parent(parent_path: str, page_id: str):
    """插入页面的父子关系到数据库"""
    SQLiteHelper.insert_record("pages", {
        "parent_path": parent_path,
        "id": page_id
    })

def get_parent_page(page_id: str) -> dict:
    """根据页面ID获取其父页面信息
    
    Args:
        page_id: 页面ID
        
    Returns:
        父页面信息的字典，如果没有找到返回None
    """
    sql = """
        SELECT parent_path
        FROM pages WHERE id = ?
    """
    result = SQLiteHelper.fetch_one(sql, (page_id,))
    parent_path = result[0] if result else None
    # parent_path 可能为 NULL、不存在或来自其它机器（历史数据里存的是绝对路径），必须容错
    if not parent_path or not os.path.exists(parent_path):
        return {}
    try:
        with open(parent_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def get_pages_info(pages):
    pages_info = ""
    for p in pages:
        pages_info += f"""页面 {p['name']}，id：{p['id']}：\n页面描述：{p.get('description', '')}\n页面请求：{p.get('request')}\n"""
    return pages_info
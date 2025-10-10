# article_utils.py

import os
from utils.git_utils import get_repo_path
from typing import List, Dict,Any

def scan_posts_tree(repo_url: str) -> Dict[str, Any]:
    """
    扫描 _posts 目录，返回包含子目录和文件的树形结构 + 文件总数
    返回格式: { "items": [...], "total": N }
    """
    repo_path = get_repo_path(repo_url)
    posts_dir = os.path.join(repo_path, "source", "_posts")

    if not os.path.exists(posts_dir):
        return {"items": [], "total": 0}

    total_files = 0  #  文件计数器

    def build_tree(root_path: str) -> List[Dict]:
        nonlocal total_files  #  声明使用外层变量
        items = []
        try:
            for name in sorted(os.listdir(root_path)):
                full_path = os.path.join(root_path, name)
                rel_path = os.path.relpath(full_path, posts_dir).replace("\\", "/")

                if os.path.isfile(full_path):
                    if name.lower().endswith(('.md', '.markdown')):
                        total_files += 1  #  计数！
                        items.append({
                            "type": "file",
                            "name": name,
                            "path": rel_path
                        })
                elif os.path.isdir(full_path):
                    children = build_tree(full_path)
                    items.append({
                        "type": "dir",
                        "name": name,
                        "path": rel_path,
                        "children": children
                    })
        except PermissionError:
            pass  # 忽略无权限访问的目录
        return items

    items = build_tree(posts_dir)
    return {
        "items": items,
        "total": total_files
    }


def get_posts_dir(repo_url: str) -> str:
    """根据仓库 URL 获取 _posts 目录"""
    repo_path = get_repo_path(repo_url)
    posts_dir = os.path.join(repo_path, "source", "_posts")
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir, exist_ok=True)
    return posts_dir

def read_post(repo_url: str, filename: str) -> Dict:
    """
    读取文章（支持子目录）
    filename: 可以是 'hello.md' 或 'tech/python.md'
    """
    posts_dir = get_posts_dir(repo_url)
    filepath = os.path.join(posts_dir, filename)  # ✅ 正确拼接子目录路径

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文章不存在: {filename}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析 Front Matter
    import re
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if match:
        fm_lines = match.group(1).splitlines()
        front_matter = {}
        for line in fm_lines:
            if ':' in line:
                k, v = line.split(':', 1)
                front_matter[k.strip()] = v.strip().strip('"\'')
        body = match.group(2)
    else:
        front_matter, body = {}, content

    # 从文件名提取标题（保留原逻辑）
    name_part = os.path.splitext(filename)[0]  # 使用 os.path 分离扩展名
    parts = name_part.split('-', 3)
    title = parts[3].replace('-', ' ').title() if len(parts) >= 4 else name_part

    return {
        "path": filename,  # ✅ 使用相对路径作为唯一 ID
        "filename": front_matter.get("title", title)+".md",
        "title": front_matter.get("title", title),
        "date": front_matter.get("date",
                                 f"{parts[0]}-{parts[1]}-{parts[2]}" if len(parts) >= 3 else ""),
        "draft": str(front_matter.get("draft", "false")),  # 确保是字符串
        "body": content.strip()
    }

def save_post(repo_url: str, filename: str, data: dict):
    """
    保存文章（支持子目录，自动创建目录）
    """
    posts_dir = get_posts_dir(repo_url)
    filepath = os.path.join(posts_dir, filename)

    # ✅ 确保父目录存在
    parent_dir = os.path.dirname(filepath)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # 构建 front-matter
    # front_matter = {
    #     "title": data["title"],
    #     "date": data.get("date", ""),
    #     "tags": data.get("tags", ""),
    #     "categories": data.get("categories", ""),
    #     "draft": str(data.get("draft", "false"))  # 确保是字符串
    # }
    #
    # header = "---\n"
    # for k, v in front_matter.items():
    #     header += f"{k}: {v}\n"
    # header += "---\n\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data["body"].strip() + '\n')


def delete_post(repo_url: str, filename: str):
    """
    删除文章（支持子目录）
    """
    posts_dir = get_posts_dir(repo_url)
    filepath = os.path.join(posts_dir, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
    else:
        raise FileNotFoundError(f"文章不存在，无法删除: {filename}")
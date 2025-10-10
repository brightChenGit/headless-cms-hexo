# git_utils.py

import git
import os
import re
from fastapi import HTTPException

from configs.config import REPOS_BASE_DIR # 会自动触发目录创建

def get_repo_name_from_url(url: str) -> str:
    """从 Git URL 提取仓库名（用作本地目录名）"""
    # 支持 git@ 或 https://
    match = re.search(r'[:/]([^/]+/[^/.]+?)(\.git)?$', url)
    if not match:
        raise ValueError("无效的 Git 仓库地址")
    return match.group(1).replace('/', '-').replace('@', '')

def get_repo_path(repo_url: str) -> str:
    """根据仓库 URL 生成本地路径"""
    repo_name = get_repo_name_from_url(repo_url)
    return os.path.join(REPOS_BASE_DIR, repo_name)

def ensure_repo_cloned(repo_url: str, branch: str = "main") -> str:
    """
    确保仓库已克隆，返回本地路径
    """
    repo_path = get_repo_path(repo_url)
    # 双保险：确保父目录存在
    parent_dir = os.path.dirname(repo_path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # 如果仓库目录不存在，克隆
    if not os.path.exists(repo_path):
        print(f"📁 仓库未克隆，正在克隆 {repo_url} 到 {repo_path}")
        os.makedirs(repo_path, exist_ok=True)
        try:
            git.Repo.clone_from(repo_url, repo_path, branch=branch)
            print(f"✅ 克隆成功")
        except git.exc.GitCommandError as e:
            raise HTTPException(500, detail=f"克隆失败: {str(e)}")
    else:
        print(f"🔁 仓库已存在: {repo_path}")

    return repo_path

def git_pull(repo_url: str, branch: str = "main") -> dict:
    """拉取指定仓库"""
    repo_path = ensure_repo_cloned(repo_url, branch)
    try:
        repo = git.Repo(repo_path)
        print(f"📥 正在拉取 {repo_url}")
        origin = repo.remote()
        result = origin.pull(branch)
        for info in result:
            print(f"Pull: {info}")
        return {"status": "pulled"}
    except Exception as e:
        raise HTTPException(500, detail=f"拉取失败: {str(e)}")

def git_commit_and_push(repo_url: str, branch: str = "main", message: str = None) -> dict:
    """提交并推送"""
    repo_path = ensure_repo_cloned(repo_url, branch)
    try:
        repo = git.Repo(repo_path)
        if not repo.is_dirty(untracked_files=True):
            print("✅ 无更改，无需提交")
            return {"status": "nothing_to_commit"}

        repo.git.add("--all")
        commit_msg = message or f"📝 CMS 更新: {repo_url}"
        repo.index.commit(commit_msg)

        print(f"📤 正在推送 {repo_url}")
        origin = repo.remote()
        result = origin.push(branch)
        for info in result:
            if info.flags & info.ERROR:
                raise git.exc.GitCommandError("push", info.summary)
            print(f"Push: {info.summary}")

        return {"status": "pushed", "commit": commit_msg}
    except Exception as e:
        raise HTTPException(500, detail=f"提交/推送失败: {str(e)}")
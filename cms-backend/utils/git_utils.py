# git_utils.py
import traceback

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

    # 判断是否需要克隆：目录不存在 或 存在但不是有效 Git 仓库
    should_clone = False
    if not os.path.exists(repo_path):
        should_clone = True
    else:
        # 目录存在，检查是否是有效 Git 仓库
        try:
            git.Repo(repo_path)
            print(f"🔁 仓库已存在: {repo_path}")
        except git.exc.InvalidGitRepositoryError:
            print(f"⚠️ 路径存在但不是 Git 仓库（可能是空目录）: {repo_path}")
            should_clone = True
        except Exception:
            # 其他异常（如权限问题）也视为无效，尝试重新克隆
            should_clone = True

    if should_clone:
        print(f"📁 仓库未克隆或无效，正在克隆 {repo_url} 到 {repo_path}")
        # 删除残留目录（如果是无效的）
        if os.path.exists(repo_path):
            import shutil
            shutil.rmtree(repo_path)
        try:
            git.Repo.clone_from(repo_url, repo_path, branch=branch)
            print(f"✅ 克隆成功")
        except git.exc.GitCommandError as e:
            raise HTTPException(500, detail=f"克隆失败: {str(e)}")

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
    except git.exc.GitCommandError as e:
        # 👇 这是最关键的：Git 命令本身的错误（stderr）
        error_detail = (
            f"Git 命令执行失败:\n"
            f"  命令: {e.command}\n"
            f"  返回码: {e.status}\n"
            f"  标准输出: {e.stdout}\n"
            f"  标准错误: {e.stderr}\n"
            f"  完整异常: {str(e)}"
        )
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"Git 拉取失败: {e.stderr or str(e)}")

    except Exception as e:
        # 捕获其他异常（如文件不存在、权限问题等）
        full_trace = traceback.format_exc()
        print(f"❌ 未知错误:\n{full_trace}")
        raise HTTPException(status_code=500, detail=f"拉取失败: {str(e)} (详见日志)")


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
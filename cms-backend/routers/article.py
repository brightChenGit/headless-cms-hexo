# routers/article.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List,Any
from datetime import datetime

from configs.config import current_repo
from model.articleModel import ArticleCreate
from utils.token_utils import verify_token
from utils.git_utils import git_pull, git_commit_and_push, ensure_repo_cloned
from utils.article_utils import scan_posts_tree, read_post, save_post, delete_post
from commons.articleCache import MultiRepoCacheManager

router = APIRouter(prefix="/api", tags=["Article"])
# 全局缓存管理器
cache_manager = MultiRepoCacheManager()
# 获取全局 current_repo（来自 repo.py）
def get_current_repo():
    if not current_repo["url"]:
        raise HTTPException(status_code=400, detail="请先调用 /api/setup 设置仓库")
    return current_repo


# ----------------------------s
# 列出所有文章
# ----------------------------
@router.post("/list", response_model=Dict[str, Any])
def list_article(data: Dict,token: str = Depends(verify_token)):

    try:
        repo_url = data.get("repo_url")
        branch = data.get("branch", "main")

        # 入参空但配置有数据，使用配置数据
        if not repo_url and current_repo["url"]:
            repo_url=  current_repo["url"]
            branch= current_repo["branch"]
            # repo_path = ensure_repo_cloned(repo_url, branch)
            # current_repo["path"] = repo_path
            # git_pull(repo_url, branch)
            # return scan_posts_tree(repo_url)

        #无入参且配置为空
        if not repo_url and not current_repo["url"]:
            raise HTTPException(status_code=400, detail="缺少 repo_url")


        cached_data = cache_manager.get_cached_data(repo_url, branch)
        if cached_data is not None:
            return cached_data

        repo_path = ensure_repo_cloned(repo_url, branch)

        current_repo["url"] = repo_url
        current_repo["branch"] = branch
        current_repo["path"] = repo_path

        git_pull(repo_url, branch)
        data_result = scan_posts_tree(repo_url)

        # 更新缓存并启动后台刷新
        cache_manager.set_cached_data(repo_url, branch, data_result)

        return data_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {str(e)}")

# ----------------------------
# 创建文章
# ----------------------------
@router.post("/saveArticle",summary="创建文章")
def create_article(post: ArticleCreate, token: str = Depends(verify_token)):
    post_dirct=post.model_dump()
    repo = get_current_repo()
    repo_url = repo["url"]
    branch = repo["branch"]

    title = post_dirct.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")

    git_pull(repo_url, branch)

    date_str = post_dirct.get("date")
    if date_str:
        try:
            now = date_str.split()[0]  # 取第一部分，如 "2025-09-23 10:00:00" → "2025-09-23"
        except (AttributeError, IndexError):
            now = datetime.now().strftime("%Y-%m-%d")
    else:
        now = datetime.now().strftime("%Y-%m-%d")
    slug = title.replace(' ', '-').lower()
    filename = post_dirct.get("path")

    try:
        save_post(repo_url, filename, post_dirct)

        git_commit_and_push(
            repo_url,
            branch=branch,
            message=f"✏️ 更新: {title}"
        )
        # 执行手动刷新
        data_result = cache_manager.refresh_cache(repo_url, branch)
        return {"id": filename, "message": "创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

# ----------------------------
# 获取单篇文章
# ----------------------------
@router.post("/getArticle")
def get_article(post: Dict, token: str = Depends(verify_token)):
    filename = post.get("path")
    if not filename.endswith(".md"):
        filename += ".md"
    repo = get_current_repo()
    try:
        return read_post(repo["url"], filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文章未找到")

# ----------------------------
# 更新文章-提交到git上
# ----------------------------
@router.post("/updateGit")
def update_article(post: Dict, token: str = Depends(verify_token)):

    repo = get_current_repo()
    repo_url = repo["url"]
    branch = repo["branch"]
    comment = post.get("comment")
    try:
        git_commit_and_push(
            repo_url,
            branch=branch,
            message=f"✏️ 更新: {comment}"
        )
        data_result = cache_manager.refresh_cache(repo_url, branch)
        return {"message": "更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

# ----------------------------
# 删除文章
# ----------------------------
@router.post("/delete")
def remove_article(post: Dict, token: str = Depends(verify_token)):
    filename = post.get("path")

    if not filename.endswith(".md"):
        filename += ".md"

    repo = get_current_repo()
    repo_url = repo["url"]
    branch = repo["branch"]

    try:
        post = read_post(repo_url, filename)
        title = post["title"]
    except:
        title = filename

    git_pull(repo_url, branch)

    try:
        delete_post(repo_url, filename)
        git_commit_and_push(
            repo_url,
            branch=branch,
            message=f"🗑️ 删除: {title}"
        )
        data_result = cache_manager.refresh_cache(repo_url, branch)
        return {"message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
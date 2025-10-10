# routers/repo.py

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict

from configs.config import SECRET_TOKEN,current_repo
from utils.git_utils import ensure_repo_cloned
from utils.token_utils import verify_token


router = APIRouter(prefix="/api", tags=["Repository"])


@router.post("/setup")
def setup_repo(data: Dict, token: str = Depends(verify_token)) -> Dict:
    repo_url = data.get("repo_url")
    branch = data.get("branch", "main")

    if not repo_url:
        raise HTTPException(status_code=400, detail="缺少 仓库地址")

    try:
        repo_path = ensure_repo_cloned(repo_url, branch)
        current_repo["url"] = repo_url
        current_repo["branch"] = branch
        current_repo["path"] = repo_path

        return {
            "message": "仓库设置成功",
            "repo_url": repo_url,
            "branch": branch,
            "posts_dir": f"{repo_path}/source/_posts"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")

@router.get("/status")
def get_status(token: str = Depends(verify_token)) -> Dict:
    if not current_repo["url"]:
        return {"status": "未设置仓库"}
    return current_repo
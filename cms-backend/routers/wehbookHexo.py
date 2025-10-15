# routers/webhook.py

import threading

from fastapi import APIRouter, Request, HTTPException,Depends,Query

from commons.deployCache import get_task, update_task, create_task, get_last_task_by_triggered_by
from configs.config import current_repo  # 复用已有的全局仓库配置
from utils.git_utils import git_pull, git_commit_and_push
from utils.token_utils import verify_token  # 复用 Token 校验
from loguru import logger
from datetime import datetime
from utils.webhook_utils import HexoBuilder

router = APIRouter(prefix="/webhookHexo", tags=["WebhookHexo"])
class BuildInterruptedError(Exception):
    def __init__(self, message: str, results: list):
        super().__init__(message)
        self.results = results

def get_hexo_repo_path():
    """获取当前配置的 Hexo 仓库本地路径"""
    if not current_repo.get("path"):
        raise HTTPException(status_code=400, detail="请先调用 /api/setup 或 /api/list 设置仓库")
    return current_repo["path"]


def run_hexo_build_with_callback(repo_path: str, task_id: str = None, triggered_by: str = None):
    """带状态回调的 Hexo 构建（供后台线程调用）"""
    def _update_status(step_name: str, status: str, message: str = "", error: str = "", stdout: str = ""):
        if task_id:
            step = {
                "step": step_name,
                "status": status,
                "message": message,
                "error": error,
                "stdout": stdout[:500] if stdout else "",  # 防止过大
            }
            current = get_task(task_id)
            if current:
                steps_list = current.get("steps", []) + [step]  # 避免与外层 steps 冲突
                # 判断是否是最后一步（npx hexo generate）
                is_final_step = (step_name == "npx hexo generate")
                update_task(
                    task_id,
                    status="success" if status == "success" and is_final_step else "running",
                    message=message or f"正在执行: {step_name}",
                    steps=steps_list
                )

    results = []

    # === Step 1: Git Pull ===
    repo_url = current_repo.get("url")
    branch = current_repo.get("branch", "main")
    if not repo_url:
        error_msg = "未配置仓库 URL"
        _update_status("git_pull", "failure", error=error_msg)
        raise BuildInterruptedError(error_msg, [{"step": "git_pull", "status": "error", "error": error_msg}])

    try:
        logger.info("🔄 正在拉取最新代码...")
        git_pull(repo_url, branch)
        _update_status("git_pull", "success", f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Git 拉取成功 ")
        results.append({"step": "git_pull", "status": "success"})
    except Exception as e:
        err_str = str(e)
        _update_status("git_pull", "failure", error=err_str)
        raise BuildInterruptedError(f"Git 拉取失败: {err_str}", [{"step": "git_pull", "status": "error", "error": err_str}])

    # === Step 2: Hexo 构建 ===
    # === Step 2: Hexo 构建 ===
    try:
        builder = HexoBuilder(repo_path=repo_path)
        steps = [
            ("npm install", ["npm", "install"]),
            ("npx hexo clean", ["npx", "hexo", "clean"]),
            ("npx hexo generate", ["npx", "hexo", "generate"]),
        ]

        for action_name, cmd in steps:
            try:
                logger.info(f"正在执行: {action_name}")
                cmd_stdout = builder.run_command(cmd)
                _update_status(action_name, "success", message=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {action_name} success", stdout=cmd_stdout)
                results.append({
                    "step": action_name,
                    "status": "success",
                    "stdout": cmd_stdout,
                })
                logger.info(f"✅ 执行成功: {cmd_stdout[:200].strip()}...")
            except Exception as e:
                err_msg = str(e)
                _update_status(action_name, "failure", message=action_name + " error", error=err_msg)
                results.append({
                    "step": action_name,
                    "status": "error",
                    "error": err_msg,
                })
                raise BuildInterruptedError(err_msg, results)

        # ✅ 构建成功，但不 return！继续执行推送
        logger.info("🎉 Hexo 构建成功，准备推送部署...")

    except Exception as e:
        if task_id:
            update_task(task_id, status="failure", message=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 构建失败: {str(e)}")
        raise  # 重新抛出，中断流程

    # === Step 3: 提交并推送构建结果 ===
    try:
        commit_msg = f"Deploy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        git_commit_and_push(
            repo_url,
            branch=branch,
            message=f"✏️ 部署更新"
        )
        _update_status("git_commit_and_push", "success", message="✅ 构建产物已成功推送至 Git")
        results.append({
            "step": "git_commit_and_push",
            "status": "success",
            "message": "Git 推送成功"
        })
    except Exception as e:
        err_msg = f"Git 提交与推送失败: {str(e)}"
        _update_status("git_commit_and_push", "failure", error=err_msg)
        results.append({
            "step": "git_commit_and_push",
            "status": "error",
            "error": err_msg
        })
        raise BuildInterruptedError(err_msg, results)

    # ✅ 所有步骤完成，最终返回
    if task_id:
        update_task(task_id, status="success", message=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Hexo 构建并部署成功！")
    return results



def run_hexo_build(repo_path: str):
    """执行 Hexo 构建流程（Git Pull + 构建），支持 Windows / Linux / macOS"""
    results = []

    # === Step 1: Git Pull ===
    repo_url = current_repo.get("url")
    branch = current_repo.get("branch", "main")
    if not repo_url:
        error_msg = "未配置仓库 URL"
        results.append({"step": "git_pull", "status": "error", "error": error_msg})
        raise BuildInterruptedError(error_msg, results)

    try:
        logger.info("🔄 正在拉取最新代码...")
        git_pull(repo_url, branch)
        results.append({"step": "git_pull", "status": "success"})
        logger.info("✅ Git 拉取成功")
    except Exception as e:
        error_msg = f"Git 拉取失败: {str(e)}"
        results.append({"step": "git_pull", "status": "error", "error": str(e)})
        logger.error(f"❌ {error_msg}")
        raise BuildInterruptedError(error_msg, results)

    # === Step 2: Hexo 构建 ===
    try:
        builder = HexoBuilder(repo_path=repo_path)
        steps = [
            ("npm install", ["npm", "install"]),
            ("npx hexo clean", ["npx", "hexo", "clean"]),
            ("npx hexo generate", ["npx", "hexo", "generate"]),
        ]

        for step_name, cmd in steps:
            try:
                logger.info(f"正在执行: {step_name}")
                stdout = builder.run_command(cmd)
                results.append({
                    "step": step_name,
                    "status": "success",
                    "stdout": stdout,
                    "stderr": ""
                })
                logger.info(f"✅ 执行成功: {stdout[:200].strip()}...")
            except Exception as e:
                err_msg = str(e)
                results.append({
                    "step": step_name,
                    "status": "error",
                    "error": err_msg,
                    "stdout": "",
                    "stderr": ""
                })
                logger.error(f"❌ {step_name} → {err_msg}")
                raise BuildInterruptedError(err_msg, results)

    except BuildInterruptedError:
        raise  # 透传中断异常
    except Exception as e:
        # 捕获 HexoBuilder 初始化等意外错误
        error_msg = f"构建系统异常: {str(e)}"
        results.append({
            "step": "build_system",
            "status": "error",
            "error": error_msg
        })
        logger.error(f"💥 构建系统崩溃: {error_msg}")
        raise BuildInterruptedError(error_msg, results)

    logger.info("🎉 Hexo 构建全部成功！")
    return results


@router.post("/deploy")
async def trigger_hexo_build_async(
        request: Request,
        token: str = Depends(verify_token)
):
    repo_path = get_hexo_repo_path()
    client_ip = request.client.host
    logger.info(f"📥 异步部署请求，来源IP: {client_ip}")

    # 1. 创建任务
    task_id = create_task(token)

    update_task(task_id, triggered_by=token)

    # 2. 启动后台线程执行
    def background_worker():
        try:
            run_hexo_build_with_callback(repo_path, task_id=task_id, triggered_by=client_ip)
        except Exception as e:
            logger.exception(f"后台任务异常: {e}")
            # 异常已在 run_hexo_build_with_callback 中处理

    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()

    # 3. 立即返回 task_id
    return {
        "status": "accepted",
        "task_id": task_id,
        "message": "部署任务已提交，正在后台执行",
        "triggered_by": client_ip
    }

@router.get("/status")
async def get_deploy_status(
        task_id: str = Query(None, description="任务ID"),
        token: str = Depends(verify_token)
):
    task = None
    if task_id and task_id.strip():
        task = get_task(task_id)
    else:
        # 未指定 task_id：获取该用户最近一次任务
        task = get_last_task_by_triggered_by(token)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    return {
        "task_id": task_id,
        "status": task["status"],  # queued | running | success | failure
        "message": task.get("message", ""),
        "triggered_by": task.get("triggered_by"),
        "steps": task.get("steps", []),
        "created_at": task.get("created_at")
    }
# 异步执行构建，避免阻塞响应
# background_tasks.add_task(run_hexo_build, repo_path)
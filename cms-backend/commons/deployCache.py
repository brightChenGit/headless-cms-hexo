import time
from typing import Dict, Any
import uuid

TASKS: Dict[str, Dict[str, Any]] = {}
MAX_TASK_AGE = 3600  # 1 小时（秒）
MAX_TASK_COUNT = 50  # 最多保留 50 个任务（可选）

def _cleanup_old_tasks():
    """清理过期或过多的任务"""
    now = time.time()
    to_delete = []

    # 标记过期任务
    for tid, task in TASKS.items():
        if now - task.get("created_at", 0) > MAX_TASK_AGE:
            to_delete.append(tid)

    # 如果数量超限，按创建时间删除最老的（可选）
    if len(TASKS) - len(to_delete) > MAX_TASK_COUNT:
        # 按 created_at 排序，取最老的
        sorted_tasks = sorted(
            [(tid, task) for tid, task in TASKS.items() if tid not in to_delete],
            key=lambda x: x[1].get("created_at", 0)
        )
        excess = len(sorted_tasks) - MAX_TASK_COUNT
        if excess > 0:
            to_delete.extend(tid for tid, _ in sorted_tasks[:excess])

    # 执行删除
    for tid in to_delete:
        TASKS.pop(tid, None)

def create_task(triggered_by: str = "unknown") -> str:
    _cleanup_old_tasks()  # 创建前清理过期任务

    task_id = f"_hexo_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    TASKS[task_id] = {
        "status": "queued",
        "message": "任务已提交，等待执行",
        "steps": [],
        "created_at": time.time(),
        "triggered_by": triggered_by
    }
    return task_id

def update_task(task_id: str, **kwargs):
    if task_id in TASKS:
        TASKS[task_id].update(kwargs)

def get_task(task_id: str):
    return TASKS.get(task_id)


def get_last_task_by_triggered_by(triggered_by: str):
    """
    获取指定用户最近一次创建的任务（按 created_at 最新）
    :param triggered_by: 用户标识（token / user_id）
    :return: 任务 dict 或 None
    """
    if not isinstance(triggered_by, str):
        return None

    candidate_tasks = [
        task for task in TASKS.values()
        if task.get("triggered_by") == triggered_by
    ]

    if not candidate_tasks:
        return None

    # 按 created_at 降序，取第一个（最新）
    latest_task = max(candidate_tasks, key=lambda t: t.get("created_at", 0))
    return latest_task
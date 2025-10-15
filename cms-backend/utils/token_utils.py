
from fastapi import  HTTPException, Header,Request
from pydantic.v1.validators import max_str_int

from configs.config import SECRET_TOKEN,AUTH_STORAGE
from datetime import datetime, timedelta

MAX_FAILED_BEFORE_TEMP_BAN = 20
TEMP_BAN_DURATION = timedelta(minutes=5)
MAX_FAILED_BEFORE_PERM_BAN = 50



def verify_token(request: Request) -> str:
    client_ip = request.client.host
    now = datetime.now()

    # 获取当前失败记录
    failed_count, unban_time = AUTH_STORAGE.get_failed_attempts(client_ip)

    # 检查是否在临时封禁期内
    if unban_time and now < unban_time:
        remain_sec = int((unban_time - now).total_seconds())
        raise HTTPException(
            status_code=403,
            detail=f"请求过于频繁，IP {client_ip} 被临时封禁，请 {remain_sec} 秒后重试"
        )

    # 检查是否永久封禁
    if failed_count >= MAX_FAILED_BEFORE_PERM_BAN:
        raise HTTPException(
            status_code=403,
            detail=f"IP {client_ip} 因多次验证失败已被永久封禁"
        )


    authorization = request.headers.get("Authorization")

    """
    验证 Bearer Token
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="缺少认证头",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="认证头格式错误，应为 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]
    if token != SECRET_TOKEN:
        # 记录ip错误次数，准备封禁
        _record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=401,
            detail="无效或过期的 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # ✅ 验证成功，清空失败记录（可选）
    AUTH_STORAGE.clear_failed_attempts(client_ip)
    return token  # 认证通过



def _record_failed_attempt(ip: str):
    """记录一次失败，并判断是否需要封禁"""
    now = datetime.now()
    failed_count, unban_time = AUTH_STORAGE.get_failed_attempts(ip)

    # 如果之前被封但已过期，重置计数
    if unban_time and now >= unban_time :
        failed_count = 0
        unban_time = None

    failed_count += 1

    # 达到临时封禁阈值，且未永久封禁
    if MAX_FAILED_BEFORE_TEMP_BAN <= failed_count < MAX_FAILED_BEFORE_PERM_BAN:
        unban_time = now + TEMP_BAN_DURATION

    # 更新记录
    AUTH_STORAGE.set_failed_attempts(ip, failed_count, unban_time)
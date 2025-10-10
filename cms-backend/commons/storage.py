# storage.py
from abc import ABC, abstractmethod
from datetime import datetime
from threading import Lock
from typing import Optional, Tuple

class IFailedAuthStorage(ABC):
    @abstractmethod
    def get_failed_attempts(self, ip: str) -> Tuple[int, Optional[datetime]]:
        pass

    @abstractmethod
    def set_failed_attempts(self, ip: str, count: int, unban_time: Optional[datetime] = None):
        pass

    @abstractmethod
    def clear_failed_attempts(self, ip: str):
        pass

# 内存存储

class MemoryStorage(IFailedAuthStorage):
    def __init__(self):
        self._store: dict[str, tuple[int, datetime | None]] = {}
        self._lock = Lock()

    def get_failed_attempts(self, ip: str) -> Tuple[int, Optional[datetime]]:
        with self._lock:
            return self._store.get(ip, (0, None))

    def set_failed_attempts(self, ip: str, count: int, unban_time: Optional[datetime] = None):
        with self._lock:
            self._store[ip] = (count, unban_time)

    def clear_failed_attempts(self, ip: str):
        with self._lock:
            self._store.pop(ip, None)




# import redis
# import json
#
# class RedisStorage(IFailedAuthStorage):
#     def __init__(self, redis_url="redis://localhost:6379/0"):
#         self.client = redis.from_url(redis_url, decode_responses=True)
#         self.prefix = "auth_fail:"
#
#     def _key(self, ip: str) -> str:
#         return f"{self.prefix}{ip}"
#
#     def get_failed_attempts(self, ip: str) -> Tuple[int, Optional[datetime]]:
#         data = self.client.get(self._key(ip))
#         if not data:
#             return 0, None
#         obj = json.loads(data)
#         unban_time = datetime.fromisoformat(obj["unban_time"]) if obj.get("unban_time") else None
#         return obj["count"], unban_time
#
#     def set_failed_attempts(self, ip: str, count: int, unban_time: Optional[datetime] = None):
#         data = {
#             "count": count,
#             "unban_time": unban_time.isoformat() if unban_time else None
#         }
#         self.client.set(self._key(ip), json.dumps(data))
#
#     def clear_failed_attempts(self, ip: str):
#         self.client.delete(self._key(ip))
import threading
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

from configs.config import current_repo
from utils.article_utils import scan_posts_tree
from utils.git_utils import ensure_repo_cloned, git_pull

## 每次缓存间隔 300S
CACHE_FLUSH_TIME=300

# ============= 缓存条目 =============
class CacheEntry:
    def __init__(self, repo_url: str, branch: str):
        self.repo_url = repo_url
        self.branch = branch
        self.data = None
        self.last_updated: Optional[datetime] = None
        self.lock = threading.RLock()  # 每个仓库独立锁
        self.stop_event = threading.Event()
        self.background_thread: Optional[threading.Thread] = None

    def set_data(self, data):
        with self.lock:
            self.data = data
            self.last_updated = datetime.now()

    def get_data(self):
        with self.lock:
            return self.data

    def start_background_refresh(self):
        """为当前仓库启动后台刷新线程"""
        self.stop_background_refresh()  # 先停止旧线程

        def refresh_loop():
            while not self.stop_event.is_set():
                try:
                    repo_path = ensure_repo_cloned(self.repo_url, self.branch)
                    git_pull(self.repo_url, self.branch)
                    data = scan_posts_tree(self.repo_url)
                    self.set_data(data)
                    print(f"[{datetime.now()}] 仓库 {self.repo_url}@{self.branch} 缓存已刷新")
                except Exception as e:
                    print(f"[{datetime.now()}] 仓库 {self.repo_url}@{self.branch} 后台刷新失败: {e}")
                time.sleep(CACHE_FLUSH_TIME)

        self.background_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.background_thread.start()

    def stop_background_refresh(self):
        if self.background_thread and self.background_thread.is_alive():
            self.stop_event.set()
            self.background_thread.join(timeout=2)
            self.stop_event.clear()


# ============= 缓存管理器（支持多仓库） =============
class MultiRepoCacheManager:
    def __init__(self):
        self._caches: Dict[Tuple[str, str], CacheEntry] = {}
        self._global_lock = threading.RLock()  # 用于管理 _caches 字典本身

    def get_cache_entry(self, repo_url: str, branch: str) -> CacheEntry:
        key = (repo_url, branch)
        with self._global_lock:
            if key not in self._caches:
                self._caches[key] = CacheEntry(repo_url, branch)
            return self._caches[key]

    def get_cached_data(self, repo_url: str, branch: str):
        entry = self.get_cache_entry(repo_url, branch)
        return entry.get_data()

    def set_cached_data(self, repo_url: str, branch: str, data):
        entry = self.get_cache_entry(repo_url, branch)
        entry.set_data(data)
        # 自动启动后台刷新（如果尚未启动）
        if not (entry.background_thread and entry.background_thread.is_alive()):
            entry.start_background_refresh()

    def refresh_cache(self, repo_url: str, branch: str):
        """手动刷新指定仓库缓存"""
        entry = self.get_cache_entry(repo_url, branch)
        try:
            repo_path = ensure_repo_cloned(repo_url, branch)
            git_pull(repo_url, branch)
            data = scan_posts_tree(repo_url)
            entry.set_data(data)
            # 确保后台线程运行
            if not (entry.background_thread and entry.background_thread.is_alive()):
                entry.start_background_refresh()
            return data
        except Exception as e:
            raise Exception(f"手动刷新失败: {str(e)}")

    def get_cache_status(self, repo_url: str, branch: str):
        entry = self.get_cache_entry(repo_url, branch)
        with entry.lock:
            return {
                "repo_url": entry.repo_url,
                "branch": entry.branch,
                "has_data": entry.data is not None,
                "last_updated": entry.last_updated.isoformat() if entry.last_updated else None,
                "background_thread_alive": entry.background_thread is not None and entry.background_thread.is_alive(),
            }

    def get_all_cache_status(self):
        with self._global_lock:
            return {
                f"{key[0]}@{key[1]}": self.get_cache_status(key[0], key[1])
                for key in self._caches.keys()
            }



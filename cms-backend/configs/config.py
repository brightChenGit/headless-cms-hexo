# config.py
import os
from pathlib import Path
from commons.storage import MemoryStorage

# ========== 开发用内存 ==========
AUTH_STORAGE = MemoryStorage()

# ========== 生产用 Redis（取消注释即可切换） ==========
# AUTH_STORAGE = RedisStorage("redis://localhost:6379/0")


# 项目根目录 (cmsBackend/)
BASE_DIR = Path(__file__).parent.parent.resolve()
# 所有仓库的根目录
REPOS_BASE_DIR = BASE_DIR /"repos"

# 固定 Token
SECRET_TOKEN = os.getenv("ACCESS_TOKEN", "自定义token")  # 从环境变量读取,默认为"token"


# 全局变量（生产环境建议替换为数据库） hexo的git仓库地址和
current_repo = {
    "url": os.getenv("HEXO_GIT_REPO", "git@gitee.com:xxx-hexo.git"),# 从环境变量读取,hexo的git地址
    "branch": os.getenv("HEXO_GIT_BRANCH", "master"),# 从环境变量读取,hexo的git 分支 一般为master或者main
    "path": None #后续自动初始化
}

# 确保目录存在
if not os.path.exists(REPOS_BASE_DIR):
    print(f"📁 目录 {REPOS_BASE_DIR} 不存在，正在创建...")
    os.makedirs(REPOS_BASE_DIR, exist_ok=True)
    print(f"✅ {REPOS_BASE_DIR} 创建成功")
else:
    print(f"🔁 目录已存在: {REPOS_BASE_DIR}")
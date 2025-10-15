# run.py

"""
🚀 启动 FastAPI 服务
使用方式：python run.py
"""

import uvicorn

if __name__ == "__main__":
    print("🌍 启动 Hexo Headless CMS API")
    print("📌 访问文档: http://localhost:3001/docs")
    print("🛑 按 Ctrl+C 停止 服务\n")

    uvicorn.run(
        "main:app",           # 🔥 使用字符串形式
        host="0.0.0.0",
        port=3001,
        reload=True,          # ✅ 现在热重载会生效
        log_level="info"
    )
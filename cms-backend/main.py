# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from routers import repo, article,wehbookHexo

app = FastAPI(docs_url=None, version="1.0.0")  # 禁用默认 /docs

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(

        openapi_url="/openapi.json",
        title =" Hexo Headless CMS",
        swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js",
        swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui.css",
    )


# ----------------------------
# CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# 注册路由
# ----------------------------
app.include_router(repo.router)
app.include_router(article.router)
app.include_router(wehbookHexo.router)

# ----------------------------
# 根路径提示
# ----------------------------
@app.get("/")
def read_root():
    return {
        "message": "Hexo Headless CMS API",
        "docs": "/docs",
        "redoc": "/redoc"
    }
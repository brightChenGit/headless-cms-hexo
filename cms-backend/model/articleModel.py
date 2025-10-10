# schemas.py
from pydantic import BaseModel
from typing import Optional
from pydantic import Field

class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, description="文章标题，不能为空")
    path: str = Field(..., description="自定义文件路径，不能为空")
    date: Optional[str] = Field(None, description="发布日期，格式 YYYY-MM-DD")
    body: Optional[str] = Field(None, description="Markdown 内容")
    draft: bool = Field(False, description="是否为草稿")

    class Config:
        json_schema_extra  = {
            "example": {
                "path": "posts/my-first-post.md",
                "title": "我的第一篇文章",
                "date": "2025-09-19",
                "body": "---\ntitle: 我的第一篇文章\n---\n这是正文...",
                "draft": False
            }
        }
# hexo_builder.py
import subprocess
import sys
from pathlib import Path

def _resolve_executable(name: str) -> str:
    """根据平台返回正确 cl的可执行文件名"""
    if sys.platform == "win32":
        if name in ("npm", "npx"):
            return f"{name}.cmd"
        # 其他工具如 node → node.exe（但一般不需要）
        return f"{name}.exe"
    else:
        return name


class HexoBuilder:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"仓库路径不存在: {repo_path}")

    def run_command(self, cmd: list, cwd=None):
        """
        跨平台安全执行命令
        - Windows: 自动使用 .cmd 后缀
        - 所有平台: 显式指定 encoding='utf-8'
        """
        if not cmd:
            raise ValueError("命令不能为空")

        cwd = cwd or self.repo_path
        resolved_cmd = [_resolve_executable(cmd[0])] + cmd[1:]

        try:
            result = subprocess.run(
                resolved_cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,
                encoding='utf-8'
            )
            return result.stdout
        except FileNotFoundError:
            cmd_str = ' '.join(resolved_cmd)
            raise RuntimeError(
                f"命令未找到: {cmd_str}。\n"
                f"请确保 Node.js 已安装并加入系统 PATH。\n"
                f"当前平台: {sys.platform}"
            )
        except subprocess.CalledProcessError as e:
            # 抛出带 stderr 的异常，便于上层捕获
            raise RuntimeError(e.stderr.strip() or "命令执行失败，无错误输出") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("命令执行超时（5分钟）") from e

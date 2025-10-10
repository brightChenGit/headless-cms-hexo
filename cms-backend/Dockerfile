# Dockerfile - 放在 cmsBackend/ 目录下
# 基于 Python 3.11 官方轻量镜像
FROM python:3.13-slim

# 设置默认时区（可在 docker-compose 中覆盖）
ENV TZ=Asia/Shanghai

# 安装 Git + OpenSSH + ca-certificates
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gnupg \
    openssh-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ========== 安装 Node.js 20.x (LTS) ==========
# 添加 NodeSource 源并安装 Node.js
# 添加 NodeSource APT 源（Node.js 20.x）
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/trusted.gpg.d/nodesource.gpg \
    && echo "deb [arch=amd64] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list

# 安装 Node.js 和 npm
RUN apt-get update && apt-get install -y \
    nodejs \
    && npm install -g npm@latest \
    && npm install -g hexo-cli \
    && node --version \
    && npm --version \
    && hexo --version \
    && rm -rf /var/lib/apt/lists/*



# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装（利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用源码
COPY . .

# ========== SSH 配置 ==========
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh



# 设置 Git 使用指定私钥（可在 docker-compose 中覆盖）
ENV GIT_SSH_COMMAND="ssh -i /root/.ssh/id_rsa -o IdentitiesOnly=yes"

# ========== 启动脚本：动态设置时区 + Git 用户 + known_hosts ==========
RUN echo '#!/bin/bash\n\
\n\
# ========== 设置时区 ==========\n\
if [ -n "$TZ" ]; then\n\
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone\n\
    echo "🌍 时区已设置为: $TZ"\n\
fi\n\
\n\
# ========== 设置 Git 用户（从环境变量读取） ==========\n\
GIT_USER_NAME="${GIT_USER_NAME:-HexoDeployer}"\n\
GIT_USER_EMAIL="${GIT_USER_EMAIL:-deploy@yourdomain.com}"\n\
git config --global user.name "$GIT_USER_NAME"\n\
git config --global user.email "$GIT_USER_EMAIL"\n\
echo "👤 Git 用户已设置为: $GIT_USER_NAME <$GIT_USER_EMAIL>"\n\
\n\
# ========== 生成 known_hosts ==========\n\
HOSTS="${SSH_KNOWN_HOSTS:-github.com gitee.com}"\n\
echo "🔐 正在为以下主机生成 known_hosts: $HOSTS"\n\
ssh-keyscan $HOSTS > /root/.ssh/known_hosts 2>/dev/null\n\
chmod 644 /root/.ssh/known_hosts\n\
echo "✅ known_hosts 已生成，共 $(wc -l < /root/.ssh/known_hosts) 行"\n\
\n\
# ========== 启动应用 ==========\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info\n\
' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# 设置启动脚本
ENTRYPOINT ["/entrypoint.sh"]
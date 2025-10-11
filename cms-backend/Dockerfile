#
FROM python:3.13-slim

# 设置时区
ENV TZ=Asia/Shanghai

# ========== 替换为清华 Debian 源（支持 bookworm）==========
RUN CODENAME=$(grep -oP 'VERSION_CODENAME=\K\w+' /etc/os-release) && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $CODENAME main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security $CODENAME-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $CODENAME-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list


# 安装依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gnupg \
    xz-utils \
    openssh-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ========== 2. 使用国内镜像安装 Node.js 20.x ==========
# 方案：直接下载 Node.js 二进制包（绕过 NodeSource）
ENV NODE_VERSION=20.17.0
ENV NODE_DISTRO=linux-x64

# 从淘宝 NPM 镜像下载 Node.js
RUN curl -fsSL https://npmmirror.com/mirrors/node/v${NODE_VERSION}/node-v${NODE_VERSION}-${NODE_DISTRO}.tar.xz | tar -xJ -C /usr/local --strip-components=1

# 验证安装
RUN node --version && npm --version

# ========== 3. 设置 npm 使用国内镜像 ==========
RUN npm config set registry https://registry.npmmirror.com

# 安装 Hexo CLI（现在走淘宝镜像，极快）
RUN npm install -g hexo-cli && hexo --version

# ========== 4. 安装 Python 依赖（你已用清华源，保留）==========
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码
COPY . .

# ========== SSH 配置 ==========
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# 设置 Git SSH 命令
ENV GIT_SSH_COMMAND="ssh -i /root/.ssh/id_rsa -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"

# ========== 启动脚本（保持不变）==========
RUN echo '#!/bin/bash\n\
if [ -n "$TZ" ]; then\n\
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone\n\
    echo "🌍 时区已设置为: $TZ"\n\
fi\n\
GIT_USER_NAME="${GIT_USER_NAME:-HexoDeployer}"\n\
GIT_USER_EMAIL="${GIT_USER_EMAIL:-deploy@yourdomain.com}"\n\
git config --global user.name "$GIT_USER_NAME"\n\
git config --global user.email "$GIT_USER_EMAIL"\n\
echo "👤 Git 用户已设置为: $GIT_USER_NAME <$GIT_USER_EMAIL>"\n\
HOSTS="${SSH_KNOWN_HOSTS:-github.com gitee.com}"\n\
ssh-keyscan $HOSTS > /root/.ssh/known_hosts 2>/dev/null\n\
chmod 644 /root/.ssh/known_hosts\n\
echo "✅ known_hosts 已生成"\n\
exec uvicorn main:app --host 0.0.0.0 --port 3000 --log-level info\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
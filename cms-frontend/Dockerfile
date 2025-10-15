# 第一阶段：构建阶段
FROM node:24-alpine AS build

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json（确保依赖锁定）
COPY package*.json ./

# 安装依赖（使用 --frozen-lockfile 确保一致性，npm 用 --no-fund --silent 可选）
RUN npm ci --silent

# 复制源代码
COPY . .

# 构建生产版本（Vite 默认输出到 dist/）
RUN npm run build

# 第二阶段：运行阶段（使用 Nginx 托管静态资源）
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 可选：复制自定义 Nginx 配置（支持 Vue Router history 模式）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# 启动 Nginx（前台运行）
CMD ["nginx", "-g", "daemon off;"]
# 第一阶段：构建项目
# 使用带有 Node.js 的官方基础镜像
FROM node:latest as build-stage

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装项目依赖
RUN npm install

# 复制项目文件
COPY . .

# 构建应用
RUN npm run build

# 第二阶段：部署项目
FROM nginx:stable-alpine as production-stage

# 将构建产物从构建阶段复制到当前阶段的工作目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制 Nginx 配置文件
COPY default.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# 使用 Nginx 启动容器
CMD ["nginx", "-g", "daemon off;"]


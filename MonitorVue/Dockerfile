# 使用官方的 Node.js 镜像作为基础镜像
FROM node:latest

# 设置工作目录
WORKDIR /app

# 复制项目文件到镜像中
COPY . .

# 安装项目依赖
RUN npm install

# 构建项目
RUN npm run build

# 暴露应用程序运行时的端口
EXPOSE 5000

# 启动应用程序
CMD ["npm", "run", "serve"]

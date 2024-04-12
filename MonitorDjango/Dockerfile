# 使用Python官方镜像作为基础镜像
FROM python:3.8

# 设置环境变量，确保Python输出直接打印到控制台，不被缓存
ENV PYTHONUNBUFFERED 1

# 在容器内部创建一个目录来存放你的应用
RUN mkdir /app

# 将工作目录设置为你创建的目录
WORKDIR /app

# 将你的项目代码复制到工作目录中
COPY . /app

RUN pip install --upgrade pip \
    && pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 暴露端口8000，供Django运行
EXPOSE 8000

# 运行Django服务
CMD sh -c 'python manage.py runserver 0.0.0.0:8000'

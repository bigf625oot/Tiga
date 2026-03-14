FROM python:3.11-slim

# 设置环境变量：语言、时区、无缓冲输出
ENV LANG=zh_CN.UTF-8 \
    LC_ALL=zh_CN.UTF-8 \
    TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1

# 替换为国内源 (Debian)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖和 locales
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    && echo "zh_CN.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制依赖并安装 (使用清华源)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY . .

# 编译翻译文件
RUN pybabel compile -d app/locales

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

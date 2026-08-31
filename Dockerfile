# 使用官方 Python 3.11-slim 镜像（Debian系列兼容 mini-racer 的预编译包）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖：ffmpeg（yt-dlp合成/转码需要）、ca证书
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖说明文件并安装 Python 包
COPY requirements.txt /app/
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt

# 专用非 root 用户
RUN addgroup --system app && adduser --system --ingroup app app
RUN mkdir -p /app/downloads /app/logs && chown -R app:app /app

# 复制项目所有代码
COPY --chown=app:app . /app/

USER app

# 开放 8051 端口
EXPOSE 8051

# 启动命令
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8051", "--timeout", "120", "app:app"]

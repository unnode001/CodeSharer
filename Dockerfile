# CodeSharer/Dockerfile

# --- 1. 使用Docker Hub官方Python基础镜像 ---
FROM python:3.10-slim

# --- 2. 设置环境变量 ---
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- 3. 设置工作目录 ---
WORKDIR /app

# --- 4. 配置pip使用国内镜像源 ---
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# --- 5. 安装依赖 ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- 6. 复制应用代码 ---
COPY ./backend /app/backend

# --- 7. 暴露端口 ---
EXPOSE 8000

# --- 8. 设置启动命令 ---
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "backend.api_server:app", "--bind", "0.0.0.0:8000"]
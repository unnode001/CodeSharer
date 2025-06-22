![image](https://github.com/user-attachments/assets/1a7530f3-e8d4-4fba-ad4e-f7440dfe8c14)# CodeSharer

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Frameworks](https://img.shields.io/badge/frameworks-PyQt6_&_FastAPI-green.svg)

**一款轻量级的桌面代码片段管理器，支持本地存储和在线分享。**

---



## 简介 (Introduction)

在日常开发、教学或技术支持中，我们经常需要记录、复用和分享代码片段。CodeSharer 旨在解决这一痛点，它提供了一个简洁、高效的桌面端解决方案，让开发者可以轻松管理本地代码库，并通过一键操作将代码分享给他人，生成一个带有时效性的链接。

## 功能亮点 (Features)

-   **本地代码管理**
    -   **创建、编辑、删除**: 完整的本地代码片段CRUD（增删改查）功能。
    -   **语法高亮**: 集成 Pygments，支持上百种编程语言的语法高亮。
    -   **本地搜索**: 支持按标题实时过滤，快速定位所需代码。
    -   **离线使用**: 所有本地代码片段均存储在本地SQLite数据库中，无需网络连接即可访问。

-   **在线分享**
    -   **一键分享**: 将选中的代码片段快速上传并生成唯一的分享链接。
    -   **有效期设置**: 分享时可自定义链接的有效期（如1天、7天、永久）。
    -   **自动复制**: 分享成功后，链接会自动复制到系统剪贴板，方便快捷。

## 技术栈 (Tech Stack)

| 模块         | 技术/库                                   | 用途                             |
| ------------ | ----------------------------------------- | -------------------------------- |
| **桌面客户端** | **Python 3.10+**                          | 主要编程语言                     |
|              | **PyQt6**                                 | 构建跨平台的图形用户界面 (GUI)   |
|              | **Pygments**                              | 语法高亮引擎                     |
|              | **requests**                              | 与后端API进行HTTP通信            |
|              | **pyperclip**                             | 跨平台剪贴板操作                 |
|              | **SQLite**                                | 存储本地代码片段                 |
| **后端服务**   | **FastAPI**                               | 构建高性能、现代化的RESTful API  |
|              | **Uvicorn + Gunicorn**                    | 生产级ASGI服务器                 |
|              | **PostgreSQL**                            | 生产环境下的后端数据库           |
| **部署**     | **Docker & Docker Compose**               | 容器化部署后端服务和数据库       |
|              | **PyInstaller**                           | 将客户端打包为独立可执行文件     |

## 项目结构 (Project Structure)

```
CodeSharer/
├── backend/
│   ├── __init__.py
│   └── api_server.py        # FastAPI后端服务代码
├── database/
│   ├── __init__.py
│   └── db_handler.py        # 客户端本地数据库处理器
├── widgets/
│   ├── __init__.py
│   └── syntax_highlighter.py # 语法高亮器组件
├── assets/
│   └── app.ico              # 应用图标
├── .env                     # 环境变量 (数据库密码等)
├── docker-compose.yml       # Docker编排文件
├── Dockerfile               # 后端服务的Dockerfile
├── main.py                  # 客户端应用主入口
├── requirements.txt         # Python依赖列表
└── README.md                # 项目说明文件
```

## 本地开发环境设置 (Local Development Setup)

1.  **克隆仓库**
    ```bash
    git clone https://github.com/your-username/CodeSharer.git
    cd CodeSharer
    ```

2.  **创建并激活虚拟环境 (Windows CMD)**
    ```cmd
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **安装所有依赖**
    ```cmd
    pip install -r requirements.txt
    ```

4.  **配置环境变量**
    复制 `.env.example` (如果提供) 或手动创建 `.env` 文件，并根据需要填写数据库配置。对于默认的 `docker-compose` 设置，您无需修改。

## 运行应用 (Running the Application)

您需要同时运行后端和前端。

#### 1. 启动后端服务 (使用 Docker)

确保您的机器上已安装 Docker 和 Docker Compose。

```bash
# 在项目根目录下，构建并启动后端API和数据库容器
docker-compose up --build -d
```

后端服务将在 `http://127.0.0.1:8000` 上运行。您可以访问 `http://127.0.0.1:8000/docs` 查看交互式API文档。

#### 2. 启动客户端应用

打开一个 **新的** 终端窗口，激活虚拟环境，然后运行：

```cmd
# 激活虚拟环境
.\venv\Scripts\activate

# 运行PyQt6客户端
python main.py
```

现在，您应该可以看到应用程序的GUI界面，并且可以正常使用所有功能，包括在线分享。

## 打包与部署 (Packaging & Deployment)

### 客户端打包

使用 PyInstaller 将客户端打包成单个可执行文件。

```cmd
# 确保已激活虚拟环境并安装了 pyinstaller
pip install pyinstaller

# 运行打包命令
pyinstaller --name CodeSharer --onefile --windowed --icon=assets/app.ico main.py
```
生成的可执行文件位于 `dist/` 目录下。

### 后端部署

后端服务已完全容器化，可以直接使用 `docker-compose.yml` 部署在任何支持 Docker 的服务器上。只需将项目文件上传到服务器，并运行 `docker-compose up -d` 即可。

为获得最佳性能和安全性，建议在生产服务器上使用 Nginx 作为反向代理，并配置HTTPS。详细步骤请参考 `部署文档.md`。

## 许可 (License)

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 授权。

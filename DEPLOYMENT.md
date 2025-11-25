# 涡旋压缩机 COP 计算器 - 部署指南

本指南将教您如何让您的 COP 计算器在手机上也能使用。

---

## 方案一：局域网测试（最简单，无需部署）

如果您只想在这个办公室或家里，用连接了同一个 WiFi 的手机访问，使用此方法。

### 步骤：
1.  **确保防火墙允许**：运行程序时，Windows 可能弹出防火墙提示，请勾选“允许访问专用网络”和“公用网络”。
2.  **获取电脑 IP 地址**：
    -   打开 PowerShell 或 CMD。
    -   输入 `ipconfig` 并回车。
    -   找到 **IPv4 地址**，例如 `192.168.1.5`。
3.  **运行程序**：
    -   在 VS Code 中运行 `app.py`。
    -   终端会显示 `Running on http://0.0.0.0:5001`。
4.  **手机访问**：
    -   确保手机连接了和电脑同一个 WiFi。
    -   打开手机浏览器。
    -   输入地址：`http://[电脑IP]:5001`，例如 `http://192.168.1.5:5001`。

---

## 方案二：使用 Render 部署（推荐，支持 HTTPS，自动化）

您提到的 Render 是一个非常现代且流行的云平台，非常适合部署 Flask 应用。它有免费套餐（Free Tier），支持自动从 GitHub 拉取代码。

### 1-A. 如何上传代码到 GitHub (网页版 - 适合初学者)

如果您不熟悉命令行工具，可以直接通过浏览器操作：

1.  **注册/登录**：访问 [github.com](https://github.com) 并登录。
2.  **创建仓库**：点击右上角的 **"+"** -> **"New repository"**。
    -   Repository name: 填一个名字，例如 `cop-cal-tool`。
    -   Public/Private: 选 **Public** (Render 免费版通常需要 Public 仓库)。
    -   点击 **"Create repository"**。
3.  **上传文件**：
    -   在创建好的仓库页面，点击 **"uploading an existing file"** 链接。
    -   将您电脑上项目文件夹里的文件拖进去：
        -   `app.py`
        -   `cop_cal.py`
        -   `requirements.txt`
        -   `templates/` 文件夹（或者先创建一个 templates 文件夹再上传 `index.html`，如果在网页不好操作文件夹，可以只上传文件）。
        -   *注意：如果网页版不支持拖拽文件夹，请先确保根目录有 requirements.txt, app.py 等核心文件。templates 目录如果难以上传，请确保代码结构正确。*
    -   点击底部的 **"Commit changes"**。

### 1-B. 如何上传代码到 GitHub (命令行版 - 推荐)
如果您电脑上安装了 Git，且您习惯使用 VS Code：
1.  在 VS Code 中打开终端。
2.  初始化 Git：`git init`
3.  添加文件：`git add .`
4.  提交更改：`git commit -m "Initial commit"`
5.  关联远程仓库（请先在 GitHub 创建一个空仓库，然后复制它的 URL）：
    `git remote add origin https://github.com/您的用户名/cop-cal-tool.git`
6.  推送代码：`git push -u origin master` (或 main)

---

### 2. 在 Render 上进行部署

1.  **登录 Render**：访问 [dashboard.render.com](https://dashboard.render.com/)，用 GitHub 账号登录。
2.  **新建服务**：点击 **"New +"** -> **"Web Service"**。
3.  **连接仓库**：找到您刚才上传的 `cop-cal-tool`，点击 **"Connect"**。
4.  **配置参数**：
    -   **Name**: `cop-calculator`
    -   **Runtime**: **Python 3**
    -   **Build Command**: `pip install -r requirements.txt`
    -   **Start Command**: `gunicorn app:app`
    -   **Instance Type**: Free
5.  **部署**：点击 **"Create Web Service"**，等待几分钟即可。

---

## 方案三：使用 PythonAnywhere（备选）

如果您不想用 GitHub，PythonAnywhere 支持直接在网页上传文件。具体步骤见上文历史版本，或直接在 PythonAnywhere 后台 Upload File 即可，非常直观。

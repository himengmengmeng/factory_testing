# Factory Testing Tool — Client End

A Django-based web client for the Instavision ODM factory testing platform. It provides a dark-themed UI for managing seller accounts, viewing product variants, and binding/updating floating Device IDs (DIDs) to product variants via the Instavision backend API.

---

## Features

### Authentication
- Seller login with email/password via JWT tokens
- Automatic token refresh with session lifecycle management
- Environment switching (Production / Staging)

### Sellers & Products Dashboard
- View primary seller's product variants (name, variant ID, OEM model ID, OEM model name)
- View all sub-sellers and their product variants
- One-click copy for variant IDs and OEM model IDs

### DID Binding Operations
- **Single DID**: Query a DID's current status, then auto-detect and perform assign or update
- **Batch CSV**: Upload a CSV file (`Device Id`, `Access Key`) to process multiple DIDs
  - Real-time progress bar and operation log
  - Pause / Resume controls
  - Retry mechanism for failed items
  - Export outcome as CSV
- Supports both primary seller and sub-seller operations
- Navigation guard warns before leaving during an active batch

### UI / UX
- Dark theme with frosted glass sidebar and top navigation
- Tailwind CSS via CDN
- Searchable variant picker
- Responsive layout

---

## Project Structure

```
factory_testing/
├── manage.py
├── requirements.txt
├── root_directory/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── token_based_factory_tool/  # Main app
    ├── views.py             # Backend logic & API proxy
    ├── urls.py              # URL routing
    └── templates/token_based_factory_tool/
        ├── base.html        # Base template (Tailwind config, global styles)
        ├── _sidebar.html    # Sidebar navigation partial
        ├── _topbar.html     # Top navigation bar partial
        ├── login.html       # Login page
        ├── dashboard.html   # Sellers & Products page
        └── operations.html  # DID binding operations page
```

## Quick Start

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install django requests PyJWT

# 3. Run migrations (session table)
python manage.py migrate

# 4. Start dev server
python manage.py runserver 9000
```

Open http://localhost:9000/factory-tool/login/ and sign in with your seller account.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/factory-tool/login/` | Login page |
| GET | `/factory-tool/logout/` | Logout and clear session |
| GET | `/factory-tool/dashboard/` | Sellers & Products page |
| GET | `/factory-tool/operations/` | DID operations page |
| GET | `/factory-tool/api/variants/` | Fetch primary seller variants |
| GET | `/factory-tool/api/sub-sellers/` | Fetch sub-sellers list |
| GET | `/factory-tool/api/sub-sellers/<id>/variants/` | Fetch sub-seller variants |
| GET | `/factory-tool/api/query-did/?device_id=<did>` | Query DID status |
| POST | `/factory-tool/api/bind-did/` | Assign or update a single DID |
| POST | `/factory-tool/api/batch-bind/` | Server-side batch processing |

## CSV Format

```csv
Device Id,Access Key
ABC123,key123
DEF456,key456
```

---

# Factory Testing Tool — 客户端

基于 Django 的 Instavision ODM 产测平台 Web 客户端。提供暗黑主题 UI，用于管理 Seller 账号、查看产品 Variant、以及将浮动设备 ID（DID）绑定/更新到产品 Variant。

---

## 功能特性

### 认证登录
- 使用邮箱/密码通过 JWT Token 登录
- 自动刷新 Token，完整的会话生命周期管理
- 支持切换环境（生产环境 / 测试环境）

### Seller 与产品信息展示
- 查看一级 Seller 的产品 Variant（名称、Variant ID、OEM 机型 ID、OEM 机型名称）
- 查看所有二级 Seller 及其产品 Variant
- 一键复制 Variant ID 和 OEM 机型 ID

### DID 绑定操作
- **单个 DID 操作**：查询 DID 当前状态，自动检测并执行 assign（绑定）或 update（更新）
- **批量 CSV 上传**：上传 CSV 文件（`Device Id`、`Access Key` 两列）批量处理
  - 实时进度条与操作日志
  - 暂停 / 继续控制
  - 失败项重试机制
  - 导出处理结果为 CSV
- 支持一级 Seller 和二级 Seller 操作
- 批量处理期间离开页面会弹出确认提示

### UI / 用户体验
- 暗黑主题，侧边栏和顶部导航采用毛玻璃效果
- 通过 CDN 引入 Tailwind CSS
- 可搜索的 Variant 选择器
- 响应式布局

---

## 项目结构

```
factory_testing/
├── manage.py
├── requirements.txt
├── root_directory/            # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── token_based_factory_tool/  # 主应用
    ├── views.py               # 后端逻辑 & API 代理
    ├── urls.py                # URL 路由
    └── templates/token_based_factory_tool/
        ├── base.html          # 基础模板（Tailwind 配置、全局样式）
        ├── _sidebar.html      # 侧边栏导航组件
        ├── _topbar.html       # 顶部导航栏组件
        ├── login.html         # 登录页
        ├── dashboard.html     # Seller 与产品信息页
        └── operations.html    # DID 绑定操作页
```

## 快速开始

```bash
# 1. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install django requests PyJWT

# 3. 执行数据库迁移（session 表）
python manage.py migrate

# 4. 启动开发服务器
python manage.py runserver 9000
```

打开 http://localhost:9000/factory-tool/login/ 使用 Seller 账号登录。

## CSV 格式

```csv
Device Id,Access Key
ABC123,key123
DEF456,key456
```

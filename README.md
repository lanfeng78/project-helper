<div align="center">

# 📖 Project Helper · 项目学习助手

**AI 驱动的开源项目源码分析工具 — 输入 GitHub 链接，秒懂任何项目**

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D)
![DeepSeek](https://img.shields.io/badge/DeepSeek-V4-4F46E5)
![LangChain](https://img.shields.io/badge/LangChain-0.3-important)

</div>

---

## ✨ 功能

- **一键分析** — 粘贴 GitHub 仓库地址，自动获取源码并生成完整分析报告
- **零克隆** — 通过 GitHub REST API 直接读取源码，无需 git clone，秒级响应
- **AI 报告** — 项目概述、技术栈、目录结构、核心模块、数据流、设计模式、阅读建议，13 个维度
- **交互问答** — 对源码任意提问，AI 自主查找代码回答，流式打字机输出
- **实时进度** — SSE 实时推送分析进度，自动缓存已分析项目

## 🛠 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12 + FastAPI + LangChain + SQLite |
| AI | DeepSeek V4 (`deepseek-v4-flash`) |
| 前端 | Vue 3 + Vite + Pinia + marked + highlight.js |
| 源码获取 | GitHub REST API（优先）/ git clone（降级） |

## 🚀 快速开始

### 1. 克隆

```bash
git clone https://github.com/yourname/project-helper
cd project-helper
```

### 2. 后端

```bash
cd backend
pip install -r requirements.txt

# 确保 Python 3.12+
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

> 后端启动在 `http://localhost:8000`。  
> API Key 已在 `config.py` 中预配置 DeepSeek API。如需更换，修改 `deepseek_api_key` 和 `deepseek_model` 字段。

### 3. 前端

```bash
cd frontend
npm install
npx vite --host 0.0.0.0 --port 3000
```

> 前端启动在 `http://localhost:3000`，自动代理 `/api` 请求到后端。

### 4. 打开浏览器

访问 [http://localhost:3000](http://localhost:3000)

## 📸 截图

```
┌──────────────────────────────────────────────────────┐
│  🔗 https://github.com/facebook/react          [分析] │
├──────────────────────────────────────────────────────┤
│                                                      │
│  📊 完整分析报告           💬 交互问答              │
│  ┌────────────────┐      ┌────────────────┐          │
│  │ 项目概述       │      │ 这个项目的核   │          │
│  │ 技术栈         │      │ 心数据结构是   │          │
│  │ 目录结构       │      │ 什么？         │          │
│  │ 核心模块       │      │               │          │
│  │ 数据流         │      │ 项目使用了JS  │          │
│  │ 设计模式       │      │ 原型链...      │          │
│  └────────────────┘      └────────────────┘          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
project-helper/
├── backend/
│   ├── main.py              # FastAPI 路由 + SSE 进度
│   ├── config.py            # 配置（API Key, 模型）
│   ├── models.py            # SQLite + Project ORM
│   ├── github_api.py        # GitHub REST API 客户端
│   ├── repo_manager.py      # 源码获取（API 优先/Clone 降级）
│   ├── analyzer.py          # AI 报告生成（LangChain + DeepSeek）
│   ├── qa_engine.py         # 流式问答引擎
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/           # 4 个页面
│   │   ├── components/      # 可复用组件
│   │   ├── api/             # API 封装
│   │   ├── router/          # 路由
│   │   └── stores/          # 状态管理
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```

## 🧠 分析流程

```
用户输入 GitHub URL
    ↓
GitHub REST API
├─ GET /repos/{owner}/{repo}          → 仓库元数据
├─ GET /git/trees/{sha}?recursive=1   → 目录树
└─ GET /contents/{path}               → 文件内容
    ↓
LangChain + DeepSeek V4
├─ 分析项目结构、数据流、设计模式
└─ 生成 13 维度分析报告
    ↓
用户查看报告 / 交互问答（流式输出）
```

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analyze` | 提交 GitHub URL 开始分析 |
| GET | `/api/progress/{id}` | SSE 实时进度 |
| GET | `/api/report/{id}` | 获取分析报告 |
| GET | `/api/projects` | 列出已缓存项目 |
| DELETE | `/api/projects/{id}` | 删除缓存项目 |
| POST | `/api/qa` | 流式交互问答 |

## ⚙️ 配置

`backend/config.py`:

```python
deepseek_api_key: str = "sk-xxx"           # DeepSeek API Key
deepseek_base_url: str = "https://api.deepseek.com"
deepseek_model: str = "deepseek-v4-flash"   # 2026 最新模型
max_file_size: int = 200 * 1024             # 单文件上限 200KB
max_total_size: int = 5 * 1024 * 1024       # 总内容上限 5MB
```

## 🎨 设计

- 赛博霓虹暗色主题（`#030712` 背景 + `#00e5ff` 青 + `#e040fb` 紫）
- Glassmorphism 毛玻璃卡片 + 渐变发光边框
- Bento Grid 非对称布局
- `prefers-reduced-motion` 无障碍支持
- 响应式移动端适配

---

<div align="center">
Made with ❤️ by Project Helper
</div>

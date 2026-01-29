<p align="center">
  <img src="logo.png" alt="Relio Logo" width="128" height="128">
</p>

<h1 align="center">Relio</h1>

<p align="center">
  <strong>Relationship Intelligence Orchestrator</strong>
</p>

<p align="center">
  <em>智能关系管理与对话决策辅助系统</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-macOS-blue?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.10+-green?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Version-1.0.0-purple?style=flat-square" alt="Version">
</p>

---

## ✨ 简介

**Relio** 是一款基于用户画像与关系状态的智能对话决策辅助系统。通过分析用户的社交关系网络和历史交互行为，Relio 为每位联系人建立个性化的用户画像，动态追踪关系演化，并提供符合用户表达习惯和社交语境的个性化回复建议。

> 💡 **设计理念**：Relio 是决策辅助工具，而非自动化聊天机器人。它尊重用户的自主性，提供多样化建议供用户选择，而非替代用户进行对话。

## 🎯 核心功能

### 用户画像管理
为每位联系人建立独立的对话风格配置：
- **风格参数** - 正式程度、主动性、情绪表达、幽默倾向、冗长程度
- **联系人类型** - 好友、家人、同事、陌生人等
- **个性化描述** - 自定义备注和标签

### 关系状态追踪
动态监测与每位联系人的关系演化：
- **关系阶段** - 初识 → 建立 → 稳定 → 亲密（或疏远）
- **亲密度曲线** - 可视化展示关系变化趋势
- **互动频率** - 自动统计交流频率

### 智能对话分析
深度理解对话内容：
- **意图识别** - 问候、提问、请求、投诉等
- **情感分析** - 正面/中性/负面情绪检测
- **关键词提取** - 核心话题识别

### 个性化回复建议
基于多维度信息生成回复：
- **主建议** - 最匹配当前语境的回复
- **替代方案** - 多种风格的备选回复
- **策略说明** - 解释为何推荐该回复

### 自适应学习
根据用户反馈持续优化：
- **反馈机制** - 点赞/踩评价回复质量
- **参数调整** - 自动优化用户画像参数
- **长期记忆** - 记录重要交互信息

## 📦 安装

### 方式一：使用预构建应用（推荐）

1. 下载 `Relio.app`
2. 将其拖拽到「应用程序」文件夹
3. 双击运行

### 方式二：从源码运行

#### 环境要求

- **操作系统**: macOS 10.15+（推荐）/ Linux / Windows
- **Python**: 3.10 或更高版本
- **依赖管理**: pip 或 conda

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/relio.git
cd relio

# 2. 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API 密钥
cp config/.env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 5. 运行应用
python main.py
```

### 方式三：自行构建 macOS 应用

```bash
# 确保已安装依赖
pip install -r requirements.txt

# 运行打包脚本
chmod +x build_app.sh
./build_app.sh
```

构建完成后，`Relio.app` 将出现在项目根目录。

## ⚙️ 配置

### API 配置

复制 `config/.env.example` 为 `.env`，并填写配置：

```env
# LLM API 配置（必填）
SILICONFLOW_API_KEY=sk-your-api-key-here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-R1-0528-Qwen3-8B

# 数据存储目录
DATA_DIR=data

# 模型参数（可选）
LLM_TEMPERATURE=0.7
LLM_TOP_P=0.7
LLM_FREQUENCY_PENALTY=0.5
LLM_MAX_HISTORY=6
LLM_MAX_TOKENS=512
```

### 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `SILICONFLOW_API_KEY` | API 密钥 | **必填** |
| `SILICONFLOW_BASE_URL` | API 地址 | https://api.siliconflow.cn/v1 |
| `SILICONFLOW_MODEL` | 模型名称 | deepseek-ai/DeepSeek-R1-0528-Qwen3-8B |
| `LLM_TEMPERATURE` | 生成随机性 (0-1) | 0.7 |
| `LLM_MAX_TOKENS` | 最大输出长度 | 512 |
| `DATA_DIR` | 数据存储目录 | data |

## 🖥️ 使用指南

### 基本工作流

```
1. 添加联系人
   ↓
2. 输入收到的消息
   ↓
3. Relio 分析消息并生成回复建议
   ↓
4. 选择或编辑建议后发送
   ↓
5. 对建议进行反馈（点赞/踩）
   ↓
6. Relio 学习并优化
```

### 主要界面

- **联系人列表** - 左侧显示所有联系人及亲密度
- **对话区域** - 中间显示对话历史和回复建议
- **用户画像** - 右侧展示当前联系人的详细信息和亲密度曲线

### 快捷操作

- **添加联系人** - 点击左上角「+」按钮
- **生成回复** - 输入消息后点击「生成建议」
- **反馈** - 对 AI 回复点击 👍 或 👎

## 📁 项目结构

```
relio/
├── main.py                 # 应用入口
├── requirements.txt        # Python 依赖
├── build_app.sh            # macOS 应用打包脚本
├── Relio.spec              # PyInstaller 配置
├── logo.png                # 应用图标源文件
├── README.md               # 项目文档
├── LICENSE                 # 开源许可证
│
├── config/
│   └── .env.example        # 环境变量示例
│
├── core/                   # 核心业务逻辑
│   ├── config.py           # 配置管理
│   ├── system.py           # 系统核心引擎
│   ├── user_profile.py     # 用户画像管理
│   ├── relationship_state.py # 关系状态管理
│   ├── conversation_analyzer.py # 对话分析
│   ├── reply_decision.py   # 回复决策引擎
│   ├── llm_client.py       # LLM API 客户端
│   ├── storage.py          # 数据持久化
│   ├── history_store.py    # 对话历史存储
│   ├── intimacy_manager.py # 亲密度管理
│   └── memory_extractor.py # 长期记忆提取
│
├── ui/                     # 用户界面
│   ├── main_window.py      # 主窗口
│   ├── dialogs.py          # 对话框
│   ├── settings_dialogs.py # 设置对话框
│   ├── theme_manager.py    # 主题管理
│   ├── button_styles.py    # 按钮样式
│   └── store.py            # UI 状态管理
│
├── assets/                 # 静态资源
│   └── *.svg               # 图标文件
│
├── data/                   # 数据存储
│   ├── profiles.json       # 用户画像数据
│   ├── relationship_states.json # 关系状态数据
│   ├── long_term_memories.json # 长期记忆
│   └── user_settings.json  # 用户设置
│
└── vendor/                 # 第三方库
    └── itchat_uos/         # 微信接口（可选）
```

## 🔒 隐私与安全

- **本地存储** - 所有用户数据存储在本地 `data/` 目录
- **无云端同步** - 不会上传任何数据到云端
- **API 安全** - 仅向 LLM API 发送必要的对话内容
- **开源透明** - 代码完全开源，可审计

## 🛠️ 开发

### 技术栈

- **语言**: Python 3.10+
- **GUI 框架**: PySide6 (Qt for Python)
- **图表**: Matplotlib
- **LLM**: OpenAI API 兼容接口
- **打包**: PyInstaller

### 本地开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行应用
python main.py

# 构建 macOS 应用
./build_app.sh
```

## 📋 更新日志

### v1.0.0 (2026-01-30)
- 🎉 首次发布
- ✨ 用户画像管理
- ✨ 关系状态追踪
- ✨ 智能回复建议
- ✨ 亲密度可视化
- ✨ macOS 原生应用支持

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题或建议，请通过 GitHub Issues 联系。

---

<p align="center">
  Made with ❤️ by ssheep
</p>

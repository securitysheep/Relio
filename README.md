<p align="center">
  <img src="logo.png" alt="Relio Logo" width="128" height="128">
</p>

<h1 align="center">Relio</h1>

<p align="center">
  <strong>Relationship Intelligence Orchestrator</strong>
</p>

<p align="center">
  <em>全名：一种基于用户画像与关系状态的对话回复决策系统</em>
</p>

---

## 简介

**Relio** 是一款面向关系沟通场景的桌面应用。它通过联系人画像、关系状态、对话上下文和长期记忆，生成可参考的回复建议，并支持基于反馈持续优化。

> Relio 是“回复决策辅助工具”，不是自动代聊机器人。

## 核心能力

- 联系人管理：关系类型、目标、风格标签、备注与头像管理
- 回复建议：结合当前消息与关系状态生成主建议和备选建议
- 关系画像：亲密度、阶段变化、趋势可视化
- 长期记忆：对象特征、关系事件、沟通策略三类记忆
- 反馈学习：通过 👍/👎 反馈影响亲密度与策略有效性
- 本地存储：关系数据与配置存储在本地目录

## 运行环境

- Python：**3.10+**（推荐 3.11）
- 操作系统：
  - 源码运行：macOS / Linux / Windows
  - 打包脚本 `build_app.sh`：**macOS**（依赖 `sips`、`iconutil`）

## 从源码运行（推荐）

```bash
# 1) 进入项目目录
cd 一种基于用户画像与关系状态的对话回复决策系统

# 2) 创建并激活虚拟环境（可选但推荐）
python3 -m venv .venv
source .venv/bin/activate

# 3) 安装依赖
pip install -r requirements.txt

# 4) 准备配置文件
cp config/.env.example .env

# 5) 启动
python main.py
```

## 配置说明

默认读取项目根目录的 `.env`（`python-dotenv` 自动加载）：

```env
SILICONFLOW_API_KEY=你的密钥
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-R1-0528-Qwen3-8B

DATA_DIR=data

LLM_TEMPERATURE=0.7
LLM_TOP_P=0.7
LLM_FREQUENCY_PENALTY=0.5
LLM_MAX_HISTORY=6
LLM_MAX_TOKENS=512
```

说明：

- 建议你始终在 `.env` 中配置自己的 `SILICONFLOW_API_KEY`
- `DATA_DIR` 不配置时：
  - 开发模式默认使用项目内 `data/`
  - macOS 打包应用默认使用 `~/Library/Application Support/Relio/`

## 打包 macOS 应用

```bash
chmod +x build_app.sh
./build_app.sh
```

打包完成后：

- 产物位于项目根目录：`Relio.app`
- 可直接双击运行，或拖入“应用程序”目录

## 项目结构（当前）

```text
.
├── main.py
├── requirements.txt
├── build_app.sh
├── Relio.spec
├── README.md
├── 使用手册.md
├── config/
│   └── .env.example
├── core/
├── ui/
├── assets/
└── data/
```

## 常见问题

- 启动时报 API 或初始化失败：
  - 检查 `.env` 是否存在且 `SILICONFLOW_API_KEY` 有效
- 打包失败：
  - 先执行 `pip install -r requirements.txt`
  - 确认在 macOS 环境执行 `build_app.sh`
- 看不到历史数据：
  - 开发模式看项目内 `data/`
  - 打包应用看 `~/Library/Application Support/Relio/`

## 隐私说明

- 关系数据与配置保存在本地
- 仅在生成建议时向你配置的模型接口发送必要文本

## 许可证

本项目采用 [MIT License](LICENSE)。

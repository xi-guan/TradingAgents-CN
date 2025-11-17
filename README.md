# TradingAgents 中文增强版

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-cn--0.1.15-green.svg)](./VERSION)

面向中文用户的多智能体与大模型股票分析学习平台。帮助你系统化学习如何使用多智能体交易框架与 AI 大模型进行合规的股票研究与策略实验。

> 基于 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 项目开发

## 核心特性

### 技术架构
- 后端：FastAPI + Uvicorn
- 前端：Vue 3 + Vite + Element Plus
- 数据库：MongoDB + Redis
- 部署：Docker 多架构支持（amd64 + arm64）

### 主要功能
- 用户权限管理和角色系统
- 可视化配置管理中心
- 多级缓存系统（MongoDB/Redis/文件）
- 实时通知（SSE + WebSocket）
- 批量分析和智能股票筛选
- 自选股管理和个股详情页
- 模拟交易系统
- 专业报告导出（Markdown/Word/PDF）
- 多LLM提供商支持（OpenRouter、DeepSeek、Google AI、阿里百炼）

### 数据支持
- A股：Tushare、AkShare、BaoStock
- 美股、港股：Yahoo Finance
- 实时新闻聚合与分析

## 快速开始

### Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/hsliuping/TradingAgents-CN.git
cd TradingAgents-CN

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加 API 密钥

# 启动服务
docker-compose up -d

# 访问应用
# http://localhost:8501
```

### 本地安装

```bash
# 创建虚拟环境
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动应用
python -m streamlit run web/app.py
```

### 配置 API 密钥

在 `.env` 文件中配置以下密钥（选择其一）：

```bash
# LLM API（必选其一）
DEEPSEEK_API_KEY=sk-your-key-here
# DASHSCOPE_API_KEY=your-key-here
# OPENAI_API_KEY=sk-your-key-here

# 数据源（可选）
TUSHARE_TOKEN=your-token-here

# 数据库（可选）
MONGODB_ENABLED=false
REDIS_ENABLED=false
```

## 文档

完整文档请访问 [docs/](./docs/) 目录：

- [快速开始](./docs/QUICK_START.md) - 5分钟快速上手
- [安装指南](./docs/guides/docker-deployment-guide.md) - Docker 部署详细指南
- [配置说明](./docs/configuration/config-guide.md) - 配置文件详解
- [使用指南](./docs/usage/web-interface-guide.md) - Web 界面使用说明
- [API 文档](./docs/api/) - API 参考文档
- [更新日志](./docs/releases/CHANGELOG.md) - 版本历史

## 贡献

欢迎各种形式的贡献：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

详见 [贡献者名单](./docs/CONTRIBUTORS.md)

## 许可证

本项目采用混合许可证模式：

- **开源部分**（Apache 2.0）：`tradingagents/`、`web/`、`cli/`、`scripts/`、`docs/`
- **专有部分**（需商业授权）：`app/`（FastAPI 后端）、`frontend/`（Vue 前端）

详见 [LICENSE](./LICENSE) 和 [许可证说明](./docs/legal/LICENSING.md)

商业授权请联系：hsliup@163.com

## 联系方式

- GitHub Issues：[提交问题](https://github.com/hsliuping/TradingAgents-CN/issues)
- 邮箱：hsliup@163.com
- QQ群：187537480
- 微信公众号：TradingAgents-CN

<img src="assets/wexin.png" alt="微信公众号" width="200"/>

## 风险提示

本框架仅用于研究和教育目的，不构成投资建议。

- 交易表现可能因多种因素而异
- AI 模型的预测存在不确定性
- 投资有风险，决策需谨慎
- 建议咨询专业财务顾问

---

**如果这个项目对您有帮助，请给我们一个 Star！**

[⭐ Star](https://github.com/hsliuping/TradingAgents-CN) | [Fork](https://github.com/hsliuping/TradingAgents-CN/fork) | [文档](./docs/)

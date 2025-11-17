# TradingAgents 中文增强版

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-cn--0.1.15-green.svg)](./VERSION)

面向中文用户的**多智能体与大模型股票分析学习平台**。基于 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 开发，提供系统化的股票研究与策略实验环境。

> **定位说明**: 本平台专注于学习与研究，不提供实盘交易指令。

---

## 快速开始

### 部署方式

| 方式 | 适用场景 | 难度 | 文档 |
|------|---------|------|------|
| **绿色版** | Windows 快速体验 | ★☆☆ | [安装指南](https://mp.weixin.qq.com/s/eoo_HeIGxaQZVT76LBbRJQ) |
| **Docker** | 生产环境/跨平台 | ★★☆ | [部署指南](https://mp.weixin.qq.com/s/JkA0cOu8xJnoY_3LC5oXNw) |
| **源码版** | 开发者/定制需求 | ★★★ | [安装指南](https://mp.weixin.qq.com/s/cqUGf-sAzcBV19gdI4sYfA) |

### 核心功能

**v1.0.0-preview 新特性**

▸ **技术架构**: FastAPI + Vue 3 + MongoDB/Redis
▸ **企业功能**: 用户权限 · 配置中心 · 缓存管理 · 实时通知
▸ **分析增强**: 批量分析 · 智能筛选 · 自选股管理 · 模拟交易
▸ **数据修复**: 技术指标 · 基本面数据 · 死循环问题
▸ **多平台**: Docker 多架构支持 (x86_64/ARM64)

**中文增强特色**

▸ 智能新闻分析 · 多层次过滤 · 质量评估
▸ 多 LLM 提供商 · 模型选择持久化
▸ 完整 A股支持 · 中文本地化
▸ 专业报告导出 · 统一日志管理

---

## 使用指南

详细文档请查看：

→ [使用指南](https://mp.weixin.qq.com/s/ppsYiBncynxlsfKFG8uEbw)
→ [Docker 部署](https://mp.weixin.qq.com/s/JkA0cOu8xJnoY_3LC5oXNw)
→ [绿色版安装](https://mp.weixin.qq.com/s/eoo_HeIGxaQZVT76LBbRJQ)
→ [源码安装](https://mp.weixin.qq.com/s/cqUGf-sAzcBV19gdI4sYfA)
→ [完整文档](./docs/)

**重要提醒**: 在分析前请先同步股票数据，详见相关文档。

---

## 许可证

本项目采用混合许可证模式：

**开源部分** (Apache 2.0)
→ 适用范围: 除 `app/` 和 `frontend/` 外的所有文件
→ 权限: ✓ 商业使用 · ✓ 修改分发 · ✓ 私人使用 · ✓ 专利使用
→ 条件: 保留版权声明 · 包含许可证副本

**专有部分** (需商业授权)
→ 适用范围: `app/` (FastAPI后端) 和 `frontend/` (Vue前端)
→ 商业使用需要单独许可协议
→ 联系授权: hsliup@163.com

详见: [许可证文档](./docs/license/)

---

## 贡献

欢迎各种形式的贡献:

▸ Bug 修复 · 新功能开发
▸ 文档改进 · 本地化翻译
▸ 代码优化 · 性能提升

**贡献流程**:

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

查看贡献者: [贡献者名单](./docs/contributors.md)

---

## 致谢

**感谢源项目**

向 [Tauric Research](https://github.com/TauricResearch) 团队致敬，感谢他们创造的革命性多智能体交易框架。

**感谢社区**

感谢所有为本项目贡献代码、文档、建议和反馈的开发者和用户。

详见: [致谢文档](./docs/acknowledgments.md)

---

## 联系方式

→ **GitHub Issues**: [提交问题和建议](https://github.com/hsliuping/TradingAgents-CN/issues)
→ **邮箱**: hsliup@163.com
→ **QQ 群**: 187537480
→ **微信公众号**: TradingAgents-CN

<img src="assets/wexin.png" alt="微信公众号" width="200"/>

---

## 风险提示

**重要声明**: 本框架仅用于研究和教育目的，不构成投资建议。

→ 交易表现可能因多种因素而异
→ AI 模型的预测存在不确定性
→ 投资有风险，决策需谨慎
→ 建议咨询专业财务顾问

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 Star！**

[★ Star](https://github.com/hsliuping/TradingAgents-CN) | [Fork](https://github.com/hsliuping/TradingAgents-CN/fork) | [文档](./docs/)

</div>

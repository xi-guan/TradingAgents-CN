# 贡献者名单

感谢所有为 TradingAgents-CN 项目做出贡献的开发者和用户！

---

## 核心贡献者

### Docker 容器化

**[@breeze303](https://github.com/breeze303)**
→ 贡献: 完整的 Docker Compose 配置和容器化部署方案
→ 影响: 大大简化了项目的部署和开发环境配置
→ 时间: 2025年

### 报告导出功能

**[@baiyuxiong](https://github.com/baiyuxiong)** (baiyuxiong@163.com)
→ 贡献: 设计并实现完整的多格式报告导出系统
→ 技术: Word、PDF、Markdown 格式支持
→ 影响: 为用户提供灵活的分析报告输出选项
→ 时间: 2025年

### AI 模型集成

**[@charliecai](https://github.com/charliecai)**
→ 贡献: 添加硅基流动(SiliconFlow) LLM 提供商支持
→ 技术: 完整的 API 集成、配置管理和用户界面支持
→ 影响: 扩展了平台的 LLM 生态，提供更多模型选择
→ 时间: 2025年

**[@yifanhere](https://github.com/yifanhere)**
→ 贡献: 修复 logging_manager.py 中的 NameError 异常
→ 技术: 添加模块级自举日志器，解决配置文件加载失败问题
→ 影响: 提升了日志系统的稳定性和可靠性
→ 时间: 2025年8月

### Bug 修复与优化

**[@YifanHere](https://github.com/YifanHere)**
→ CLI 代码质量改进 ([PR #158](https://github.com/hsliuping/TradingAgents-CN/pull/158))
  • 优化命令行界面的用户体验和错误处理
  • 提升命令行工具的稳定性和友好性
→ 关键 Bug 修复 ([PR #173](https://github.com/hsliuping/TradingAgents-CN/pull/173))
  • 发现并修复 `KeyError: 'volume'` 问题
  • 提升 Tushare 数据源的系统稳定性
  • 解决缓存数据标准化问题

**[@BG8CFB](https://github.com/BG8CFB)**
→ 修复 GLM 模型无法调用新闻分析的问题 ([PR #457](https://github.com/hsliuping/TradingAgents-CN/pull/457))
  • 修正新闻分析模块与 GLM 模型的适配问题
  • 提升新闻分析功能的可用性与稳定性
→ 时间: 2025年11月

---

## 贡献统计

| 类型 | 人数 | 主要内容 |
|------|------|---------|
| 容器化部署 | 1 | Docker 配置、部署优化 |
| 功能开发 | 1 | 报告导出系统 |
| AI 模型集成 | 3 | LLM 提供商、日志系统、千帆模型 |
| Bug 修复 | 2 | 稳定性问题、CLI 优化、GLM 修复 |
| 代码优化 | 1 | 命令行界面、用户体验 |

**总计**: 7 位贡献者 · 8 个 PR

---

## 如何成为贡献者

### 技术贡献

▸ 代码贡献: Bug 修复、新功能开发、性能优化
▸ 测试贡献: 编写测试用例、发现并报告 Bug
▸ 文档贡献: 完善文档、编写教程、翻译内容

### 非技术贡献

▸ 用户反馈: 使用体验反馈、功能需求建议
▸ 社区建设: 回答问题、帮助新用户、组织活动
▸ 推广宣传: 撰写文章、社交媒体分享、会议演讲

### 贡献流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 开发测试
4. 提交 Pull Request
5. 代码审查
6. 合并发布

---

## 联系方式

→ **GitHub Issues**: [提交问题或建议](https://github.com/hsliuping/TradingAgents-CN/issues)
→ **QQ 群**: 782124367

---

**最后更新**: 2025-11-15

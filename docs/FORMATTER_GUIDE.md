# 🎨 代码格式化指南

TradingAgents-CN 使用现代化的代码格式化工具来保持代码风格的一致性。

---

## 📦 工具选择

| 项目部分 | Formatter | Linter | 配置文件 |
|---------|-----------|--------|---------|
| **后端** (Python) | **Ruff** | **Ruff** | `pyproject.toml` |
| **前端** (TypeScript/Vue) | **Biome** | **Biome** + ESLint | `frontend/biome.json` |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 方式 1: 使用 Makefile（推荐）
make install

# 方式 2: 手动安装
# 后端
pip install -e ".[dev]"

# 前端
cd frontend && npm install
```

### 2. 格式化代码

```bash
# 格式化所有代码（后端 + 前端）
make format

# 仅格式化后端
make format-backend

# 仅格式化前端
make format-frontend
```

### 3. 检查代码格式

```bash
# 检查但不修改（用于 CI）
make format-check
```

### 4. Lint 检查

```bash
# 运行 lint 检查
make lint

# 自动修复 lint 问题
make lint-fix
```

---

## 🐍 后端 - Ruff

### 特性

- ⚡ **极快** - 用 Rust 编写，比传统工具快 10-100 倍
- 🔧 **All-in-one** - 替代 Black, isort, flake8, pylint 等工具
- 🎯 **自动修复** - 大部分问题可以自动修复

### 配置

配置文件: `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.format]
quote-style = "double"  # 双引号
indent-style = "space"  # 空格缩进
line-ending = "lf"      # LF 换行符
```

### 命令

```bash
# 格式化代码
ruff format .

# 检查格式（不修改）
ruff format --check .

# Lint 检查
ruff check .

# Lint 检查 + 自动修复
ruff check --fix .

# 一键格式化 + Lint
ruff check --fix . && ruff format .
```

### 在 VS Code 中使用

安装扩展: [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

`.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  }
}
```

---

## 🎯 前端 - Biome

### 特性

- ⚡ **极快** - 用 Rust 编写，比 Prettier + ESLint 快 10-20 倍
- 🔧 **All-in-one** - Formatter + Linter + Import Organizer
- 🎨 **兼容 Prettier** - 几乎完全兼容 Prettier 的格式化规则

### 配置

配置文件: `frontend/biome.json`

```json
{
  "formatter": {
    "indentWidth": 2,
    "lineWidth": 100,
    "lineEnding": "lf"
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "asNeeded",
      "trailingCommas": "none"
    }
  }
}
```

### 命令

```bash
cd frontend

# 格式化代码
npm run format
# 或: biome format --write .

# 检查格式（不修改）
npm run format:check
# 或: biome format .

# Lint 检查
npm run lint:biome
# 或: biome lint --write .

# 一键格式化 + Lint + Import 排序
npm run check
# 或: biome check --write .
```

### 在 VS Code 中使用

安装扩展: [Biome](https://marketplace.visualstudio.com/items?itemName=biomejs.biome)

`.vscode/settings.json`:
```json
{
  "[javascript][typescript][vue]": {
    "editor.defaultFormatter": "biomejs.biome",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "quickfix.biome": "explicit"
    }
  }
}
```

---

## 📋 Makefile 命令速查

| 命令 | 说明 |
|-----|------|
| `make help` | 显示帮助信息 |
| `make install` | 安装所有依赖 |
| `make format` | 格式化所有代码 |
| `make format-check` | 检查格式（CI用） |
| `make lint` | 运行 Lint 检查 |
| `make lint-fix` | 自动修复 Lint 问题 |
| `make test` | 运行测试 |
| `make clean` | 清理构建产物 |
| `make db-start` | 启动数据库 |
| `make dev-backend` | 启动后端开发服务器 |
| `make dev-frontend` | 启动前端开发服务器 |

---

## 🔄 从旧工具迁移

### 后端：从 Black/Flake8 迁移到 Ruff

Ruff 完全兼容 Black 的格式化规则，可以无缝替换。

**迁移步骤**:
1. ✅ 已添加 Ruff 配置到 `pyproject.toml`
2. ✅ 卸载旧工具: `pip uninstall black flake8 isort`
3. ✅ 安装 Ruff: `pip install ruff`
4. ✅ 运行格式化: `ruff format .`

### 前端：从 Prettier 迁移到 Biome

Biome 几乎完全兼容 Prettier，配置已经匹配原有的 `.prettierrc.json`。

**迁移步骤**:
1. ✅ 已添加 Biome 配置到 `frontend/biome.json`
2. ✅ 已更新 `package.json` 脚本
3. ⚠️ 可选: 卸载 Prettier
   ```bash
   cd frontend
   npm uninstall prettier @vue/eslint-config-prettier
   ```
4. ✅ 运行格式化: `npm run format`

**注意**: 如果需要保留 Prettier（比如团队成员还在使用），两者可以共存。只需在各自的 ignore 文件中互相排除即可。

---

## ⚙️ 配置对比

### 后端格式化规则

| 规则 | Ruff 配置 |
|-----|----------|
| 行宽 | 100 字符 |
| 引号 | 双引号 `"` |
| 缩进 | 4 空格 (Python 默认) |
| 换行符 | LF (`\n`) |
| 尾随逗号 | 保留 |

### 前端格式化规则

| 规则 | Biome 配置 |
|-----|----------|
| 行宽 | 100 字符 |
| 引号 | 单引号 `'` |
| 缩进 | 2 空格 |
| 换行符 | LF (`\n`) |
| 分号 | 按需 (asNeeded) |
| 尾随逗号 | 无 (none) |
| 箭头函数括号 | 按需 (asNeeded) |

---

## 🚨 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  format-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # 后端
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Ruff
        run: pip install ruff

      - name: Check backend formatting
        run: ruff format --check .

      - name: Lint backend
        run: ruff check .

      # 前端
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install frontend dependencies
        run: cd frontend && npm ci

      - name: Check frontend formatting
        run: cd frontend && npm run format:check

      - name: Lint frontend
        run: cd frontend && npm run lint:biome
```

### 使用 Makefile (推荐)

```yaml
- name: Run CI checks
  run: make ci
```

---

## 💡 最佳实践

### 1. 提交前自动格式化

安装 Git pre-commit hook:

```bash
# 创建 .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
make format
git add -u
EOF

chmod +x .git/hooks/pre-commit
```

### 2. IDE 集成

推荐在 VS Code 中启用 "Format on Save"，这样每次保存文件时自动格式化。

### 3. 团队协作

确保团队成员都安装了相同的工具和配置：

1. 运行 `make install` 安装依赖
2. 在 VS Code 中安装 Ruff 和 Biome 扩展
3. 启用 "Format on Save"

### 4. 渐进式采用

如果项目代码量很大，可以渐进式地格式化代码：

```bash
# 只格式化修改过的文件
ruff format $(git diff --name-only --diff-filter=ACMR "*.py")

# 或者按目录逐步格式化
ruff format app/
ruff format tradingagents/
```

---

## 📚 参考文档

- **Ruff**: https://docs.astral.sh/ruff/
- **Biome**: https://biomejs.dev/
- **Makefile**: https://www.gnu.org/software/make/manual/

---

## ❓ 常见问题

### Q1: Ruff 和 Black 有什么区别？

**A**: Ruff 是用 Rust 编写的，速度更快（10-100x），且功能更全（包含 linter）。格式化规则几乎完全兼容 Black。

### Q2: Biome 和 Prettier 有什么区别？

**A**: Biome 也是用 Rust 编写的，速度更快（10-20x），且包含 linter 功能。格式化规则与 Prettier 高度兼容。

### Q3: 为什么前端还保留了 ESLint？

**A**: Biome 目前对 Vue 特定规则的支持还不够完善，所以保留 ESLint 用于 Vue 组件的 lint 检查。未来 Biome 成熟后可以完全替代 ESLint。

### Q4: 如何在旧代码上运行格式化？

**A**: 建议分批进行：
```bash
# 先检查会有哪些改动
make format-check

# 确认后再格式化
make format
```

### Q5: 格式化工具会改变代码逻辑吗？

**A**: 不会。格式化工具只改变代码的外观（空格、缩进、换行等），不会改变代码的语义和逻辑。

---

**最后更新**: 2025-11-16
**维护者**: TradingAgents-CN Team

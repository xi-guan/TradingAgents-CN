#!/bin/bash

# TradingAgents-CN 配置初始化脚本
# Setup script for TradingAgents-CN configuration

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CONFIG_DIR="$PROJECT_ROOT/config"
CONFIG_FILE="$CONFIG_DIR/local.yaml"
TEMPLATE_FILE="$PROJECT_ROOT/scripts/templates/local.yaml.template"
ENV_FILE="$PROJECT_ROOT/.env"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️ ${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# 打印横幅
print_banner() {
    echo ""
    echo "============================================================"
    echo "  TradingAgents-CN 配置初始化"
    echo "  TradingAgents-CN Configuration Setup"
    echo "============================================================"
    echo ""
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 python3，请先安装 Python 3.8+"
        exit 1
    fi

    # 检查 PyYAML
    if ! python3 -c "import yaml" &> /dev/null; then
        print_warning "未安装 PyYAML，正在安装..."
        pip install pyyaml
    fi

    print_success "依赖检查完成"
}

# 创建配置目录
create_config_dir() {
    if [ ! -d "$CONFIG_DIR" ]; then
        print_info "创建配置目录: $CONFIG_DIR"
        mkdir -p "$CONFIG_DIR"
    fi
}

# 生成密钥
generate_secrets() {
    print_info "生成安全密钥..."

    # 使用Python生成密钥
    SECRETS_OUTPUT=$(python3 "$SCRIPT_DIR/utils/generate_secrets.py" | grep -E "^[A-Z_]+=")

    # 将密钥保存到临时文件
    echo "$SECRETS_OUTPUT" > /tmp/tradingagents_secrets.env

    print_success "密钥生成完成"
}

# 读取用户输入的API密钥
read_api_keys() {
    print_info "配置API密钥..."
    echo ""

    # Tushare Token
    echo -n "请输入 Tushare Token (留空跳过): "
    read TUSHARE_TOKEN
    if [ -z "$TUSHARE_TOKEN" ]; then
        TUSHARE_TOKEN=""
    fi

    # OpenAI API Key
    echo -n "请输入 OpenAI API Key (留空跳过): "
    read OPENAI_API_KEY
    if [ -z "$OPENAI_API_KEY" ]; then
        OPENAI_API_KEY=""
    fi

    # Anthropic API Key
    echo -n "请输入 Anthropic API Key (留空跳过): "
    read ANTHROPIC_API_KEY
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        ANTHROPIC_API_KEY=""
    fi

    # Google API Key
    echo -n "请输入 Google API Key (留空跳过): "
    read GOOGLE_API_KEY
    if [ -z "$GOOGLE_API_KEY" ]; then
        GOOGLE_API_KEY=""
    fi

    echo ""
    print_success "API密钥配置完成"
}

# 生成配置文件
generate_config() {
    print_info "生成配置文件: $CONFIG_FILE"

    # 检查模板文件
    if [ ! -f "$TEMPLATE_FILE" ]; then
        print_error "模板文件不存在: $TEMPLATE_FILE"
        exit 1
    fi

    # 读取生成的密钥
    source /tmp/tradingagents_secrets.env

    # 复制模板并替换占位符
    cp "$TEMPLATE_FILE" "$CONFIG_FILE"

    # 使用 sed 替换占位符
    sed -i "s|__POSTGRES_PASSWORD__|${POSTGRES_PASSWORD}|g" "$CONFIG_FILE"
    sed -i "s|__REDIS_PASSWORD__|${REDIS_PASSWORD}|g" "$CONFIG_FILE"
    sed -i "s|__JWT_SECRET__|${JWT_SECRET}|g" "$CONFIG_FILE"
    sed -i "s|__CSRF_SECRET__|${CSRF_SECRET}|g" "$CONFIG_FILE"
    sed -i "s|__QDRANT_API_KEY__|${QDRANT_API_KEY}|g" "$CONFIG_FILE"

    # 替换用户输入的API密钥
    sed -i "s|__TUSHARE_TOKEN__|${TUSHARE_TOKEN}|g" "$CONFIG_FILE"
    sed -i "s|__OPENAI_API_KEY__|${OPENAI_API_KEY}|g" "$CONFIG_FILE"
    sed -i "s|__ANTHROPIC_API_KEY__|${ANTHROPIC_API_KEY}|g" "$CONFIG_FILE"
    sed -i "s|__GOOGLE_API_KEY__|${GOOGLE_API_KEY}|g" "$CONFIG_FILE"

    # 清理临时文件
    rm -f /tmp/tradingagents_secrets.env

    print_success "配置文件生成完成: $CONFIG_FILE"
}

# 生成 .env 文件
generate_env_file() {
    print_info "生成 .env 文件..."

    python3 "$SCRIPT_DIR/utils/generate_env.py"

    print_success ".env 文件生成完成: $ENV_FILE"
}

# 显示下一步操作
show_next_steps() {
    echo ""
    echo "============================================================"
    echo "  ✅ 配置初始化完成！"
    echo "============================================================"
    echo ""
    echo "📝 生成的文件:"
    echo "   - $CONFIG_FILE (主配置文件)"
    echo "   - $ENV_FILE (环境变量文件)"
    echo ""
    echo "🚀 下一步操作:"
    echo "   1. 检查配置文件: cat $CONFIG_FILE"
    echo "   2. 启动数据库: docker-compose up -d"
    echo "   3. 安装依赖: pip install -r requirements.txt"
    echo "   4. 运行示例: python examples/database_v2_example.py"
    echo "   5. 启动后端: cd backend && uvicorn app.main:app --reload"
    echo "   6. 启动前端: cd frontend && npm run dev"
    echo ""
    echo "📚 相关文档:"
    echo "   - 数据库快速开始: docs/DATABASE_V2_QUICK_START.md"
    echo "   - 数据库迁移指南: docs/DATABASE_MIGRATION_GUIDE.md"
    echo ""
    echo "⚠️  注意事项:"
    echo "   - config/local.yaml 和 .env 已加入 .gitignore"
    echo "   - 请勿将这些文件提交到版本控制"
    echo "   - 如需重新配置，删除这些文件后重新运行 ./scripts/setup.sh"
    echo ""
    echo "============================================================"
    echo ""
}

# 主函数
main() {
    print_banner

    # 检查是否已存在配置文件
    if [ -f "$CONFIG_FILE" ]; then
        print_warning "配置文件已存在: $CONFIG_FILE"
        echo -n "是否覆盖? (y/N): "
        read CONFIRM
        if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
            print_info "取消配置，退出"
            exit 0
        fi
    fi

    # 执行配置步骤
    check_dependencies
    create_config_dir
    generate_secrets
    read_api_keys
    generate_config
    generate_env_file

    # 显示下一步
    show_next_steps
}

# 运行主函数
main

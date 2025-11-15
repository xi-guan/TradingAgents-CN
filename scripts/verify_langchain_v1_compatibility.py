#!/usr/bin/env python3
"""
LangChain 1.0 兼容性验证脚本

验证现有代码是否与 LangChain 1.0 兼容
"""

import sys
import importlib.util
from pathlib import Path

def check_package_version(package_name: str, min_version: str = "1.0.0"):
    """检查包版本"""
    try:
        module = __import__(package_name)
        version = getattr(module, "__version__", "unknown")
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: 未安装")
        return False

def check_import_compatibility():
    """检查导入兼容性"""
    print("\n🔍 检查导入兼容性...")

    imports_to_check = [
        # 核心导入
        ("langchain_core.messages", "BaseMessage"),
        ("langchain_core.prompts", "ChatPromptTemplate"),
        ("langchain_core.runnables", "RunnablePassthrough"),

        # LLM 提供商
        ("langchain_openai", "ChatOpenAI"),
        ("langchain_anthropic", "ChatAnthropic"),
        ("langchain_google_genai", "ChatGoogleGenerativeAI"),

        # LangGraph
        ("langgraph.graph", "StateGraph"),
        ("langgraph.prebuilt", "ToolNode"),

        # 新的 1.0 API
        ("langchain", "create_agent"),
    ]

    all_ok = True
    for module_name, obj_name in imports_to_check:
        try:
            module = __import__(module_name, fromlist=[obj_name])
            obj = getattr(module, obj_name)
            print(f"✅ from {module_name} import {obj_name}")
        except ImportError as e:
            print(f"❌ from {module_name} import {obj_name} - {e}")
            all_ok = False
        except AttributeError as e:
            print(f"⚠️  {module_name}.{obj_name} 不存在 - {e}")
            all_ok = False

    return all_ok

def check_deprecated_usage():
    """检查项目中是否使用了废弃的 API"""
    print("\n🔍 检查废弃 API 使用情况...")

    deprecated_patterns = [
        ("AgentExecutor", "已废弃，建议使用 create_agent"),
        ("from langchain.chains import", "已废弃，建议使用 LCEL 或迁移到 langchain-classic"),
        ("from langchain.agents import", "部分已废弃，检查是否需要迁移"),
    ]

    project_root = Path(__file__).parent.parent / "tradingagents"
    deprecated_found = []

    for py_file in project_root.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")

        for pattern, message in deprecated_patterns:
            if pattern in content:
                deprecated_found.append((py_file.relative_to(project_root), pattern, message))

    if deprecated_found:
        print(f"⚠️  发现 {len(deprecated_found)} 处使用废弃 API:")
        for file, pattern, message in deprecated_found[:10]:  # 只显示前10个
            print(f"   📄 {file}: {pattern}")
            print(f"      💡 {message}")
    else:
        print("✅ 未发现使用废弃 API")

    return len(deprecated_found) == 0

def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 测试基本功能...")

    try:
        from langchain_core.messages import HumanMessage, AIMessage
        from langchain_core.prompts import ChatPromptTemplate

        # 测试消息创建
        msg = HumanMessage(content="测试消息")
        print(f"✅ 消息创建: {type(msg).__name__}")

        # 测试 Prompt 模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是助手"),
            ("user", "{input}")
        ])
        print(f"✅ Prompt 模板: {type(prompt).__name__}")

        # 测试 StateGraph (现有代码使用)
        from langgraph.graph import StateGraph, END
        from typing import TypedDict

        class State(TypedDict):
            messages: list

        graph = StateGraph(State)
        print(f"✅ StateGraph: {type(graph).__name__}")

        return True

    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("🚀 LangChain 1.0 兼容性验证")
    print("=" * 70)

    # 1. 检查包版本
    print("\n📦 检查包版本...")
    packages = [
        "langchain",
        "langchain_core",
        "langchain_openai",
        "langchain_anthropic",
        "langchain_google_genai",
        "langgraph",
    ]

    all_installed = all(check_package_version(pkg) for pkg in packages)

    # 2. 检查导入兼容性
    imports_ok = check_import_compatibility()

    # 3. 检查废弃 API
    no_deprecated = check_deprecated_usage()

    # 4. 测试基本功能
    basic_ok = test_basic_functionality()

    # 总结
    print("\n" + "=" * 70)
    print("📊 验证结果总结")
    print("=" * 70)

    results = {
        "包安装": all_installed,
        "导入兼容性": imports_ok,
        "无废弃API": no_deprecated,
        "基本功能": basic_ok,
    }

    for check, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{check}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有检查通过！可以安全使用 LangChain 1.0")
    else:
        print("⚠️  部分检查失败，请查看上面的详细信息")
        if not no_deprecated:
            print("💡 提示: 废弃 API 不影响当前功能，但建议逐步迁移")
    print("=" * 70)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

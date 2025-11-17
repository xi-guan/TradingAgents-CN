#!/usr/bin/env python3
"""
生成安全的随机密钥
Generate secure random secrets for configuration
"""

import secrets
import string
from typing import Dict


def generate_random_string(length: int = 32, use_special_chars: bool = True) -> str:
    """
    生成随机字符串

    Args:
        length: 字符串长度
        use_special_chars: 是否包含特殊字符

    Returns:
        随机字符串
    """
    if use_special_chars:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    else:
        alphabet = string.ascii_letters + string.digits

    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_hex_secret(length: int = 32) -> str:
    """
    生成十六进制密钥

    Args:
        length: 字节长度

    Returns:
        十六进制字符串
    """
    return secrets.token_hex(length)


def generate_url_safe_secret(length: int = 32) -> str:
    """
    生成URL安全的密钥

    Args:
        length: 字节长度

    Returns:
        URL安全的base64字符串
    """
    return secrets.token_urlsafe(length)


def generate_password(length: int = 16) -> str:
    """
    生成数据库密码（不包含特殊字符以避免shell转义问题）

    Args:
        length: 密码长度

    Returns:
        密码字符串
    """
    return generate_random_string(length, use_special_chars=False)


def generate_all_secrets() -> Dict[str, str]:
    """
    生成所有需要的密钥

    Returns:
        密钥字典
    """
    secrets_dict = {
        # 数据库密码
        "POSTGRES_PASSWORD": generate_password(24),
        "REDIS_PASSWORD": generate_password(24),

        # JWT密钥（较长以提高安全性）
        "JWT_SECRET": generate_hex_secret(48),

        # CSRF密钥
        "CSRF_SECRET": generate_hex_secret(32),

        # Qdrant API密钥（可选，如果需要）
        "QDRANT_API_KEY": "",  # 留空表示不使用
    }

    return secrets_dict


def main():
    """主函数"""
    secrets_dict = generate_all_secrets()

    print("=" * 60)
    print("生成的安全密钥 / Generated Secrets")
    print("=" * 60)
    print()

    for key, value in secrets_dict.items():
        if value:
            print(f"{key}={value}")
        else:
            print(f"{key}=  # 可选 (optional)")

    print()
    print("=" * 60)
    print("✅ 密钥生成完成！请妥善保管这些密钥。")
    print("=" * 60)


if __name__ == "__main__":
    main()

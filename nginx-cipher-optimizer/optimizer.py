#!/usr/bin/env python3
"""
nginx 加密套件优化工具
检查和优化 nginx 的 SSL/TLS 加密套件配置
"""

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from typing import List, Tuple, Optional

# 推荐的配置
RECOMMENDED_PROTOCOLS = "TLSv1.2 TLSv1.3"

# TLSv1.2 加密套件（nginx 格式）
TLS12_CIPHERS_NGINX = [
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-RSA-CHACHA20-POLY1305-SHA256",
    "ECDHE-ECDSA-CHACHA20-POLY1305-SHA256",
]

# TLSv1.3 加密套件（nginx 格式）
TLS13_CIPHERS_NGINX = [
    "TLS-AES-128-GCM-SHA256",
    "TLS-AES-256-GCM-SHA384",
    "TLS-CHACHA20-POLY1305-SHA256",
]

# 完整的加密套件字符串
RECOMMENDED_CIPHERS = ":".join(TLS12_CIPHERS_NGINX + TLS13_CIPHERS_NGINX)


def find_nginx_conf() -> Optional[str]:
    """查找 nginx 配置文件"""
    common_paths = [
        "/etc/nginx/nginx.conf",
        "/usr/local/etc/nginx/nginx.conf",
        "./nginx.conf",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None


def parse_nginx_config(file_path: str) -> dict:
    """解析 nginx 配置，查找 ssl 相关指令"""
    result = {
        'ssl_protocols': None,
        'ssl_ciphers': None,
        'ssl_prefer_server_ciphers': None,
        'blocks': [],  # 存储找到配置的块位置
    }

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # 查找 ssl_protocols
        protocols_match = re.search(r'ssl_protocols\s+([^;]+);', content)
        if protocols_match:
            result['ssl_protocols'] = protocols_match.group(1).strip()

        # 查找 ssl_ciphers
        ciphers_match = re.search(r'ssl_ciphers\s+([^;]+);', content)
        if ciphers_match:
            result['ssl_ciphers'] = ciphers_match.group(1).strip()

        # 查找 ssl_prefer_server_ciphers
        prefer_match = re.search(r'ssl_prefer_server_ciphers\s+(on|off);', content, re.IGNORECASE)
        if prefer_match:
            result['ssl_prefer_server_ciphers'] = prefer_match.group(1).lower()

    except Exception as e:
        print(f"Error reading config file: {e}")

    return result


def compare_config(current: dict) -> dict:
    """比较当前配置和推荐配置"""
    issues = []
    fixes = []

    # 检查协议
    if current['ssl_protocols'] != RECOMMENDED_PROTOCOLS:
        issues.append(("协议版本", current['ssl_protocols'], RECOMMENDED_PROTOCOLS))
        fixes.append("更新 ssl_protocols")

    # 检查加密套件
    if current['ssl_ciphers'] != RECOMMENDED_CIPHERS:
        issues.append(("加密套件", current['ssl_ciphers'], RECOMMENDED_CIPHERS))
        fixes.append("更新 ssl_ciphers")

    # 检查 ssl_prefer_server_ciphers
    if current['ssl_prefer_server_ciphers'] != 'on':
        issues.append(("服务端优先", current['ssl_prefer_server_ciphers'], 'on'))
        fixes.append("设置 ssl_prefer_server_ciphers on")

    return {
        'needs_update': len(issues) > 0,
        'issues': issues,
        'fixes': fixes,
    }


def update_nginx_config(file_path: str) -> Tuple[bool, str]:
    """更新 nginx 配置文件"""
    try:
        # 备份原文件
        backup_path = file_path + '.bak'
        shutil.copy2(file_path, backup_path)
        print(f"✓ 已备份配置文件到: {backup_path}")

        with open(file_path, 'r') as f:
            content = f.read()

        # 更新或添加 ssl_protocols
        if re.search(r'ssl_protocols\s+[^;]+;', content):
            content = re.sub(
                r'ssl_protocols\s+[^;]+;',
                f'ssl_protocols {RECOMMENDED_PROTOCOLS};',
                content
            )
        else:
            # 在 http 块中添加
            content = re.sub(
                r'(\s*http\s*\{)',
                r'\1\n    ssl_protocols TLSv1.2 TLSv1.3;',
                content
            )

        # 更新或添加 ssl_ciphers
        if re.search(r'ssl_ciphers\s+[^;]+;', content):
            content = re.sub(
                r'ssl_ciphers\s+[^;]+;',
                f'ssl_ciphers {RECOMMENDED_CIPHERS};',
                content
            )
        else:
            content = re.sub(
                r'(\s*http\s*\{)',
                fr'\1\n    ssl_ciphers {RECOMMENDED_CIPHERS};',
                content
            )

        # 更新或添加 ssl_prefer_server_ciphers
        if re.search(r'ssl_prefer_server_ciphers\s+(on|off);', content, re.IGNORECASE):
            content = re.sub(
                r'ssl_prefer_server_ciphers\s+(on|off);',
                'ssl_prefer_server_ciphers on;',
                content,
                flags=re.IGNORECASE
            )
        else:
            content = re.sub(
                r'(\s*http\s*\{)',
                r'\1\n    ssl_prefer_server_ciphers on;',
                content
            )

        # 写入更新后的配置
        with open(file_path, 'w') as f:
            f.write(content)

        return True, backup_path

    except Exception as e:
        return False, str(e)


def verify_nginx_config() -> bool:
    """验证 nginx 配置"""
    try:
        result = subprocess.run(
            ['nginx', '-t'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


def print_status(current_config: dict, comparison: dict, config_path: str):
    """打印配置状态"""
    print("## nginx 加密套件配置检查\n")
    print(f"**配置文件:** {config_path}\n")

    print("### 当前配置")
    print(f"- ssl_protocols: {current_config['ssl_protocols'] or '(未设置)'}")
    print(f"- ssl_ciphers: {current_config['ssl_ciphers'] or '(未设置)'}")
    print(f"- ssl_prefer_server_ciphers: {current_config['ssl_prefer_server_ciphers'] or '(未设置)'}")

    print("\n### 推荐配置")
    print(f"- ssl_protocols: {RECOMMENDED_PROTOCOLS}")
    print(f"- ssl_ciphers: {RECOMMENDED_CIPHERS}")
    print(f"- ssl_prefer_server_ciphers: on")

    if comparison['needs_update']:
        print("\n### 差异")
        for name, current, recommended in comparison['issues']:
            print(f"❌ {name}: 当前 = {current}, 推荐 = {recommended}")
    else:
        print("\n✓ 配置已经是最优的！")


def main():
    parser = argparse.ArgumentParser(description='nginx 加密套件优化工具')
    parser.add_argument('config', nargs='?', help='nginx 配置文件路径')
    parser.add_argument('--apply', action='store_true', help='应用优化配置')

    args = parser.parse_args()

    # 查找配置文件
    config_path = args.config or find_nginx_conf()
    if not config_path or not os.path.exists(config_path):
        print("❌ 找不到 nginx 配置文件")
        print("请指定配置文件路径或确保 nginx 已正确安装")
        return 1

    # 解析当前配置
    current_config = parse_nginx_config(config_path)
    comparison = compare_config(current_config)

    # 打印状态
    print_status(current_config, comparison, config_path)

    if not comparison['needs_update']:
        return 0

    # 应用更改
    if args.apply:
        print("\n正在应用优化配置...")
        success, result = update_nginx_config(config_path)

        if success:
            print("✓ 配置已更新")

            # 验证配置
            print("\n正在验证 nginx 配置...")
            if verify_nginx_config():
                print("✓ nginx 配置验证通过")
                print("\n## nginx 加密套件配置已优化\n")
                print("### 更改内容")
                for fix in comparison['fixes']:
                    print(f"- [x] {fix}")
            else:
                print("❌ nginx 配置验证失败，请检查")
                print(f"备份文件保存在: {result}")
                return 1
        else:
            print(f"❌ 更新失败: {result}")
            return 1
    else:
        print("\n使用 --apply 参数来应用优化配置")

    return 0


if __name__ == '__main__':
    main()

---
name: nginx-cipher-optimizer
description: 检查和自动优化 nginx 的加密套件设置，仅支持 TLSv1.3 和 TLSv1.2，使用指定的加密套件并按效率排序
license: MIT
metadata:
  author: nginx-cipher-optimizer
  version: "1.0"
---

# nginx 加密套件优化工具

## 功能说明

本 skill 用于检查和自动优化 nginx 的 SSL/TLS 加密套件配置，只支持 TLSv1.3 和 TLSv1.2 协议，并按照指定的加密套件列表进行配置，按效率从高到低排序。

## 支持的协议和加密套件

### TLSv1.3（按效率从高到低）
1. TLS_AES_128_GCM_SHA256
2. TLS_AES_256_GCM_SHA384
3. TLS_CHACHA20_POLY1305_SHA256

### TLSv1.2（按效率从高到低）
1. TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
2. TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
3. TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
4. TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
5. TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256
6. TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256

**重要：TLSv1.2 的加密套件优先于 TLSv1.3，按效率由高到低排序，不考虑安全性。**

## 输入

可以指定 nginx 配置文件路径。如果省略，会自动搜索常见位置：
- /etc/nginx/nginx.conf
- /usr/local/etc/nginx/nginx.conf
- ./nginx.conf

## 步骤

1. **检查是否有 Python 脚本可用**

   首先检查本 skill 附带的 `optimizer.py` 脚本是否可用。

2. **查找 nginx 配置文件**

   如果提供了路径，使用该路径；否则搜索常见位置。

3. **使用 Python 脚本检查当前配置**

   运行 `python optimizer.py <config-path>` 来分析当前配置。

4. **显示配置差异**

   - 显示当前配置
   - 显示推荐配置
   - 突出显示差异

5. **询问是否应用优化**

   使用 AskUserQuestion 工具询问用户是否应用优化配置。

6. **应用优化配置**

   如果用户确认，运行 `python optimizer.py <config-path> --apply` 来应用优化。

7. **验证配置**

   脚本会自动运行 `nginx -t` 验证配置是否正确。

## 推荐的配置

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305-SHA256:ECDHE-ECDSA-CHACHA20-POLY1305-SHA256:TLS-AES-128-GCM-SHA256:TLS-AES-256-GCM-SHA384:TLS-CHACHA20-POLY1305-SHA256;
ssl_prefer_server_ciphers on;
```

注意：nginx 中 TLSv1.3 加密套件使用短横线格式，TLSv1.2 同样使用短横线格式，用冒号分隔。

## 输出格式

### 检查模式

```
## nginx 加密套件配置检查

**配置文件:** /path/to/nginx.conf

### 当前配置
- ssl_protocols: TLSv1 TLSv1.1 TLSv1.2 TLSv1.3
- ssl_ciphers: ... (当前值)
- ssl_prefer_server_ciphers: on/off

### 推荐配置
- ssl_protocols: TLSv1.2 TLSv1.3
- ssl_ciphers: ... (推荐值)
- ssl_prefer_server_ciphers: on

### 差异
❌ 协议包含不支持的版本: TLSv1, TLSv1.1
❌ 加密套件不符合要求
```

### 优化后输出

```
## nginx 加密套件配置已优化

**配置文件:** /path/to/nginx.conf

### 更改内容
- [x] 更新 ssl_protocols
- [x] 更新 ssl_ciphers  
- [x] 设置 ssl_prefer_server_ciphers on

### 验证结果
✓ nginx 配置验证通过
```

## 手动实现（如果 Python 脚本不可用）

如果无法使用 Python 脚本，按以下步骤手动操作：

1. 读取 nginx 配置文件
2. 使用正则表达式查找和替换以下指令：
   - `ssl_protocols`
   - `ssl_ciphers`
   - `ssl_prefer_server_ciphers`
3. 在修改前备份原始文件
4. 验证配置语法

## Guardrails

- 在修改配置前先备份原始文件（脚本会自动创建 .bak 文件）
- 只修改 ssl_protocols、ssl_ciphers、ssl_prefer_server_ciphers 这三个指令
- 如果指令不存在，在 http 块中添加
- 修改后必须验证 nginx 配置语法

---
name: systemd-service-generator
description: 自动生成 Debian 系统上的 systemd 服务单元文件（.service），支持自定义字段与内置 Clash 模板
license: MIT
metadata:
  author: systemd-service-generator
  version: "1.0"
---

# systemd 服务生成器

## 功能说明

本 skill 用于自动生成 Debian 系统上的 systemd 服务单元文件。支持两种模式：

1. **自定义服务**：通过命令行参数指定 Description、ExecStart、User 等字段。
2. **内置模板**：使用 `--template clash` 快速生成 Clash 代理服务的 systemd 单元文件。

## 模板示例

### Clash 服务模板

```ini
[Unit]
Description=Clash daemon, A rule-based proxy in Go.
After=network-online.target

[Service]
Type=simple
Restart=always
User=www-data
ExecStart=/usr/local/bin/clash -d /etc/clash

[Install]
WantedBy=multi-user.target
```

## 输入参数

运行 `python3 generator.py <service-name>` 时使用以下参数：

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | - | - | 服务名（不含 `.service` 后缀） |
| `--description` | `-d` | `My service` | 服务描述 |
| `--after` | `-a` | `network-online.target` | `After` 目标 |
| `--type` | - | `simple` | 服务类型 |
| `--restart` | `-r` | `always` | 重启策略 |
| `--user` | `-u` | `www-data` | 运行用户 |
| `--exec-start` | `-e` | `/usr/local/bin/myapp` | 启动命令 |
| `--wanted-by` | - | `multi-user.target` | `WantedBy` 目标 |
| `--template` | `-t` | - | 使用内置 `clash` 模板或自定义模板文件路径 |
| `--output` | `-o` | - | 输出路径，默认 root 用户写入 `/etc/systemd/system/`，非 root 写入当前目录 |
| `--apply` | - | false | 写入文件，否则仅打印到 stdout |
| `--reload` | - | false | 写入后执行 `systemctl daemon-reload` |
| `--enable` | - | false | 写入后执行 `systemctl enable <service>` |
| `--start` | - | false | 写入后执行 `systemctl start <service>` |

## 使用步骤

1. **生成并预览服务文件**

   ```bash
   python3 generator.py clash -t clash
   ```

2. **应用并启用 Clash 服务**

   ```bash
   sudo python3 generator.py clash -t clash --apply --reload --enable --start
   ```

3. **生成自定义服务**

   ```bash
   python3 generator.py myapp \
     -d "My custom application" \
     -u myuser \
     -e "/usr/local/bin/myapp --config /etc/myapp/config.yaml" \
     --apply --reload --enable
   ```

4. **使用自定义模板文件**

   ```bash
   python3 generator.py myapp -t /path/to/template.service --apply
   ```

## 输出格式

### 仅预览模式

```ini
[Unit]
Description=My custom application
After=network-online.target

[Service]
Type=simple
Restart=always
User=myuser
ExecStart=/usr/local/bin/myapp --config /etc/myapp/config.yaml

[Install]
WantedBy=multi-user.target
```

### 应用模式

```
Service unit written to: /etc/systemd/system/myapp.service
```

## Guardrails

- 写入已存在的服务文件前会自动创建 `.bak` 备份。
- 默认只打印到 stdout，必须显式使用 `--apply` 才会写入文件。
- 修改 systemd 配置后建议使用 `--reload` 重新加载守护进程。
- 启用或启动服务需要 root 权限。
- 本工具生成的单元文件适用于 Debian 及其衍生发行版，其他 systemd 发行版通常也可兼容。

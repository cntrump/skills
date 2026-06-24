#!/usr/bin/env python3
"""Generate systemd service unit files for Debian systems."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_TEMPLATE = """[Unit]
Description={description}
After={after}

[Service]
Type={type}
Restart={restart}
User={user}
ExecStart={exec_start}

[Install]
WantedBy={wanted_by}
"""

CLASH_TEMPLATE = """[Unit]
Description=Clash daemon, A rule-based proxy in Go.
After=network-online.target

[Service]
Type=simple
Restart=always
User=www-data
ExecStart=/usr/local/bin/clash -d /etc/clash

[Install]
WantedBy=multi-user.target
"""


def build_unit(args) -> str:
    """Build a systemd unit file from parsed arguments."""
    if args.template == "clash":
        return CLASH_TEMPLATE

    if args.template:
        template_path = Path(args.template)
        if not template_path.is_file():
            print(f"Error: template file not found: {template_path}", file=sys.stderr)
            sys.exit(1)
        return template_path.read_text(encoding="utf-8")

    return DEFAULT_TEMPLATE.format(
        description=args.description,
        after=args.after,
        type=args.type,
        restart=args.restart,
        user=args.user,
        exec_start=args.exec_start,
        wanted_by=args.wanted_by,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate systemd service unit files for Debian systems."
    )
    parser.add_argument("name", help="Service name without .service extension")
    parser.add_argument(
        "--description", "-d", default="My service", help="Service description"
    )
    parser.add_argument(
        "--after", "-a", default="network-online.target", help="After targets"
    )
    parser.add_argument("--type", default="simple", help="Service type")
    parser.add_argument("--restart", "-r", default="always", help="Restart policy")
    parser.add_argument("--user", "-u", default="www-data", help="User to run as")
    parser.add_argument(
        "--exec-start", "-e", default="/usr/local/bin/myapp", help="ExecStart command"
    )
    parser.add_argument(
        "--wanted-by", default="multi-user.target", help="WantedBy target"
    )
    parser.add_argument(
        "--template",
        "-t",
        default="",
        help="Use built-in 'clash' template or a custom template file path",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="",
        help="Output path. Defaults to /etc/systemd/system/<name>.service if run as root, otherwise ./<name>.service",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the file to disk. Without this flag, the unit content is printed to stdout.",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Run systemctl daemon-reload after writing the unit file",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable the service after writing the unit file (implies --apply)",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start the service after writing the unit file (implies --apply)",
    )

    args = parser.parse_args()

    service_name = args.name if args.name.endswith(".service") else f"{args.name}.service"
    unit_content = build_unit(args)

    if not args.apply and not args.reload and not args.enable and not args.start:
        print(unit_content)
        return 0

    if args.output:
        output_path = Path(args.output)
    else:
        if os.geteuid() == 0:
            output_path = Path("/etc/systemd/system") / service_name
        else:
            output_path = Path.cwd() / service_name

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        backup = output_path.with_suffix(f"{output_path.suffix}.bak")
        backup.write_text(output_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Backup created: {backup}")

    output_path.write_text(unit_content, encoding="utf-8")
    print(f"Service unit written to: {output_path}")

    if args.reload:
        os.system("systemctl daemon-reload")
    if args.enable:
        os.system(f"systemctl enable {service_name}")
    if args.start:
        os.system(f"systemctl start {service_name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Security Quick Fix Script
安全快速修复脚本

This script helps fix the most critical security issues immediately.
此脚本帮助立即修复最严重的安全问题。

Usage:
    python scripts/security_quickfix.py
"""

import secrets
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def generate_secure_keys():
    """Generate secure random keys"""
    print_header("🔑 生成安全密钥 | Generate Secure Keys")

    keys = {
        "JWT_SECRET_KEY": secrets.token_urlsafe(32),
        "ADMIN_SECRET_KEY": secrets.token_urlsafe(32),
        "DATABASE_ENCRYPTION_KEY": secrets.token_urlsafe(32),
    }

    print("生成的新密钥 | Generated Keys:")
    print("\n请将以下内容复制到你的 .env 文件(生产环境):")
    print("Please copy to your .env file (production):\n")

    for key_name, key_value in keys.items():
        print(f"{key_name}={key_value}")

    print("\n⚠️  警告 | WARNING:")
    print("- 请勿将这些密钥提交到Git")
    print("- Do NOT commit these keys to Git")
    print("- 将 .env 添加到 .gitignore")
    print("- Add .env to .gitignore\n")

    return keys


def check_gitignore():
    """Check if .env is in .gitignore"""
    print_header("📄 检查 .gitignore | Check .gitignore")

    gitignore_path = project_root / ".gitignore"

    if not gitignore_path.exists():
        print("❌ .gitignore 文件不存在! | .gitignore not found!")
        create = input("是否创建? | Create? (y/n): ")
        if create.lower() == 'y':
            gitignore_path.write_text("# Environment variables\n.env\n.env.local\n.env.*.local\n")
            print("✅ 已创建 .gitignore | Created .gitignore")
        return

    content = gitignore_path.read_text()

    if ".env" not in content:
        print("⚠️  .env 不在 .gitignore 中! | .env not in .gitignore!")
        add = input("是否添加? | Add? (y/n): ")
        if add.lower() == 'y':
            with gitignore_path.open('a') as f:
                f.write("\n# Environment variables\n.env\n.env.local\n.env.*.local\n")
            print("✅ 已添加到 .gitignore | Added to .gitignore")
    else:
        print("✅ .env 已在 .gitignore 中 | .env is in .gitignore")


def check_env_in_git():
    """Check if .env is tracked by git"""
    print_header("🔍 检查Git历史 | Check Git History")

    import subprocess

    try:
        # Check if .env is currently tracked
        result = subprocess.run(
            ['git', 'ls-files', '.env'],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            print("❌ 危险! .env 文件被Git追踪!")
            print("❌ DANGER! .env is tracked by Git!")
            print("\n请执行以下命令移除:")
            print("Please run these commands to remove:\n")
            print("git rm --cached .env")
            print("git commit -m 'Remove .env from git history'")
            print("\n⚠️  警告: 这只移除当前版本,不清除历史记录")
            print("⚠️  WARNING: This only removes current version, not history")
            print("\n完全清除历史记录需要:")
            print("To completely remove from history:\n")
            print("git filter-repo --path .env --invert-paths")
            print("# 或 | or")
            print("bfg --delete-files .env")

        else:
            print("✅ .env 未被Git追踪 | .env is not tracked by Git")

    except FileNotFoundError:
        print("⚠️  未检测到Git | Git not detected")
    except Exception as e:
        print(f"⚠️  检查失败 | Check failed: {e}")


def generate_env_template():
    """Generate .env.example template"""
    print_header("📝 生成 .env.example | Generate .env.example")

    template = """# AcademicGuard Environment Configuration
# 环境配置模板

# Application Settings
APP_NAME=AcademicGuard
DEBUG=false  # MUST be false in production | 生产环境必须为false

# LLM Provider Settings
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-plus
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.7

# DashScope (阿里云灵积) API
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus

# Volcengine (火山引擎) API
VOLCENGINE_API_KEY=your_volcengine_api_key_here
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCENGINE_MODEL=deepseek-v3-2-251201

# Security Settings
# 使用命令生成: python -c "import secrets; print(secrets.token_urlsafe(32))"
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your_jwt_secret_key_here_at_least_32_chars
ADMIN_SECRET_KEY=your_admin_secret_key_here

# Default Settings
DEFAULT_COLLOQUIALISM_LEVEL=4
DEFAULT_TARGET_LANG=en
SEMANTIC_SIMILARITY_THRESHOLD=0.80

# CORS Settings (production should be specific domains)
# CORS设置(生产环境应指定具体域名)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
"""

    template_path = project_root / ".env.example"
    template_path.write_text(template)
    print(f"✅ 已生成 {template_path} | Generated {template_path}")
    print("\n团队成员可以复制此文件为 .env 并填入实际值")
    print("Team members can copy this file to .env and fill in actual values")


def check_cors_config():
    """Check CORS configuration"""
    print_header("🌐 检查CORS配置 | Check CORS Config")

    main_py = project_root / "src" / "main.py"

    if not main_py.exists():
        print("⚠️  未找到 src/main.py | src/main.py not found")
        return

    content = main_py.read_text()

    if 'allow_origins=["*"]' in content:
        print("❌ 危险! CORS允许所有来源!")
        print("❌ DANGER! CORS allows all origins!")
        print("\n在 src/main.py 中找到:")
        print("Found in src/main.py:\n")
        print('    allow_origins=["*"],  # ⚠️  不安全!')
        print("\n建议修改为:")
        print("Suggested fix:\n")
        print("""    allow_origins=[
        "http://localhost:5173",  # 开发环境 | Development
        "https://yourdomain.com",  # 生产环境 | Production
    ],""")
    else:
        print("✅ CORS配置看起来合理 | CORS config looks reasonable")


def check_https_enforcement():
    """Check HTTPS enforcement"""
    print_header("🔒 检查HTTPS强制 | Check HTTPS Enforcement")

    print("生产环境部署检查清单 | Production Deployment Checklist:\n")

    checks = [
        "[ ] 已配置SSL证书(Let's Encrypt推荐) | SSL certificate configured",
        "[ ] Nginx/Caddy配置了HTTPS重定向 | HTTPS redirect configured",
        "[ ] 添加了HSTS响应头 | HSTS header added",
        "[ ] 环境变量DEBUG=false | DEBUG=false in env",
        "[ ] 所有API调用使用https:// | All API calls use https://",
    ]

    for check in checks:
        print(check)

    print("\n参考Nginx配置:")
    print("Reference Nginx config:\n")
    print("""server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000" always;

    location /api/v1/ {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}""")


def install_security_packages():
    """Suggest security packages to install"""
    print_header("📦 安全包安装建议 | Security Packages")

    packages = [
        ("bcrypt", "密码哈希 | Password hashing"),
        ("slowapi", "API速率限制 | API rate limiting"),
        ("python-magic", "文件类型检测 | File type detection"),
        ("bandit", "代码安全扫描 | Code security scanner"),
        ("pip-audit", "依赖包漏洞检查 | Dependency vulnerability checker"),
    ]

    print("建议安装以下安全相关包:")
    print("Recommended security packages:\n")

    for pkg, desc in packages:
        print(f"  - {pkg:<20} # {desc}")

    print("\n安装命令 | Install command:")
    print(f"pip install {' '.join(p[0] for p in packages)}")


def main():
    """Main function"""
    print("\n" + "="*60)
    print("  AcademicGuard Security Quick Fix")
    print("  AcademicGuard 安全快速修复工具")
    print("="*60)

    print("\n此脚本将检查并修复关键安全问题")
    print("This script checks and fixes critical security issues\n")

    try:
        # 1. Generate secure keys
        keys = generate_secure_keys()

        # 2. Check .gitignore
        check_gitignore()

        # 3. Check if .env is in git
        check_env_in_git()

        # 4. Generate .env.example
        generate_env_template()

        # 5. Check CORS
        check_cors_config()

        # 6. Check HTTPS
        check_https_enforcement()

        # 7. Security packages
        install_security_packages()

        print_header("✅ 检查完成 | Check Complete")

        print("\n下一步行动 | Next Steps:\n")
        print("1. 轮换所有已泄露的API密钥")
        print("   Rotate all exposed API keys")
        print("\n2. 从Git历史中删除 .env 文件")
        print("   Remove .env from Git history")
        print("\n3. 修复 src/main.py 中的CORS配置")
        print("   Fix CORS config in src/main.py")
        print("\n4. 配置生产环境HTTPS")
        print("   Configure HTTPS for production")
        print("\n5. 阅读完整的安全审计报告:")
        print("   Read full security audit report:")
        print("   doc/security-audit-report.md")

        print("\n" + "="*60 + "\n")

    except KeyboardInterrupt:
        print("\n\n用户中断 | User interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误 | Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

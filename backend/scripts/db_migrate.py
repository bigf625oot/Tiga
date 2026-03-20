import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="自动生成并执行数据库迁移脚本 (Alembic)")
    parser.add_argument("-m", "--message", default="auto migration", help="迁移脚本的描述信息")
    parser.add_argument("--dry-run", action="store_true", help="仅生成脚本，不执行 upgrade")
    
    args = parser.parse_args()

    # 切换到 backend 目录（保证 alembic 能找到 alembic.ini）
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(backend_dir)
    
    print(f"[*] 正在对比数据库并生成迁移脚本: {args.message}...")
    try:
        # 生成迁移脚本
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", args.message], check=True)
        print("\n[*] 迁移脚本生成成功！")
        
        if args.dry_run:
            print("[*] 处于 --dry-run 模式，跳过执行迁移。")
            return

        print("[*] 正在执行迁移命令，将修改应用到数据库...")
        # 执行迁移
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("\n[*] 数据库迁移执行成功！")
        
    except subprocess.CalledProcessError as e:
        print(f"\n[!] 发生错误，进程退出码: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n[!] 找不到 alembic 命令，请确保已安装相关的依赖，并在正确的虚拟环境中执行。")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ExamParse Desktop 完整构建脚本
自动构建 Python sidecar 和 Tauri 桌面应用
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path
from typing import List, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DESKTOP_DIR = PROJECT_ROOT / "apps" / "desktop"
SIDECAR_DIST_DIR = DESKTOP_DIR / "src-tauri" / "sidecar-dist"

def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if arch in ["x86_64", "amd64"]:
        arch = "x86_64"
    elif arch in ["aarch64", "arm64"]:
        arch = "aarch64"
    elif arch in ["i386", "i686"]:
        arch = "i686"
    
    return system, arch

def run_command(cmd: List[str], cwd: Optional[Path] = None, description: str = "") -> None:
    """运行命令"""
    if description:
        print(f"🚀 {description}")
    
    print(f"   Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stdout:
            print(f"   STDOUT: {e.stdout}")
        if e.stderr:
            print(f"   STDERR: {e.stderr}")
        raise

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 Checking dependencies...")
    
    # 检查 Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except:
        raise RuntimeError("Python not found")
    
    # 检查 Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✅ Node.js: {result.stdout.strip()}")
    except:
        raise RuntimeError("Node.js not found")
    
    # 检查 npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print(f"✅ npm: {result.stdout.strip()}")
    except:
        raise RuntimeError("npm not found")
    
    # 检查 Rust/Cargo
    try:
        result = subprocess.run(["cargo", "--version"], capture_output=True, text=True)
        print(f"✅ Cargo: {result.stdout.strip()}")
    except:
        raise RuntimeError("Rust/Cargo not found")

def build_sidecar():
    """构建 Python sidecar"""
    print("\n📦 Building Python sidecar...")
    
    # 运行 sidecar 构建脚本
    build_script = PROJECT_ROOT / "scripts" / "build_sidecar.py"
    run_command([sys.executable, str(build_script)], 
                cwd=PROJECT_ROOT, 
                description="Building sidecar executable")

def setup_frontend_deps():
    """安装前端依赖"""
    print("\n📦 Setting up frontend dependencies...")
    
    ui_dir = DESKTOP_DIR / "ui"
    if (ui_dir / "package-lock.json").exists():
        run_command(["npm", "ci"], 
                   cwd=ui_dir, 
                   description="Installing UI dependencies (clean)")
    else:
        run_command(["npm", "install"], 
                   cwd=ui_dir, 
                   description="Installing UI dependencies")

def build_frontend():
    """构建前端"""
    print("\n🏗️  Building frontend...")
    
    ui_dir = DESKTOP_DIR / "ui"
    run_command(["npm", "run", "build"], 
               cwd=ui_dir, 
               description="Building frontend")

def build_desktop_app(targets: Optional[List[str]] = None):
    """构建桌面应用"""
    print("\n🏗️  Building Tauri desktop app...")
    
    cmd = ["npm", "run", "tauri", "build"]
    
    if targets:
        for target in targets:
            cmd.extend(["--target", target])
    
    run_command(cmd, 
               cwd=DESKTOP_DIR, 
               description=f"Building desktop app for targets: {targets or 'default'}")

def build_dev_desktop():
    """构建开发版桌面应用"""
    print("\n🏗️  Building development desktop app...")
    
    run_command(["npm", "run", "tauri", "dev"], 
               cwd=DESKTOP_DIR, 
               description="Starting development build")

def clean_build():
    """清理构建目录"""
    print("\n🧹 Cleaning build directories...")
    
    dirs_to_clean = [
        DESKTOP_DIR / "ui" / "dist",
        DESKTOP_DIR / "ui" / "node_modules",
        DESKTOP_DIR / "node_modules",
        DESKTOP_DIR / "src-tauri" / "target",
        SIDECAR_DIST_DIR,
        PROJECT_ROOT / "build",
        PROJECT_ROOT / "dist",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"   Removing: {dir_path}")
            shutil.rmtree(dir_path)
    
    # 清理 spec 文件
    spec_files = PROJECT_ROOT.glob("*.spec")
    for spec_file in spec_files:
        print(f"   Removing: {spec_file}")
        spec_file.unlink()

def verify_build():
    """验证构建结果"""
    print("\n🔍 Verifying build results...")
    
    # 检查 sidecar 可执行文件
    system, _ = get_platform_info()
    sidecar_name = "examparse-sidecar.exe" if system == "windows" else "examparse-sidecar"
    sidecar_path = SIDECAR_DIST_DIR / sidecar_name
    
    if sidecar_path.exists():
        size_mb = sidecar_path.stat().st_size / (1024 * 1024)
        print(f"✅ Sidecar: {sidecar_path} ({size_mb:.1f} MB)")
    else:
        print(f"❌ Sidecar not found: {sidecar_path}")
        return False
    
    # 检查前端构建
    frontend_dist = DESKTOP_DIR / "ui" / "dist"
    if frontend_dist.exists():
        print(f"✅ Frontend: {frontend_dist}")
    else:
        print(f"❌ Frontend dist not found: {frontend_dist}")
        return False
    
    # 检查 Tauri 构建结果
    target_dir = DESKTOP_DIR / "src-tauri" / "target" / "release"
    if target_dir.exists():
        print(f"✅ Tauri build: {target_dir}")
        
        # 列出生成的安装包
        bundle_dir = target_dir / "bundle"
        if bundle_dir.exists():
            for item in bundle_dir.iterdir():
                if item.is_dir():
                    for bundle_file in item.iterdir():
                        if bundle_file.is_file():
                            size_mb = bundle_file.stat().st_size / (1024 * 1024)
                            print(f"📦 Package: {bundle_file.name} ({size_mb:.1f} MB)")
    else:
        print(f"❌ Tauri build not found: {target_dir}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="ExamParse Desktop Build Script")
    parser.add_argument("--clean", action="store_true", help="Clean build directories first")
    parser.add_argument("--dev", action="store_true", help="Start development server instead of building")
    parser.add_argument("--sidecar-only", action="store_true", help="Build sidecar only")
    parser.add_argument("--frontend-only", action="store_true", help="Build frontend only")
    parser.add_argument("--targets", nargs="*", help="Specific build targets")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency checks")
    
    args = parser.parse_args()
    
    print("🏗️  ExamParse Desktop Build Script")
    print("=" * 50)
    
    system, arch = get_platform_info()
    print(f"🖥️  Platform: {system}/{arch}")
    
    try:
        if args.clean:
            clean_build()
        
        if not args.skip_deps:
            check_dependencies()
        
        if args.sidecar_only:
            build_sidecar()
        elif args.frontend_only:
            setup_frontend_deps()
            build_frontend()
        elif args.dev:
            # 开发模式：只需要前端依赖，不需要构建 sidecar
            setup_frontend_deps()
            build_dev_desktop()
        else:
            # 完整构建流程
            build_sidecar()
            setup_frontend_deps()
            build_frontend()
            build_desktop_app(args.targets)
            
            if verify_build():
                print(f"\n🎉 Build completed successfully!")
                print(f"📁 Build artifacts in: {DESKTOP_DIR / 'src-tauri' / 'target'}")
            else:
                print(f"\n❌ Build verification failed!")
                sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
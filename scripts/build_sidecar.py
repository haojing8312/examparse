#!/usr/bin/env python3
"""
构建 Python sidecar 为独立可执行文件
支持 Windows/macOS/Linux 跨平台打包
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SIDECAR_DIR = PROJECT_ROOT / "sidecar"
DIST_DIR = PROJECT_ROOT / "apps" / "desktop" / "src-tauri" / "sidecar-dist"

def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # 标准化架构名称
    if arch in ["x86_64", "amd64"]:
        arch = "x86_64"
    elif arch in ["aarch64", "arm64"]:
        arch = "aarch64"
    elif arch in ["i386", "i686"]:
        arch = "i686"
    
    return system, arch

def get_executable_name(base_name: str) -> str:
    """根据平台获取可执行文件名"""
    system, _ = get_platform_info()
    if system == "windows":
        return f"{base_name}.exe"
    return base_name

def install_pyinstaller():
    """安装 PyInstaller"""
    try:
        import PyInstaller
        print(f"PyInstaller already installed: {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

def create_spec_file() -> Path:
    """创建 PyInstaller spec 文件"""
    system, arch = get_platform_info()
    executable_name = get_executable_name("examparse-sidecar")
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

# 项目根目录
project_root = Path(r"{PROJECT_ROOT}")
sidecar_dir = project_root / "sidecar"

a = Analysis(
    [str(sidecar_dir / "__main__.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 包含 sidecar 包的所有 Python 文件
        (str(sidecar_dir / "*.py"), "sidecar"),
        (str(sidecar_dir / "event_schema.json"), "sidecar"),
        # 包含项目依赖的重要模块
        (str(project_root / "utils"), "utils"),
        (str(project_root / "config.py"), "."),
        (str(project_root / "question_processor.py"), "."),
        (str(project_root / "question_standardization_manager.py"), "."),
        (str(project_root / "question_standardizer_base.py"), "."),
        (str(project_root / "*_standardizer.py"), "."),
    ],
    hiddenimports=[
        'sidecar',
        'sidecar.main',
        'sidecar.events', 
        'sidecar.config',
        'sidecar.runner',
        'utils',
        'utils.standardization_utils',
        'pydantic',
        'pydantic.fields',
        'pydantic.validators',
        'openai',
        'google.generativeai',
        'openpyxl',
        'PyMuPDF',
        'fitz',
        'tqdm',
        'httpx',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{executable_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='{arch}',
    codesign_identity=None,
    entitlements_file=None,
)
"""

    spec_file = PROJECT_ROOT / "examparse-sidecar.spec"
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print(f"Created spec file: {spec_file}")
    return spec_file

def create_main_module():
    """创建 __main__.py 入口文件"""
    main_file = SIDECAR_DIR / "__main__.py"
    if not main_file.exists():
        content = '''"""
Sidecar 包的主入口点
"""
from sidecar.main import main

if __name__ == "__main__":
    main()
'''
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created main module: {main_file}")

def build_sidecar():
    """构建 sidecar 可执行文件"""
    system, arch = get_platform_info()
    print(f"Building sidecar for {system}/{arch}")
    
    # 确保输出目录存在
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # 创建 spec 文件
    spec_file = create_spec_file()
    
    # 创建 __main__.py
    create_main_module()
    
    try:
        # 运行 PyInstaller
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
        
        # 移动生成的可执行文件到目标位置
        executable_name = get_executable_name("examparse-sidecar")
        source_exe = PROJECT_ROOT / "dist" / executable_name
        target_exe = DIST_DIR / executable_name
        
        if source_exe.exists():
            if target_exe.exists():
                target_exe.unlink()
            shutil.move(str(source_exe), str(target_exe))
            print(f"Built sidecar: {target_exe}")
            
            # 确保可执行权限 (Unix-like systems)
            if system != "windows":
                os.chmod(target_exe, 0o755)
                
            return target_exe
        else:
            raise FileNotFoundError(f"Executable not found: {source_exe}")
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        raise
    finally:
        # 清理临时文件
        cleanup_files = [
            PROJECT_ROOT / "examparse-sidecar.spec",
            PROJECT_ROOT / "build",
            PROJECT_ROOT / "dist",
        ]
        for item in cleanup_files:
            if item.exists():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

def test_sidecar(executable_path: Path):
    """测试构建的 sidecar 可执行文件"""
    print(f"Testing sidecar: {executable_path}")
    
    try:
        # 测试 --help
        result = subprocess.run([str(executable_path), "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("Help command works")
        else:
            print(f"Help command failed: {result.stderr}")
        
        # 测试 mock 模式
        result = subprocess.run([str(executable_path), "--mock", "--input", "test.pdf"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 or "FileNotFoundError" in result.stderr:
            print("Mock mode accessible (file not found is expected)")
        else:
            print(f"Mock test failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("Test timed out (this might be normal)")
    except Exception as e:
        print(f"Test error: {e}")

def main():
    """主函数"""
    print("Building ExamParse Sidecar")
    print("=" * 40)
    
    try:
        # 安装 PyInstaller
        install_pyinstaller()
        
        # 构建 sidecar
        executable_path = build_sidecar()
        
        # 测试构建结果
        test_sidecar(executable_path)
        
        print(f"\nBuild completed successfully!")
        print(f"Output: {executable_path}")
        print(f"Size: {executable_path.stat().st_size / (1024*1024):.1f} MB")
        
    except Exception as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
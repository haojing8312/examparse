#!/usr/bin/env python3
"""
ExamParse Desktop 构建验证测试
验证跨平台打包配置和 sidecar 嵌入是否正常工作
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

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
    
    return system, arch

def test_sidecar_executable():
    """测试 sidecar 可执行文件"""
    print("Testing sidecar executable...")
    
    system, _ = get_platform_info()
    sidecar_name = "examparse-sidecar.exe" if system == "windows" else "examparse-sidecar"
    sidecar_path = SIDECAR_DIST_DIR / sidecar_name
    
    if not sidecar_path.exists():
        print(f"Sidecar executable not found: {sidecar_path}")
        return False
    
    # 测试 help 命令
    try:
        result = subprocess.run([str(sidecar_path), "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("Sidecar --help works")
        else:
            print(f"Sidecar --help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing sidecar: {e}")
        return False
    
    # 测试 mock 模式
    try:
        # 创建临时测试文件
        test_dir = PROJECT_ROOT / "tmp"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test.pdf"
        test_file.write_text("test content")
        
        result = subprocess.run([str(sidecar_path), "--mock", "--input", str(test_file)], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and "completed" in result.stdout:
            print("Sidecar mock mode works")
            print(f"   Event count: {result.stdout.count('type')}")
        else:
            print(f"❌ Sidecar mock mode failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing sidecar mock: {e}")
        return False
    
    return True

def test_tauri_config():
    """测试 Tauri 配置"""
    print("Testing Tauri configuration...")
    
    tauri_config = DESKTOP_DIR / "src-tauri" / "tauri.conf.json"
    if not tauri_config.exists():
        print("tauri.conf.json not found")
        return False
    
    import json
    try:
        with open(tauri_config) as f:
            config = json.load(f)
        
        # 检查关键配置
        bundle_config = config.get("bundle", {})
        targets = bundle_config.get("targets", [])
        
        if not targets:
            print("❌ No build targets configured")
            return False
        
        target_names = [t.get("target") for t in targets]
        expected_targets = ["nsis", "msi", "deb", "appimage", "dmg"]
        
        for target in expected_targets:
            if target in target_names:
                print(f"Target configured: {target}")
            else:
                print(f"Target missing: {target}")
        
        # 检查资源和外部二进制文件配置
        resources = bundle_config.get("resources", [])
        external_bin = bundle_config.get("externalBin", [])
        
        if "../../sidecar-dist/*" in resources:
            print("Sidecar resources configured")
        else:
            print("Sidecar resources not configured")
            return False
        
        if "sidecar-dist/examparse-sidecar" in external_bin:
            print("External binary configured")
        else:
            print("External binary not configured")
            return False
        
    except Exception as e:
        print(f"❌ Error reading Tauri config: {e}")
        return False
    
    return True

def test_build_scripts():
    """测试构建脚本"""
    print("Testing build scripts...")
    
    # 检查构建脚本是否存在
    scripts = [
        PROJECT_ROOT / "scripts" / "build_sidecar.py",
        PROJECT_ROOT / "scripts" / "build_desktop.py",
    ]
    
    for script in scripts:
        if script.exists():
            print(f"Build script exists: {script.name}")
        else:
            print(f"Build script missing: {script.name}")
            return False
    
    # 检查 package.json 脚本
    package_json = DESKTOP_DIR / "package.json"
    if package_json.exists():
        import json
        with open(package_json) as f:
            pkg = json.load(f)
        
        scripts_config = pkg.get("scripts", {})
        expected_scripts = ["build:sidecar", "build:full", "clean"]
        
        for script in expected_scripts:
            if script in scripts_config:
                print(f"npm script configured: {script}")
            else:
                print(f"npm script missing: {script}")
                return False
    
    return True

def test_dependencies():
    """测试依赖配置"""
    print("Testing dependencies...")
    
    # 检查 Python 依赖
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        with open(pyproject, encoding='utf-8') as f:
            content = f.read()
        
        if "pyinstaller" in content:
            print("PyInstaller dependency configured")
        else:
            print("PyInstaller dependency missing")
            return False
    
    # 检查前端依赖
    ui_package_json = DESKTOP_DIR / "ui" / "package.json"
    if ui_package_json.exists():
        print("Frontend package.json exists")
    else:
        print("Frontend package.json missing")
        return False
    
    return True

def test_github_actions():
    """测试 GitHub Actions 配置"""
    print("Testing GitHub Actions configuration...")
    
    workflow_file = PROJECT_ROOT / ".github" / "workflows" / "build-desktop.yml"
    if workflow_file.exists():
        print("GitHub Actions workflow configured")
        
        with open(workflow_file) as f:
            content = f.read()
        
        # 检查关键步骤
        if "build_sidecar.py" in content:
            print("Sidecar build step configured")
        else:
            print("Sidecar build step missing")
            return False
        
        if "tauri-apps/tauri-action" in content:
            print("Tauri build action configured")
        else:
            print("Tauri build action missing")
            return False
            
    else:
        print("⚠️  GitHub Actions workflow not found")
    
    return True

def main():
    """运行所有测试"""
    print("ExamParse Desktop Build Verification")
    print("=" * 50)
    
    system, arch = get_platform_info()
    print(f"Platform: {system}/{arch}\n")
    
    tests = [
        ("Sidecar Executable", test_sidecar_executable),
        ("Tauri Configuration", test_tauri_config),
        ("Build Scripts", test_build_scripts),
        ("Dependencies", test_dependencies),
        ("GitHub Actions", test_github_actions),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"Result: {status}")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Build configuration is ready.")
        return 0
    else:
        print("Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
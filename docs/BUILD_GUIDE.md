# ExamParse Desktop 打包构建指南

## 概述

本文档说明如何构建 ExamParse Desktop 应用的跨平台安装包，包括 Python sidecar 和 Tauri 桌面应用的完整打包流程。

## 架构说明

ExamParse Desktop 采用混合架构：
- **前端**: React + Tailwind CSS + Radix UI
- **桌面外壳**: Tauri (Rust)
- **处理引擎**: Python sidecar (打包为独立可执行文件)
- **通信**: JSON 事件流通过 stdout/stdin

## 构建环境要求

### 通用依赖
- Python 3.9+
- Node.js 18+
- Rust (stable channel)
- Git

### 平台特定依赖

#### Windows
- Microsoft Visual Studio Build Tools (含 C++ 桌面开发)
- Windows 10/11 SDK
- WebView2 Runtime

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y \
  libwebkit2gtk-4.1-dev \
  libappindicator3-dev \
  librsvg2-dev \
  patchelf \
  libgtk-3-dev
```

#### macOS
```bash
# 安装 Xcode Command Line Tools
xcode-select --install
```

## 快速开始

### 1. 环境设置
```bash
# 克隆项目
git clone <repository-url>
cd examparse

# 安装 Python 依赖
uv sync --group build

# 安装前端依赖
cd apps/desktop/ui
npm install
cd ../..
```

### 2. 完整构建
```bash
# 方法1: 使用 Python 构建脚本 (推荐)
python scripts/build_desktop.py

# 方法2: 使用 npm 脚本
cd apps/desktop
npm run build:full
```

### 3. 开发模式
```bash
# 启动开发服务器
cd apps/desktop
npm run dev

# 或使用构建脚本
python scripts/build_desktop.py --dev
```

## 构建脚本详解

### 主要脚本

#### `scripts/build_desktop.py`
完整的桌面应用构建脚本，支持以下选项：
- `--clean`: 清理构建目录
- `--dev`: 启动开发模式
- `--sidecar-only`: 只构建 sidecar
- `--frontend-only`: 只构建前端
- `--targets TARGET1 TARGET2`: 指定构建目标

#### `scripts/build_sidecar.py`
专门用于构建 Python sidecar 可执行文件的脚本。

### npm 脚本
```json
{
  "build": "tauri build",
  "build:sidecar": "python ../../scripts/build_sidecar.py",
  "build:full": "python ../../scripts/build_desktop.py",
  "build:dev": "python ../../scripts/build_desktop.py --dev",
  "clean": "python ../../scripts/build_desktop.py --clean"
}
```

## 跨平台打包配置

### 支持的打包格式

#### Windows
- **NSIS**: 现代化安装程序 (.exe)
- **MSI**: Windows Installer 格式 (.msi)

#### Linux  
- **DEB**: Debian/Ubuntu 包 (.deb)
- **AppImage**: 便携应用程序 (.AppImage)

#### macOS
- **DMG**: macOS 磁盘镜像 (.dmg)
- **支持架构**: x86_64 和 Apple Silicon (aarch64)

### 构建目标配置

在 `tauri.conf.json` 中配置：
```json
{
  "bundle": {
    "targets": [
      { "target": "nsis", "arch": ["x86_64"] },
      { "target": "msi", "arch": ["x86_64"] },
      { "target": "deb", "arch": ["x86_64"] },
      { "target": "appimage", "arch": ["x86_64"] },
      { "target": "dmg", "arch": ["x86_64", "aarch64"] }
    ]
  }
}
```

## Sidecar 嵌入机制

### 开发模式 vs 发布模式

#### 开发模式 (`debug_assertions`)
- 使用 `python -m sidecar.main` 调用
- 依赖项目虚拟环境
- 支持热重载和调试

#### 发布模式 (`release`)
- 使用打包的可执行文件
- 无需 Python 环境
- 自包含部署

### 文件路径解析
Tauri 运行时按以下优先级查找 sidecar：
1. `resource_dir/sidecar-dist/examparse-sidecar[.exe]`
2. `app_data_dir/sidecar-dist/examparse-sidecar[.exe]`
3. `./sidecar-dist/examparse-sidecar[.exe]`

## CI/CD 集成

### GitHub Actions

已配置 `.github/workflows/build-desktop.yml` 支持：
- 多平台并行构建 (Windows, Linux, macOS)
- 自动化依赖安装
- 构建产物上传
- Release 自动发布

### 手动触发构建
```bash
# 推送到主分支触发构建
git push origin main

# 创建版本标签触发发布
git tag v1.0.0
git push origin v1.0.0
```

## 故障排除

### 常见问题

#### 1. Python 依赖问题
```bash
# 重新同步依赖
uv sync --group build
```

#### 2. Node.js 依赖问题
```bash
# 清理并重新安装
cd apps/desktop/ui
rm -rf node_modules package-lock.json
npm install
```

#### 3. Rust 编译问题
```bash
# 清理 Rust 缓存
cd apps/desktop/src-tauri
cargo clean
```

#### 4. sidecar 路径问题
检查以下文件是否存在：
- `apps/desktop/src-tauri/sidecar-dist/examparse-sidecar[.exe]`
- 确保文件有执行权限 (Unix 系统)

### 调试技巧

#### 1. 详细构建日志
```bash
python scripts/build_desktop.py --verbose
```

#### 2. 分步构建
```bash
# 只构建 sidecar
python scripts/build_desktop.py --sidecar-only

# 只构建前端
python scripts/build_desktop.py --frontend-only
```

#### 3. 验证 sidecar
```bash
# 测试 sidecar 可执行文件
./apps/desktop/src-tauri/sidecar-dist/examparse-sidecar --help
./apps/desktop/src-tauri/sidecar-dist/examparse-sidecar --mock --input test.pdf
```

## 输出文件说明

### 构建产物位置
```
apps/desktop/src-tauri/target/release/bundle/
├── nsis/                    # Windows NSIS 安装包
├── msi/                     # Windows MSI 安装包  
├── deb/                     # Linux DEB 包
├── appimage/                # Linux AppImage
└── macos/                   # macOS 应用程序包
```

### 文件命名规则
- Windows: `ExamParse Desktop_0.1.0_x64_en-US.msi`
- Linux: `examparse-desktop_0.1.0_amd64.deb`
- macOS: `ExamParse Desktop.app.tar.gz`

## 版本管理

### 版本号配置
版本号在以下文件中保持一致：
- `apps/desktop/src-tauri/tauri.conf.json`
- `apps/desktop/src-tauri/Cargo.toml`
- `apps/desktop/package.json`

### 发布流程
1. 更新版本号
2. 更新 CHANGELOG
3. 创建 Git 标签
4. 推送触发 CI/CD
5. 验证发布产物

## 安全考虑

### 代码签名
- Windows: 配置证书指纹
- macOS: 配置开发者身份和公证
- 生产环境建议启用代码签名

### 权限控制
- 应用只请求必要的系统权限
- 文件访问限制在用户选择的目录
- API 密钥通过系统钥匙串存储
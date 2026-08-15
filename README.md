# Vcs Tool

> 一个轻量的 Windows 桌面工具，把日常的 Git / SVN 操作（拉取、提交推送、查看日志、冲突解决、自定义脚本）收进一个项目树界面，配合系统托盘常驻与全局快捷键，做到「一键到位」。

基于 PyQt5 构建，开箱即用，无需命令行基础。

> 说明：项目显示名为 **Vcs Tool**，代码库 / exe / 仓库命名为 **VcsTool**（无空格）。

---

## 目录

- [功能特性](#功能特性)
- [下载安装](#下载安装)
- [快速上手](#快速上手)
- [配置文件说明](#配置文件说明)
- [从源码构建](#从源码构建)
- [发布流程（自动出 exe 并供下载）](#发布流程自动出-exe-并供下载)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [已知限制](#已知限制)
- [许可证](#许可证)

---

## 功能特性

- **项目树管理**：按项目分组管理多条指令，可折叠展开，状态自动记忆。
- **多版本库**：同时支持 Git 与 SVN，自动识别常用操作。
- **一键操作**
  - 拉取（`git pull` / `svn update`）
  - 提交并推送（Git：`add` → `commit` → `push`；SVN：`add` → `commit`）
  - 查看日志（最近 50 条）
  - 自定义命令（`.bat` / `.ps1` / `.exe`，可带参数）
- **分支支持**：Git 指令可指定分支，留空则使用当前分支。
- **冲突解决**：拉取/提交时自动检测冲突，弹出本地 / 远端内容对比窗口，支持「使用本地版本」「使用远端版本」「手动编辑后标记已解决」。
- **全局快捷键**：默认 `Ctrl+Alt+V` 呼出/隐藏主窗口，可在配置中修改或按键捕获。
- **系统托盘常驻**：关闭窗口即最小化到托盘，不干扰日常工作。
- **后台执行**：所有命令在后台线程执行，界面不卡顿。

---

## 下载安装

### 方式一：直接下载 exe（推荐）

前往项目的 [Releases 页面](https://github.com/Lendo527/VcsTool/releases)，下载最新版的 `VcsTool.exe`，双击即可运行，无需安装。

> 首次运行时 Windows SmartScreen 可能提示「未识别的应用」，点击「更多信息 → 仍要运行」即可。

### 运行环境要求

- 操作系统：Windows 10 / 11（64 位）
- 已安装 Git（[git-scm.com](https://git-scm.com/)）和/或 SVN（[tortoisesvn.org](https://tortoisesvn.net/)），并加入系统 `PATH`
- 全局快捷键功能需要以当前用户身份运行（普通用户即可）

---

## 快速上手

1. 双击 `VcsTool.exe` 启动，程序自动驻留系统托盘。
2. 按下 `Ctrl+Alt+V`（或双击托盘图标）呼出主窗口。
3. 点击工具栏「配置」：
   - **新增项目**：填写项目名称、选择版本库类型（Git / SVN）。
   - **新增指令**：填写指令名称、选择文件夹路径、操作类型；Git 可指定分支；自定义命令可选脚本类型与脚本/程序路径。
4. 回到主窗口，**双击**左侧指令即可执行，输出显示在右侧。
5. 提交并推送时如检测到冲突，会弹出冲突解决窗口，逐个解决后点击「继续提交」。

---

## 配置文件说明

配置以 JSON 形式保存在：

```
%APPDATA%\VcsTool\config.json
```

结构示例：

```json
{
  "hotkey": "ctrl+alt+v",
  "projects": [
    {
      "id": "唯一ID",
      "name": "我的项目",
      "vcs_type": "git",
      "expanded": true,
      "commands": [
        {
          "id": "唯一ID",
          "name": "拉取主分支",
          "path": "D:\\code\\my-project",
          "action": "pull",
          "branch": "main",
          "shell": "cmd",
          "script": ""
        }
      ]
    }
  ]
}
```

字段含义：

| 字段 | 说明 |
| --- | --- |
| `hotkey` | 全局呼出快捷键，如 `ctrl+alt+v`、`win+g` |
| `projects[].vcs_type` | `git` 或 `svn` |
| `commands[].action` | `pull` / `commit_push` / `log` / `script` |
| `commands[].branch` | Git 分支，留空使用当前分支 |
| `commands[].shell` | 自定义命令类型：`cmd` / `powershell` / `exe` |
| `commands[].script` | 自定义命令的脚本/程序路径（exe 可含参数） |

> 配置文件含本地路径，已默认加入 `.gitignore`，不会上传到仓库。

---

## 从源码构建

### 本地构建（Windows）

前置：已安装 Python 3.9+。

```bat
git clone https://github.com/Lendo527/VcsTool.git
cd VcsTool
build.bat
```

`build.bat` 会自动安装依赖、调用 PyInstaller 生成单文件 exe，输出在 `dist\VcsTool.exe`。

### 手动命令

```bat
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --onefile --windowed ^
  --name "VcsTool" ^
  --icon "icon.ico" ^
  --add-data "icon.ico;." ^
  --collect-all keyboard ^
  main.py
```

### 依赖

见 [requirements.txt](requirements.txt)：PyQt5、keyboard、Pillow（仅用于图标转换）。

---

## 发布流程（自动出 exe 并供下载）

项目内置 GitHub Actions 打包管线（[.github/workflows/build.yml](.github/workflows/build.yml)）：

1. **打 tag 触发**：推送 `v` 开头的标签即可自动在 Windows 环境构建并发布 Release。
   ```bat
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. 构建完成后，会在 GitHub **Releases** 页面生成一个新版本，附带可直接下载的 `VcsTool.exe`。
3. 也可在仓库 **Actions** 标签页手动 `Run workflow` 触发构建，产物会作为 workflow artifact 提供下载（不会创建 Release）。

---

## 项目结构

```
VcsTool/
├── main.py              # 程序入口
├── main_window.py       # 主窗口：项目树 / 输出区 / 托盘 / 后台执行
├── config_manager.py    # 配置持久化（项目、指令、快捷键）
├── vcs_operations.py    # Git/SVN 操作封装（拉取/提交/日志/冲突）
├── hotkey_manager.py    # 全局快捷键（keyboard 库 + Qt 信号）
├── dialogs.py           # 配置/提交/冲突解决等对话框
├── resources.py         # 资源路径处理（兼容 PyInstaller）
├── convert_icon.py      # 图标转换工具（jpg -> 多尺寸 ico）
├── icon.ico / icon.jpg  # 应用图标
├── build.bat            # 本地打包脚本
├── requirements.txt     # Python 依赖
└── .github/workflows/   # CI 打包与发布管线
```

---

## 技术栈

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — GUI 框架
- [keyboard](https://github.com/boppreh/keyboard) — 系统级全局快捷键
- [Pillow](https://python-pillow.org/) — 图标格式转换
- [PyInstaller](https://pyinstaller.org/) — 打包为单文件 exe
- [GitHub Actions](https://docs.github.com/actions) — 自动化构建与发布

---

## 已知限制

- 仅支持 Windows（依赖托盘、`cmd`、`os.startfile` 等 Windows 特性）。
- Git 命令输出默认按 UTF-8 解码；若本机 Git 输出非 UTF-8（如部分中文 Windows 的 GBK），可能出现少量乱码，可执行 `git config --global core.quotepath false` 缓解。
- 全局快捷键由 `keyboard` 库实现，个别组合键可能被系统或其他软件占用而无法注册，请在配置中更换。
- 「手动解决」策略下，标记已解决前请确认文件内冲突标记（`<<<<<<<` 等）已清除。

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源，可自由使用、修改与分发。

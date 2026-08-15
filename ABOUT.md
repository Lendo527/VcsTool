# 关于 Vcs Tool

## 项目简介

**Vcs Tool** 是一款面向 Windows 桌面用户的 Git / SVN 便捷操作工具。

它把分散在命令行里的版本库操作（拉取、提交推送、查看日志、解决冲突、运行自定义脚本）整合进一个可视化的项目树界面，配合系统托盘常驻与全局快捷键，让日常的版本库维护做到「一键到位」，无需记忆命令。

> 显示名为 **Vcs Tool**，代码库 / exe / 仓库名为 **VcsTool**（无空格）。

## 基本信息

| 项目 | 内容 |
| --- | --- |
| 名称 | Vcs Tool |
| 代码库名 | VcsTool |
| 当前版本 | 1.0.0 |
| 类型 | Windows 桌面工具（单文件 exe） |
| 适用平台 | Windows 10 / 11（64 位） |
| 运行依赖 | 已安装 Git 和/或 SVN 并加入系统 PATH |
| 技术栈 | Python · PyQt5 · keyboard · Pillow |
| 打包工具 | PyInstaller |
| 仓库 | [Lendo527/VcsTool](https://github.com/Lendo527/VcsTool) |
| 许可证 | MIT |

## 核心能力

- 项目树管理：按项目分组管理多条指令，折叠状态自动记忆。
- 多版本库：同时支持 Git 与 SVN。
- 一键操作：拉取 / 提交并推送 / 查看日志 / 自定义命令（bat·ps1·exe）。
- 分支支持：Git 指令可指定分支，留空使用当前分支。
- 冲突解决：自动检测冲突，本地/远端内容对比，支持本地/远端/手动三种解决策略。
- 全局快捷键：默认 `Ctrl+Alt+V` 呼出/隐藏，可自定义。
- 系统托盘常驻：关闭即最小化，不打扰日常工作。
- 后台执行：所有命令在后台线程运行，界面始终流畅。

## 配置位置

```
%APPDATA%\VcsTool\config.json
```

配置含本地路径，请勿分享给他人；如需迁移，复制该文件到新机器同目录即可。

## 下载

前往 [Releases](https://github.com/Lendo527/VcsTool/releases) 获取最新版 `VcsTool.exe`。

## 反馈与贡献

- 问题反馈：请在仓库提交 Issue。
- 代码贡献：欢迎提交 Pull Request。

## 致谢

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — GUI 框架
- [keyboard](https://github.com/boppreh/keyboard) — 全局快捷键
- [PyInstaller](https://pyinstaller.org/) — 打包工具
- [Pillow](https://python-pillow.org/) — 图像处理

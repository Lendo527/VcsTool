# 关于 Vcs Tool

**Vcs Tool** 是一款 Windows 桌面下的 Git / SVN 便捷操作工具。

把散落在命令行里的版本库操作收进一个可视化项目树，配合系统托盘常驻与全局快捷键，让日常的拉取、提交推送、查日志、解决冲突做到「一键到位」，无需记命令。

## 一句话

> 不开终端，也能把 Git / SVN 的事办了。

## 特性

- 项目树管理，分组维护多条指令，折叠状态记忆
- Git / SVN 双支持
- 拉取 · 提交并推送 · 查看日志 · 自定义命令（bat / ps1 / exe）
- Git 指令可指定分支，留空走当前分支
- 冲突检测与本地 / 远端对比解决
- 全局快捷键呼出（默认 `Ctrl+Alt+V`）
- 系统托盘常驻，后台执行不卡界面

## 基本信息

| 项 | 值 |
| --- | --- |
| 版本 | 1.0.0 |
| 平台 | Windows 10 / 11（64 位） |
| 依赖 | Git 和/或 SVN（加入 PATH） |
| 技术栈 | Python · PyQt5 · keyboard · Pillow |
| 打包 | PyInstaller |
| 仓库 | [Lendo527/VcsTool](https://github.com/Lendo527/VcsTool) |
| 下载 | [Releases](https://github.com/Lendo527/VcsTool/releases) |
| 许可证 | [MIT](LICENSE) |

> 显示名 **Vcs Tool**，代码库 / exe / 仓库名 **VcsTool**（无空格）。

## 配置

```
%APPDATA%\VcsTool\config.json
```

含本地路径，请勿外传；迁移时复制该文件到新机同目录即可。

## 反馈

Issue / PR 欢迎至 [Lendo527/VcsTool](https://github.com/Lendo527/VcsTool)。

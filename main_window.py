# -*- coding: utf-8 -*-
"""主窗口：项目树（可折叠）+ 输出区 + 系统托盘 + 快捷键呼出"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPlainTextEdit, QToolBar, QAction, QStatusBar, QSystemTrayIcon, QMenu,
    QMessageBox, QSplitter, QLabel, QHeaderView, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

from config_manager import ConfigManager
from vcs_operations import VcsOperations, VcsResult
from hotkey_manager import HotkeyManager
from dialogs import ConfigDialog, CommitDialog, ConflictDialog
from resources import icon_path

ACTION_LABEL = {"pull": "拉取", "commit_push": "提交并推送", "log": "查看日志",
                "script": "自定义命令"}


class CommandWorker(QThread):
    """后台执行单个 VCS 命令，避免界面卡死"""
    done = pyqtSignal(object)

    def __init__(self, fn, *args):
        super().__init__()
        self._fn = fn
        self._args = args

    def run(self):
        try:
            res = self._fn(*self._args)
        except Exception as e:
            res = VcsResult(success=False, error=str(e))
        self.done.emit(res)


class MainWindow(QMainWindow):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.vcs = VcsOperations()
        self._worker = None
        self._pending = None   # (project, cmd, message) 提交流程中间态
        self._busy = False

        self.setWindowTitle("VCSTool")
        self.resize(1020, 680)
        self.setWindowIcon(QIcon(icon_path()))

        self._build_toolbar()
        self._build_central()
        self._build_statusbar()
        self._build_tray()

        self.hotkey = HotkeyManager()
        self.hotkey.triggered.connect(self._toggle_visibility)
        self._register_hotkey()

        self.refresh_tree()

    # ============================== 界面构建 ==============================
    def _build_toolbar(self):
        tb = self.addToolBar("主工具栏")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        a_cfg = QAction("配置", self); a_cfg.triggered.connect(self._open_config)
        a_refresh = QAction("刷新", self); a_refresh.triggered.connect(self.refresh_tree)
        a_run = QAction("执行选中指令", self); a_run.triggered.connect(self._run_selected)
        a_hide = QAction("最小化到托盘", self); a_hide.triggered.connect(self.hide)
        tb.addAction(a_cfg)
        tb.addAction(a_refresh)
        tb.addAction(a_run)
        tb.addSeparator()
        tb.addAction(a_hide)

    def _build_central(self):
        central = QWidget()
        box = QVBoxLayout(central)
        box.setContentsMargins(6, 6, 6, 6)
        splitter = QSplitter(Qt.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "操作", "路径"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tree.setUniformRowHeights(True)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.itemExpanded.connect(lambda it: self._on_expand(it, True))
        self.tree.itemCollapsed.connect(lambda it: self._on_expand(it, False))
        splitter.addWidget(self.tree)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("命令输出将显示在此处。双击左侧指令执行...")
        splitter.addWidget(self.output)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        box.addWidget(splitter)
        self.setCentralWidget(central)

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_label = QLabel("就绪")
        sb.addWidget(self.status_label)

    def _build_tray(self):
        self.tray = QSystemTrayIcon(QIcon(icon_path()), self)
        self.tray.setToolTip("VCSTool — Git/SVN 便捷工具")
        menu = QMenu()
        menu.addAction("显示主窗口").triggered.connect(self._show_and_raise)
        menu.addAction("配置").triggered.connect(self._open_config)
        menu.addAction("关于 VCSTool").triggered.connect(self._show_about)
        menu.addSeparator()
        menu.addAction("退出").triggered.connect(self._real_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    # ============================== 快捷键 ==============================
    def _register_hotkey(self):
        if self.hotkey.register(self.config.get_hotkey()):
            self._set_status(f"就绪 | 快捷键：{self.config.get_hotkey()}（呼出/隐藏）")
        else:
            self._set_status("快捷键注册失败，请在配置中修改")

    def _toggle_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self._show_and_raise()

    def _show_and_raise(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ============================== 项目树 ==============================
    def refresh_tree(self):
        self.tree.clear()
        for p in self.config.projects:
            top = QTreeWidgetItem([f"[{p['vcs_type'].upper()}] {p['name']}", "", ""])
            top.setData(0, Qt.UserRole, ("project", p["id"]))
            f = top.font(0); f.setBold(True); top.setFont(0, f)
            for c in p["commands"]:
                child = QTreeWidgetItem([
                    c["name"],
                    ACTION_LABEL.get(c["action"], c["action"]),
                    c["path"],
                ])
                child.setData(0, Qt.UserRole, ("command", p["id"], c["id"]))
                top.addChild(child)
            self.tree.addTopLevelItem(top)
            top.setExpanded(p.get("expanded", True))

    def _on_expand(self, item, expanded):
        data = item.data(0, Qt.UserRole)
        if isinstance(data, tuple) and data and data[0] == "project":
            self.config.set_expanded(data[1], expanded)

    def _selected_command(self):
        it = self.tree.currentItem()
        if not it:
            return None, None
        data = it.data(0, Qt.UserRole)
        if isinstance(data, tuple) and data and data[0] == "command":
            pid, cid = data[1], data[2]
            p = self.config.get_project(pid)
            if not p:
                return None, None
            cmd = next((c for c in p["commands"] if c["id"] == cid), None)
            return p, cmd
        return None, None

    def _on_double_click(self, it, col):
        p, cmd = self._selected_command()
        if cmd:
            self._run_command(p, cmd)

    def _run_selected(self):
        p, cmd = self._selected_command()
        if not cmd:
            QMessageBox.information(self, "提示", "请先在左侧选择一条指令")
            return
        self._run_command(p, cmd)

    # ============================== 执行 ==============================
    def _run_command(self, project, cmd):
        if self._busy:
            QMessageBox.information(self, "提示", "有任务正在执行，请稍候")
            return
        if not os.path.isdir(cmd["path"]):
            QMessageBox.warning(self, "路径无效", f"路径不存在：\n{cmd['path']}")
            return
        action = cmd["action"]
        if action == "pull":
            self._exec_async(self.vcs.pull,
                             (cmd["path"], project["vcs_type"], cmd.get("branch", "")),
                             self._on_simple_done, "正在拉取...")
        elif action == "log":
            self._exec_async(self.vcs.log, (cmd["path"], project["vcs_type"]),
                             self._on_simple_done, "正在获取日志...")
        elif action == "commit_push":
            self._start_commit(project, cmd)
        elif action == "script":
            shell = cmd.get("shell", "cmd")
            target = cmd.get("script", "")
            self._exec_async(self.vcs.run_script, (cmd["path"], shell, target),
                             self._on_simple_done, "正在执行自定义命令...")

    def _exec_async(self, fn, args, done_cb, busy_msg):
        self._busy = True
        self._set_status(busy_msg)
        w = CommandWorker(fn, *args)
        w.done.connect(done_cb)
        w.finished.connect(w.deleteLater)  # 线程结束后自动回收，避免对象堆积
        self._worker = w
        w.start()

    def _on_simple_done(self, res: VcsResult):
        self._busy = False
        self._append_output(res.output or res.error or "(无输出)")
        self._set_status("执行完成" if res.success else "执行完成（有警告/错误）")

    # ---------- 提交流程：拉取 -> 冲突解决 -> 提交推送 ----------
    def _start_commit(self, project, cmd):
        dlg = CommitDialog(self)
        if dlg.exec_() != CommitDialog.Accepted:
            return
        msg = dlg.message()
        if not msg:
            QMessageBox.warning(self, "提示", "提交日志不能为空")
            return
        self._pending = (project, cmd, msg)
        self._append_output(f"\n==== {cmd['name']}：开始提交流程 ====")
        self._exec_async(self.vcs.prepare_commit,
                         (cmd["path"], project["vcs_type"], cmd.get("branch", "")),
                         self._on_prepared, "正在拉取最新代码...")

    def _on_prepared(self, res: VcsResult):
        self._append_output("--- 拉取结果 ---\n" + (res.output or res.error or "(无输出)"))
        project, cmd, msg = self._pending
        if res.conflicts:
            self._busy = False
            self._append_output(f"检测到 {len(res.conflicts)} 个冲突文件，等待解决...")
            dlg = ConflictDialog(cmd["path"], project["vcs_type"], res.conflicts, self.vcs, self)
            if dlg.exec_() != ConflictDialog.Accepted:
                self._append_output("用户取消提交（仍有未解决冲突）")
                self._set_status("已取消提交")
                self._pending = None
                return
            self._append_output("所有冲突已解决，继续提交...")
        else:
            self._append_output("无冲突，继续提交...")
        self._do_finish()

    def _do_finish(self):
        project, cmd, msg = self._pending
        self._exec_async(self.vcs.finish_commit,
                         (cmd["path"], project["vcs_type"], msg, cmd.get("branch", "")),
                         self._on_committed, "正在提交并推送...")

    def _on_committed(self, res: VcsResult):
        self._busy = False
        self._append_output("--- 提交结果 ---\n" + (res.output or res.error or "(无输出)"))
        self._pending = None
        self._set_status("提交并推送成功" if res.success else "提交完成（请查看输出）")

    # ============================== 辅助 ==============================
    def _append_output(self, text):
        self.output.appendPlainText(text)

    def _set_status(self, text):
        self.status_label.setText(text)

    # ============================== 配置 ==============================
    def _open_config(self):
        old_hk = self.config.get_hotkey()
        ConfigDialog(self.config, self).exec_()
        self.refresh_tree()
        if self.config.get_hotkey() != old_hk:
            self._register_hotkey()

    def _show_about(self):
        QMessageBox.about(
            self, "关于 VCSTool",
            "<h3>VCSTool</h3>"
            "<p>Git / SVN 便捷操作工具</p>"
            "<p>版本 1.0.0</p>"
            "<p>基于 PyQt5 构建：项目树管理、一键拉取/提交推送、冲突解决、"
            "自定义脚本执行、全局快捷键呼出与系统托盘常驻。</p>"
            "<p>配置文件：%APPDATA%\\VCSTool\\config.json</p>"
        )

    # ============================== 托盘 / 关闭 ==============================
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_visibility()

    def closeEvent(self, e):
        if self.tray.isVisible():
            e.ignore()
            self.hide()
            self.tray.showMessage("VCSTool",
                                  "程序已最小化到托盘，按快捷键或双击托盘图标恢复。")
        else:
            super().closeEvent(e)

    def _real_quit(self):
        self.tray.hide()
        self.hotkey.unregister()
        QApplication.quit()

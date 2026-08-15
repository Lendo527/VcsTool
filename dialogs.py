# -*- coding: utf-8 -*-
"""对话框：配置（项目/指令）、提交日志、冲突解决"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QTableWidget,
    QTableWidgetItem, QHeaderView, QPlainTextEdit, QAbstractItemView,
    QMessageBox, QFileDialog, QSplitter, QWidget, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from config_manager import ConfigManager
from vcs_operations import VcsOperations


class _HotkeyCaptureWorker(QThread):
    """后台捕获按键组合，避免 keyboard.read_hotkey() 阻塞主线程界面"""
    captured = pyqtSignal(str)
    failed = pyqtSignal(str)

    def run(self):
        try:
            import keyboard
            rec = keyboard.read_hotkey()
            self.captured.emit(rec)
        except Exception as e:
            self.failed.emit(str(e))


# ============================== 指令编辑 ==============================
class CommandEditDialog(QDialog):
    def __init__(self, parent=None, name="", path="", action="pull", branch="",
                 vcs_type="git", shell="cmd", script=""):
        super().__init__(parent)
        self.setWindowTitle("指令编辑")
        self.resize(600, 420)
        form = QFormLayout(self)

        self.name_edit = QLineEdit(name)

        self.path_edit = QLineEdit(path)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)
        path_w = QWidget()
        path_w.setLayout(path_row)

        self.action_combo = QComboBox()
        commit_label = "提交并推送" if vcs_type == "git" else "提交"
        self.action_combo.addItem("拉取", "pull")
        self.action_combo.addItem(commit_label, "commit_push")
        self.action_combo.addItem("查看日志", "log")
        self.action_combo.addItem("自定义命令", "script")
        for i in range(self.action_combo.count()):
            if self.action_combo.itemData(i) == action:
                self.action_combo.setCurrentIndex(i)
                break
        self.action_combo.currentIndexChanged.connect(self._on_action_changed)

        self.branch_edit = QLineEdit(branch)
        if vcs_type == "git":
            self.branch_edit.setPlaceholderText("可选，留空使用当前分支")
        else:
            self.branch_edit.setPlaceholderText("SVN 无需填写")
            self.branch_edit.setEnabled(False)

        # ---- 自定义命令相关控件 ----
        self.shell_combo = QComboBox()
        self.shell_combo.addItem("批处理 (bat)", "cmd")
        self.shell_combo.addItem("PowerShell (ps1)", "powershell")
        self.shell_combo.addItem("可执行程序 (exe)", "exe")
        for i in range(self.shell_combo.count()):
            if self.shell_combo.itemData(i) == shell:
                self.shell_combo.setCurrentIndex(i)
                break
        self.shell_combo.currentIndexChanged.connect(self._on_shell_changed)

        self.target_edit = QLineEdit(script)
        self.target_edit.setPlaceholderText("脚本/程序文件路径（exe 可含参数）")
        target_browse = QPushButton("浏览...")
        target_browse.clicked.connect(self._browse_target)
        target_row = QHBoxLayout()
        target_row.addWidget(self.target_edit)
        target_row.addWidget(target_browse)
        self._target_w = QWidget()
        self._target_w.setLayout(target_row)

        form.addRow("指令名称:", self.name_edit)
        form.addRow("文件夹路径:", path_w)
        form.addRow("操作类型:", self.action_combo)
        if vcs_type == "git":
            self._branch_row_label = QLabel("分支:")
            form.addRow(self._branch_row_label, self.branch_edit)
        else:
            self._branch_row_label = None
        self._shell_row_label = QLabel("脚本类型:")
        form.addRow(self._shell_row_label, self.shell_combo)
        self._target_row_label = QLabel("脚本/程序:")
        form.addRow(self._target_row_label, self._target_w)

        btns = QHBoxLayout()
        ok = QPushButton("确定")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        btns.addStretch(1)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        form.addRow(btns)

        self._on_action_changed()

    def _on_action_changed(self):
        is_script = self.action_combo.currentData() == "script"
        # 自定义命令时显示脚本相关控件，隐藏分支
        self._shell_row_label.setVisible(is_script)
        self.shell_combo.setVisible(is_script)
        self._target_row_label.setVisible(is_script)
        self._target_w.setVisible(is_script)
        # 分支行显隐
        if self._branch_row_label is not None:
            self._branch_row_label.setVisible(not is_script)
            self.branch_edit.setVisible(not is_script)

    def _on_shell_changed(self):
        sh = self.shell_combo.currentData()
        if sh == "exe":
            self.target_edit.setPlaceholderText("exe 路径，可含参数，如  build.exe --release")
        elif sh == "powershell":
            self.target_edit.setPlaceholderText(".ps1 脚本文件路径")
        else:
            self.target_edit.setPlaceholderText(".bat 批处理文件路径")

    def _browse_target(self):
        sh = self.shell_combo.currentData()
        if sh == "exe":
            f, _ = QFileDialog.getOpenFileName(self, "选择可执行程序", "",
                                               "程序 (*.exe);;所有文件 (*)")
        elif sh == "powershell":
            f, _ = QFileDialog.getOpenFileName(self, "选择 PowerShell 脚本", "",
                                               "PowerShell (*.ps1);;所有文件 (*)")
        else:
            f, _ = QFileDialog.getOpenFileName(self, "选择批处理文件", "",
                                               "批处理 (*.bat *.cmd);;所有文件 (*)")
        if f:
            self.target_edit.setText(f)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if d:
            self.path_edit.setText(d)

    def values(self):
        return (self.name_edit.text().strip(),
                self.path_edit.text().strip(),
                self.action_combo.currentData(),
                self.branch_edit.text().strip(),
                self.shell_combo.currentData(),
                self.target_edit.text().strip())


# ============================== 配置对话框 ==============================
class ConfigDialog(QDialog):
    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("配置")
        self.resize(840, 580)

        root = QVBoxLayout(self)

        # 快捷键设置
        hk_box = QGroupBox("全局呼出快捷键")
        hk_form = QFormLayout(hk_box)
        self.hk_edit = QLineEdit(config.get_hotkey())
        self.hk_edit.setPlaceholderText("例如: ctrl+alt+v")
        hk_capture = QPushButton("按下按键捕获")
        hk_capture.clicked.connect(self._capture_hotkey)
        hk_row = QHBoxLayout()
        hk_row.addWidget(self.hk_edit)
        hk_row.addWidget(hk_capture)
        hk_w = QWidget()
        hk_w.setLayout(hk_row)
        hk_form.addRow("快捷键:", hk_w)
        hk_form.addRow(QLabel("提示：使用键盘按键名组合，如 ctrl+alt+v / win+g"))
        root.addWidget(hk_box)

        # 主体：左项目列表 + 右详情
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        lbox = QVBoxLayout(left)
        lbox.addWidget(QLabel("项目列表"))
        self.proj_list = QListWidget()
        self.proj_list.currentItemChanged.connect(self._on_proj_changed)
        lbox.addWidget(self.proj_list)
        pbtns = QHBoxLayout()
        p_add = QPushButton("新增项目")
        p_add.clicked.connect(self._add_project)
        p_del = QPushButton("删除项目")
        p_del.clicked.connect(self._del_project)
        pbtns.addWidget(p_add)
        pbtns.addWidget(p_del)
        lbox.addLayout(pbtns)
        splitter.addWidget(left)

        right = QWidget()
        rbox = QVBoxLayout(right)
        self.name_edit = QLineEdit()
        self.vcs_combo = QComboBox()
        self.vcs_combo.addItem("Git", "git")
        self.vcs_combo.addItem("SVN", "svn")
        rform = QFormLayout()
        rform.addRow("项目名称:", self.name_edit)
        rform.addRow("版本库类型:", self.vcs_combo)
        rbox.addLayout(rform)
        apply_btn = QPushButton("应用项目修改")
        apply_btn.clicked.connect(self._apply_project)
        rbox.addWidget(apply_btn)

        rbox.addWidget(QLabel("指令列表"))
        self.cmd_table = QTableWidget(0, 4)
        self.cmd_table.setHorizontalHeaderLabels(["指令名称", "路径", "操作", "分支"])
        self.cmd_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.cmd_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cmd_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        rbox.addWidget(self.cmd_table)
        cbtns = QHBoxLayout()
        c_add = QPushButton("新增指令")
        c_add.clicked.connect(self._add_command)
        c_edit = QPushButton("编辑指令")
        c_edit.clicked.connect(self._edit_command)
        c_del = QPushButton("删除指令")
        c_del.clicked.connect(self._del_command)
        cbtns.addWidget(c_add)
        cbtns.addWidget(c_edit)
        cbtns.addWidget(c_del)
        rbox.addLayout(cbtns)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, 1)

        # 底部
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        ok = QPushButton("完成")
        ok.clicked.connect(self._finish)
        bottom.addWidget(ok)
        root.addLayout(bottom)

        self._current_pid = None
        self._refresh_projects()

    # ---- 快捷键捕获 ----
    def _capture_hotkey(self):
        QMessageBox.information(self, "按键捕获",
                                "点击确定后，请按下你想要的快捷键组合。")
        self._hk_worker = _HotkeyCaptureWorker(self)
        self._hk_worker.captured.connect(self._on_hotkey_captured)
        self._hk_worker.failed.connect(
            lambda e: QMessageBox.warning(self, "捕获失败", e))
        self._hk_worker.finished.connect(self._hk_worker.deleteLater)
        self._hk_worker.start()

    def _on_hotkey_captured(self, rec):
        self.hk_edit.setText(rec)

    # ---- 项目 ----
    def _refresh_projects(self):
        self.proj_list.clear()
        for p in self.config.projects:
            it = QListWidgetItem(f"[{p['vcs_type'].upper()}] {p['name']}")
            it.setData(Qt.UserRole, p["id"])
            self.proj_list.addItem(it)

    def _on_proj_changed(self, cur, prev):
        if cur is None:
            return
        pid = cur.data(Qt.UserRole)
        p = self.config.get_project(pid)
        if not p:
            return
        self._current_pid = pid
        self.name_edit.setText(p["name"])
        for i in range(self.vcs_combo.count()):
            if self.vcs_combo.itemData(i) == p["vcs_type"]:
                self.vcs_combo.setCurrentIndex(i)
                break
        self._refresh_commands(p)

    def _add_project(self):
        p = self.config.add_project("新项目", "git")
        self._refresh_projects()
        for i in range(self.proj_list.count()):
            if self.proj_list.item(i).data(Qt.UserRole) == p["id"]:
                self.proj_list.setCurrentRow(i)
                break

    def _del_project(self):
        if not self._current_pid:
            return
        if QMessageBox.question(self, "确认", "确定删除该项目及其所有指令？") != QMessageBox.Yes:
            return
        self.config.remove_project(self._current_pid)
        self._current_pid = None
        self._refresh_projects()
        self.cmd_table.setRowCount(0)
        self.name_edit.clear()

    def _apply_project(self):
        if not self._current_pid:
            return
        self.config.update_project(
            self._current_pid,
            name=self.name_edit.text().strip() or "未命名",
            vcs_type=self.vcs_combo.currentData(),
        )
        self._refresh_projects()
        # 重新选中
        for i in range(self.proj_list.count()):
            if self.proj_list.item(i).data(Qt.UserRole) == self._current_pid:
                self.proj_list.setCurrentRow(i)
                break

    # ---- 指令 ----
    def _current_project(self):
        if not self._current_pid:
            return None
        return self.config.get_project(self._current_pid)

    def _refresh_commands(self, p):
        self.cmd_table.setRowCount(0)
        action_label = {"pull": "拉取", "commit_push": "提交并推送" if p["vcs_type"] == "git" else "提交",
                        "log": "查看日志", "script": "自定义命令"}
        shell_label = {"cmd": "bat", "powershell": "ps1", "exe": "exe"}
        for c in p["commands"]:
            r = self.cmd_table.rowCount()
            self.cmd_table.insertRow(r)
            self.cmd_table.setItem(r, 0, QTableWidgetItem(c["name"]))
            self.cmd_table.setItem(r, 1, QTableWidgetItem(c["path"]))
            self.cmd_table.setItem(r, 2, QTableWidgetItem(action_label.get(c["action"], c["action"])))
            # 第4列：自定义命令显示脚本类型，否则显示分支
            if c["action"] == "script":
                col4 = shell_label.get(c.get("shell", "cmd"), c.get("shell", "cmd"))
            else:
                col4 = c.get("branch", "")
            self.cmd_table.setItem(r, 3, QTableWidgetItem(col4))
            self.cmd_table.item(r, 0).setData(Qt.UserRole, c["id"])

    def _add_command(self):
        p = self._current_project()
        if not p:
            QMessageBox.information(self, "提示", "请先选择一个项目")
            return
        dlg = CommandEditDialog(self, vcs_type=p["vcs_type"])
        if dlg.exec_() != QDialog.Accepted:
            return
        name, path, action, branch, shell, script = dlg.values()
        if not name or not path:
            QMessageBox.warning(self, "提示", "名称和路径不能为空")
            return
        if action == "script" and not script.strip():
            QMessageBox.warning(self, "提示", "自定义命令的脚本/命令不能为空")
            return
        self.config.add_command(p["id"], name, path, action, branch, shell, script)
        self._refresh_commands(p)

    def _edit_command(self):
        p = self._current_project()
        if not p:
            return
        row = self.cmd_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择一条指令")
            return
        cid = self.cmd_table.item(row, 0).data(Qt.UserRole)
        cmd = next((c for c in p["commands"] if c["id"] == cid), None)
        if not cmd:
            return
        dlg = CommandEditDialog(self, name=cmd["name"], path=cmd["path"],
                                action=cmd["action"], branch=cmd.get("branch", ""),
                                vcs_type=p["vcs_type"],
                                shell=cmd.get("shell", "cmd"),
                                script=cmd.get("script", ""))
        if dlg.exec_() != QDialog.Accepted:
            return
        name, path, action, branch, shell, script = dlg.values()
        self.config.update_command(p["id"], cid, name=name, path=path,
                                   action=action, branch=branch,
                                   shell=shell, script=script)
        self._refresh_commands(p)

    def _del_command(self):
        p = self._current_project()
        if not p:
            return
        row = self.cmd_table.currentRow()
        if row < 0:
            return
        cid = self.cmd_table.item(row, 0).data(Qt.UserRole)
        self.config.remove_command(p["id"], cid)
        self._refresh_commands(p)

    def _finish(self):
        hk = self.hk_edit.text().strip()
        if hk:
            self.config.set_hotkey(hk)
        self.accept()


# ============================== 提交日志对话框 ==============================
class CommitDialog(QDialog):
    def __init__(self, parent=None, prefill=""):
        super().__init__(parent)
        self.setWindowTitle("填写提交日志")
        self.resize(520, 320)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("请输入提交日志："))
        self.edit = QPlainTextEdit(prefill)
        self.edit.setPlaceholderText("输入本次提交的说明...")
        v.addWidget(self.edit)
        btns = QHBoxLayout()
        btns.addStretch(1)
        ok = QPushButton("继续（拉取后提交）")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        v.addLayout(btns)

    def message(self):
        return self.edit.toPlainText().strip()


# ============================== 冲突解决对话框 ==============================
class ConflictDialog(QDialog):
    def __init__(self, path, vcs_type, conflicts, vcs: VcsOperations, parent=None):
        super().__init__(parent)
        self.path = path
        self.vcs_type = vcs_type
        self.vcs = vcs
        self.setWindowTitle("解决冲突")
        self.resize(960, 640)

        v = QVBoxLayout(self)
        v.addWidget(QLabel("检测到以下文件存在冲突，请逐个解决后继续提交："))

        splitter = QSplitter(Qt.Horizontal)
        # 左：冲突文件列表
        left = QWidget()
        lbox = QVBoxLayout(left)
        lbox.setContentsMargins(0, 0, 0, 0)
        lbox.addWidget(QLabel("冲突文件"))
        self.file_list = QListWidget()
        self.file_list.currentItemChanged.connect(self._on_file_changed)
        lbox.addWidget(self.file_list)
        splitter.addWidget(left)

        # 右：本地 / 远端 内容对比
        right = QWidget()
        rbox = QVBoxLayout(right)
        rbox.setContentsMargins(0, 0, 0, 0)
        local_label = QLabel("本地 (ours / mine)")
        remote_label = QLabel("远端 (theirs)")
        h = QHBoxLayout()
        h.addWidget(local_label)
        h.addWidget(remote_label)
        rbox.addLayout(h)
        hh = QHBoxLayout()
        self.local_view = QPlainTextEdit()
        self.local_view.setReadOnly(True)
        self.remote_view = QPlainTextEdit()
        self.remote_view.setReadOnly(True)
        hh.addWidget(self.local_view)
        hh.addWidget(self.remote_view)
        rbox.addLayout(hh, 1)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        v.addWidget(splitter, 1)

        # 操作按钮
        ops = QHBoxLayout()
        b_local = QPushButton("使用本地版本")
        b_local.clicked.connect(lambda: self._resolve("local"))
        b_remote = QPushButton("使用远端版本")
        b_remote.clicked.connect(lambda: self._resolve("remote"))
        b_edit = QPushButton("用默认程序打开编辑")
        b_edit.clicked.connect(self._open_editor)
        b_manual = QPushButton("手动解决完成，标记已解决")
        b_manual.clicked.connect(lambda: self._resolve("manual"))
        ops.addWidget(b_local)
        ops.addWidget(b_remote)
        ops.addWidget(b_edit)
        ops.addWidget(b_manual)
        ops.addStretch(1)
        v.addLayout(ops)

        # 底部
        bottom = QHBoxLayout()
        self.info_label = QLabel()
        bottom.addWidget(self.info_label)
        bottom.addStretch(1)
        self.continue_btn = QPushButton("继续提交")
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self.accept)
        cancel = QPushButton("取消提交")
        cancel.clicked.connect(self.reject)
        bottom.addWidget(self.continue_btn)
        bottom.addWidget(cancel)
        v.addLayout(bottom)

        self._load(conflicts)

    def _load(self, conflicts):
        self.file_list.clear()
        for f in conflicts:
            self.file_list.addItem(f)
        self._update_info()

    def _current_file(self):
        it = self.file_list.currentItem()
        return it.text() if it else None

    def _on_file_changed(self, cur, prev):
        if cur is None:
            self.local_view.clear()
            self.remote_view.clear()
            return
        f = cur.text()
        local, remote = self.vcs.conflict_contents(self.path, self.vcs_type, f)
        self.local_view.setPlainText(local)
        self.remote_view.setPlainText(remote)

    def _resolve(self, strategy):
        f = self._current_file()
        if not f:
            return
        r = self.vcs.resolve_conflict(self.path, self.vcs_type, f, strategy)
        if not r.success:
            if r.error:
                QMessageBox.warning(self, "解决失败", r.error)
            return  # 解决失败时保留该条目，避免漏解决就继续提交
        # 从列表移除
        row = self.file_list.currentRow()
        self.file_list.takeItem(row)
        self.local_view.clear()
        self.remote_view.clear()
        self._update_info()

    def _open_editor(self):
        f = self._current_file()
        if not f:
            return
        full = os.path.join(self.path, f)
        try:
            os.startfile(full)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    def _update_info(self):
        n = self.file_list.count()
        self.info_label.setText(f"剩余冲突：{n}")
        self.continue_btn.setEnabled(n == 0)

# -*- coding: utf-8 -*-
"""VCS 操作封装：git / svn 的拉取、提交推送、日志、冲突检测与解决"""
import os
import re
import subprocess


# git status --porcelain 的冲突状态码
_GIT_CONFLICT_XY = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}


class VcsResult:
    def __init__(self, success=True, output="", conflicts=None, error=""):
        self.success = success
        self.output = output
        self.conflicts = conflicts or []
        self.error = error


class VcsOperations:
    # ---------- 底层执行 ----------
    @staticmethod
    def _run(args, cwd, timeout=600):
        try:
            p = subprocess.run(
                args, cwd=cwd, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout,
            )
            out = (p.stdout or "") + (p.stderr or "")
            return VcsResult(success=(p.returncode == 0), output=out, error=(p.stderr or ""))
        except FileNotFoundError:
            tool = args[0] if args else ""
            return VcsResult(success=False, error=f"未找到命令行工具 {tool}，请确认已安装并在 PATH 中")
        except subprocess.TimeoutExpired:
            return VcsResult(success=False, error="命令执行超时")
        except Exception as e:
            return VcsResult(success=False, error=str(e))

    @staticmethod
    def detect_vcs(path):
        if os.path.isdir(os.path.join(path, ".git")):
            return "git"
        if os.path.isdir(os.path.join(path, ".svn")):
            return "svn"
        return None

    # ========== 拉取 ==========
    def pull(self, path, vcs_type):
        if vcs_type == "git":
            # --no-edit 自动合并冲突标记但不打开编辑器；先尝试 pull
            r = self._run(["git", "pull", "--no-edit"], path)
            conflicts = self.git_conflicts(path)
            return VcsResult(success=r.success and not conflicts,
                             output=r.output, conflicts=conflicts, error=r.error)
        else:
            r = self._run(["svn", "update", "--accept", "postpone"], path)
            conflicts = self.svn_conflicts(path)
            return VcsResult(success=r.success and not conflicts,
                             output=r.output, conflicts=conflicts, error=r.error)

    # ========== 提交推送 ==========
    def prepare_commit(self, path, vcs_type):
        """提交前先拉取最新，自动合并不冲突项，返回冲突列表"""
        return self.pull(path, vcs_type)

    def finish_commit(self, path, vcs_type, message):
        """实际提交并推送"""
        if vcs_type == "git":
            self._run(["git", "add", "-A"], path)
            r = self._run(["git", "commit", "-m", message], path)
            # 没有改动时 commit 会失败，属正常，继续 push
            push = self._run(["git", "push"], path)
            out = r.output + "\n" + push.output
            return VcsResult(success=push.success, output=out,
                             error=(r.error or "") + "\n" + (push.error or ""))
        else:
            self._run(["svn", "add", "--force", "."], path)
            r = self._run(["svn", "commit", "-m", message], path)
            return VcsResult(success=r.success, output=r.output, error=r.error)

    # ========== 日志 ==========
    def log(self, path, vcs_type):
        if vcs_type == "git":
            r = self._run(
                ["git", "log", "-50", "--date=short",
                 "--pretty=format:%h | %ad | %an | %s"], path)
            return r
        else:
            r = self._run(["svn", "log", "-l", "50"], path)
            return r

    # ========== 冲突检测 ==========
    def git_conflicts(self, path):
        r = self._run(["git", "status", "--porcelain"], path)
        conflicts = []
        for line in r.output.splitlines():
            if len(line) < 3:
                continue
            xy = line[:2]
            if xy in _GIT_CONFLICT_XY:
                f = line[3:].strip().strip('"')
                conflicts.append(f)
        return conflicts

    def svn_conflicts(self, path):
        r = self._run(["svn", "status"], path)
        conflicts = []
        for line in r.output.splitlines():
            # 第7列 C 表示冲突
            if len(line) >= 8 and line[6] == "C":
                f = line[8:].strip()
                if f:
                    conflicts.append(f)
        return conflicts

    # ========== 冲突文件内容（本地 / 远端） ==========
    def conflict_contents(self, path, vcs_type, file):
        """返回 (local_text, remote_text)"""
        if vcs_type == "git":
            local = self._run(["git", "show", ":2:" + file], path).output
            remote = self._run(["git", "show", ":3:" + file], path).output
            return local, remote
        else:
            return self._svn_conflict_contents(path, file)

    def _svn_conflict_contents(self, path, file):
        full = os.path.join(path, file)
        # 找同目录下的 .mine / .rN 文件
        d = os.path.dirname(full) or path
        base = os.path.basename(full)
        local = ""
        remote = ""
        mine_path = os.path.join(d, base + ".mine")
        if os.path.exists(mine_path):
            with open(mine_path, "r", encoding="utf-8", errors="replace") as f:
                local = f.read()
        elif os.path.exists(full):
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                local = f.read()
        # 远端：取版本号最大的 .rN
        rver = -1
        rpath = None
        try:
            for name in os.listdir(d):
                m = re.match(re.escape(base) + r"\.r(\d+)$", name)
                if m:
                    v = int(m.group(1))
                    if v > rver:
                        rver = v
                        rpath = os.path.join(d, name)
        except Exception:
            pass
        if rpath and os.path.exists(rpath):
            with open(rpath, "r", encoding="utf-8", errors="replace") as f:
                remote = f.read()
        return local, remote

    # ========== 冲突解决 ==========
    def resolve_conflict(self, path, vcs_type, file, strategy):
        """strategy: 'local' | 'remote' | 'manual'"""
        if vcs_type == "git":
            if strategy == "local":
                self._run(["git", "checkout", "--ours", "--", file], path)
            elif strategy == "remote":
                self._run(["git", "checkout", "--theirs", "--", file], path)
            # manual: 用户自行编辑
            return self._run(["git", "add", "--", file], path)
        else:
            accept = {"local": "mine-full", "remote": "theirs-full", "manual": "working"}[strategy]
            r = self._run(["svn", "resolve", "--accept", accept, "--", file], path)
            return r

    def has_conflicts(self, path, vcs_type):
        if vcs_type == "git":
            return bool(self.git_conflicts(path))
        else:
            return bool(self.svn_conflicts(path))

    # ========== 自定义命令（bat / exe / ps1）==========
    def run_script(self, path, shell, target):
        """在指定目录下执行自定义脚本/程序
        shell: 'cmd' | 'powershell' | 'exe'
        target: 脚本/程序文件路径；exe 模式下可含参数（如 build.exe --release）
        """
        shell = (shell or "cmd").lower()
        target = (target or "").strip()
        if not target:
            return VcsResult(success=False, error="脚本/程序路径为空")

        if shell == "exe":
            # 完整命令行：首段为程序，其余为参数
            import shlex
            try:
                parts = shlex.split(target, posix=False)
            except Exception:
                parts = target.split()
            if not parts:
                return VcsResult(success=False, error="命令为空")
            return self._run(parts, path)

        if shell == "powershell":
            # target 视为 .ps1 文件路径
            if not os.path.isfile(target):
                return VcsResult(success=False, error=f"找不到脚本文件：{target}")
            args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", target]
            return self._run(args, path)

        # 默认 cmd / bat
        if not os.path.isfile(target):
            return VcsResult(success=False, error=f"找不到脚本文件：{target}")
        return self._run(["cmd", "/c", target], path)

# -*- coding: utf-8 -*-
"""配置管理：项目 / 指令 / 快捷键，持久化到用户 APPDATA 下的 JSON"""
import json
import os
import uuid


class ConfigManager:
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.config = self._load()

    def _get_config_dir(self):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        d = os.path.join(base, "VCSTool")
        os.makedirs(d, exist_ok=True)
        return d

    def _default(self):
        return {"hotkey": "ctrl+alt+v", "projects": []}

    def _load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                cfg.setdefault("hotkey", "ctrl+alt+v")
                cfg.setdefault("projects", [])
                return cfg
            except Exception:
                return self._default()
        return self._default()

    def save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    # ---------- 快捷键 ----------
    def get_hotkey(self):
        return self.config.get("hotkey", "ctrl+alt+v")

    def set_hotkey(self, hotkey):
        self.config["hotkey"] = hotkey
        self.save()

    # ---------- 项目 ----------
    @property
    def projects(self):
        return self.config["projects"]

    def add_project(self, name, vcs_type):
        p = {"id": uuid.uuid4().hex, "name": name, "vcs_type": vcs_type,
             "expanded": True, "commands": []}
        self.config["projects"].append(p)
        self.save()
        return p

    def update_project(self, pid, name=None, vcs_type=None):
        for p in self.config["projects"]:
            if p["id"] == pid:
                if name is not None:
                    p["name"] = name
                if vcs_type is not None:
                    p["vcs_type"] = vcs_type
                self.save()
                return p
        return None

    def remove_project(self, pid):
        self.config["projects"] = [p for p in self.config["projects"] if p["id"] != pid]
        self.save()

    def set_expanded(self, pid, expanded):
        for p in self.config["projects"]:
            if p["id"] == pid:
                p["expanded"] = expanded
                self.save()
                break

    def get_project(self, pid):
        for p in self.config["projects"]:
            if p["id"] == pid:
                return p
        return None

    # ---------- 指令 ----------
    def add_command(self, pid, name, path, action, branch="", shell=None, script=""):
        p = self.get_project(pid)
        if not p:
            return None
        c = {"id": uuid.uuid4().hex, "name": name, "path": path,
             "action": action, "branch": branch,
             "shell": shell, "script": script}
        p["commands"].append(c)
        self.save()
        return c

    def update_command(self, pid, cid, name=None, path=None, action=None,
                       branch=None, shell=None, script=None):
        p = self.get_project(pid)
        if not p:
            return None
        for c in p["commands"]:
            if c["id"] == cid:
                if name is not None:
                    c["name"] = name
                if path is not None:
                    c["path"] = path
                if action is not None:
                    c["action"] = action
                if branch is not None:
                    c["branch"] = branch
                if shell is not None:
                    c["shell"] = shell
                if script is not None:
                    c["script"] = script
                self.save()
                return c
        return None

    def remove_command(self, pid, cid):
        p = self.get_project(pid)
        if not p:
            return
        p["commands"] = [c for c in p["commands"] if c["id"] != cid]
        self.save()

#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MANIFEST = "manifest.json"
ENTRY = "main.js"
MANIFEST_BYTES = 64 << 10
ENTRY_BYTES = 4 << 20
LINE_CHARS = 1000
API_VERSION = 1
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
CAPABILITIES = {
    "search", "account", "suggestions", "recommendations", "danmaku", "devices",
    "rankings", "seasons", "cover", "metadata", "catalogState", "mediaAuth",
}


def string_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def manifest_problems(manifest: dict, repo: str | None, tag: str | None) -> list[str]:
    errors = []
    module_id = manifest.get("id")
    if not isinstance(module_id, str) or not ID_PATTERN.match(module_id):
        errors.append("id 只能用小写字母、数字、下划线和连字符，以字母或数字开头，最长 32 个字符")
    elif repo is not None and repo != module_id:
        errors.append(f"仓库名 {repo} 须与模块标识 {module_id} 相同")
    if not isinstance(manifest.get("name"), str) or not manifest["name"].strip():
        errors.append("缺少 name")
    version = manifest.get("version")
    if not isinstance(version, str) or not VERSION_PATTERN.match(version):
        errors.append("version 须为“主版本.次版本.修订号”，例如 1.0.0")
    elif tag is not None and tag != "v" + version:
        errors.append(f"标签 {tag} 须为 v{version}")
    if not isinstance(manifest.get("description", ""), str):
        errors.append("description 须为字符串")
    if manifest.get("runtime") != "js":
        errors.append("runtime 须为 js")
    if manifest.get("api") != API_VERSION:
        errors.append(f"api 须为 {API_VERSION}")
    if not isinstance(manifest.get("adult"), bool):
        errors.append("adult 须为 true 或 false")
    for field in ("hosts", "aliases", "hostSuffixes", "mediaAuthPaths"):
        if field in manifest and not string_list(manifest[field]):
            errors.append(f"{field} 须为字符串数组")
    capabilities = manifest.get("capabilities", [])
    if not string_list(capabilities):
        errors.append("capabilities 须为字符串数组")
        capabilities = []
    for name in capabilities:
        if name not in CAPABILITIES:
            errors.append(f"未知的能力 {name}")
    paths = manifest.get("mediaAuthPaths", [])
    if string_list(paths):
        if ("mediaAuth" in capabilities) != bool(paths):
            errors.append("mediaAuth 能力与 mediaAuthPaths 须同时声明")
        if any(not path.startswith("/") for path in paths):
            errors.append("mediaAuthPaths 的每一项须以 / 开头")
    rankings = manifest.get("rankings", [])
    seen = set()
    for ranking in rankings if isinstance(rankings, list) else [None]:
        key = ranking.get("id") if isinstance(ranking, dict) else None
        if not isinstance(key, str) or not key.strip() or not str(ranking.get("name", "")).strip() or key in seen:
            errors.append("rankings 的每一项须有 id 和 name，且 id 不重复")
            break
        seen.add(key)
    return errors


def code_problems(text: str) -> list[str]:
    errors = []
    for number, line in enumerate(text.splitlines(), 1):
        if len(line) > LINE_CHARS:
            errors.append(f"main.js 第 {number} 行超过 {LINE_CHARS} 个字符，不接受压缩或混淆过的代码")
            break
    node = shutil.which("node")
    if node is None:
        errors.append("找不到 node，无法检查 main.js 的语法")
        return errors
    with tempfile.TemporaryDirectory() as folder:
        wrapped = Path(folder) / ENTRY
        wrapped.write_text("(function(module, exports, host) {" + text + "\n})", encoding="utf-8")
        result = subprocess.run([node, "--check", str(wrapped)], capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            errors.append("main.js 语法错误：\n" + (result.stderr or result.stdout).strip())
    return errors


def problems(manifest_raw: bytes, code_raw: bytes, repo: str | None = None, tag: str | None = None) -> list[str]:
    errors = []
    if len(manifest_raw) > MANIFEST_BYTES:
        errors.append(f"{MANIFEST} 超过 {MANIFEST_BYTES >> 10} KB")
    if len(code_raw) > ENTRY_BYTES:
        errors.append(f"{ENTRY} 超过 {ENTRY_BYTES >> 20} MB")
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        return errors + [f"{MANIFEST} 无法解析：{error}"]
    if not isinstance(manifest, dict):
        return errors + [f"{MANIFEST} 须为对象"]
    errors += manifest_problems(manifest, repo, tag)
    try:
        text = code_raw.decode("utf-8")
    except UnicodeDecodeError:
        return errors + [f"{ENTRY} 须为 UTF-8 编码"]
    return errors + code_problems(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 guoapp 站源模块")
    parser.add_argument("directory", type=Path, help="模块目录")
    parser.add_argument("--repo", help="仓库名，须与模块标识相同")
    parser.add_argument("--tag", help="发版标签，须为 v<版本号>")
    args = parser.parse_args()
    files = {}
    for name in (MANIFEST, ENTRY):
        path = args.directory / name
        if not path.is_file():
            print(f"缺少 {name}", file=sys.stderr)
            return 1
        files[name] = path.read_bytes()
    errors = problems(files[MANIFEST], files[ENTRY], args.repo, args.tag)
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

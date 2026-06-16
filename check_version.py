import datetime
import json
import os
import re
import sys
from pathlib import Path

import requests


请求头 = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

产品配置 = {
    "antigravity_2_0": {
        "名称": "Antigravity 2.0",
        "显示名": "Antigravity 2.0（新版）",
        "接口": "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/releases",
        "标签前缀": "antigravity-2-0",
        "资产前缀": "Antigravity-2.0",
    },
    "antigravity_ide": {
        "名称": "Antigravity IDE",
        "显示名": "Antigravity IDE（旧版）",
        "接口": "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app/releases",
        "标签前缀": "antigravity-ide",
        "资产前缀": "Antigravity-IDE",
    },
}

README产品顺序 = ("antigravity_2_0", "antigravity_ide")

平台列表 = [
    {"键": "windows-x64", "平台": "Windows", "架构": "x64", "扩展名": "exe"},
    {"键": "windows-arm64", "平台": "Windows", "架构": "ARM64", "扩展名": "exe"},
    {"键": "darwin-arm", "平台": "macOS", "架构": "Apple Silicon", "扩展名": "dmg"},
    {"键": "darwin-x64", "平台": "macOS", "架构": "Intel", "扩展名": "dmg"},
    {"键": "linux-x64", "平台": "Linux", "架构": "x64", "扩展名": "tar.gz"},
    {"键": "linux-arm", "平台": "Linux", "架构": "ARM64", "扩展名": "tar.gz"},
]


def 版本键(版本号):
    return tuple(int(x) for x in re.findall(r"\d+", 版本号))


def 是新版IDE(版本号):
    主版本 = 版本键(版本号)[0] if 版本键(版本号) else 0
    return 主版本 >= 2


def 清理执行ID(执行ID):
    return str(执行ID).strip().strip("/")


def 完整版本(版本项):
    return f"{版本项['version']}-{清理执行ID(版本项['execution_id'])}"


def 规范化版本项(项目):
    版本 = str(项目.get("version", "")).strip()
    执行ID = 项目.get("execution_id")
    if not 执行ID and 项目.get("full_version"):
        执行ID = str(项目["full_version"]).split("-", 1)[1]
    if not 版本 or not 执行ID:
        return None
    return {"version": 版本, "execution_id": 清理执行ID(执行ID)}


def 排序去重(版本列表):
    去重 = {}
    for 项目 in 版本列表:
        标准项 = 规范化版本项(项目)
        if 标准项:
            去重[标准项["version"]] = 标准项
    return sorted(去重.values(), key=lambda x: 版本键(x["version"]))


def 获取远程版本(产品键):
    配置 = 产品配置[产品键]
    响应 = requests.get(配置["接口"], headers=请求头, timeout=20)
    响应.raise_for_status()
    数据 = 响应.json()
    if isinstance(数据, dict):
        数据 = 数据.get("versions", [])
    版本列表 = 排序去重(数据)
    if not 版本列表:
        raise RuntimeError(f"{配置['名称']} 未返回任何版本")
    return 版本列表


def 加载历史记录():
    路径 = Path("history.json")
    空历史 = {产品键: [] for 产品键 in 产品配置}
    if not 路径.exists():
        return 空历史

    try:
        原始 = json.loads(路径.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"读取 history.json 失败: {e}")
        return 空历史

    if isinstance(原始, dict):
        历史 = {}
        for 产品键 in 产品配置:
            历史[产品键] = 排序去重(原始.get(产品键, []))
        return 历史

    # 兼容旧 schema：list[{"version": "...", "full_version": "..."}]
    历史 = {产品键: [] for 产品键 in 产品配置}
    if isinstance(原始, list):
        for 项目 in 原始:
            标准项 = 规范化版本项(项目)
            if not 标准项:
                continue
            产品键 = "antigravity_2_0" if 版本键(标准项["version"])[0] >= 2 else "antigravity_ide"
            历史[产品键].append(标准项)

    for 产品键 in 产品配置:
        历史[产品键] = 排序去重(历史[产品键])
    return 历史


def 保存历史记录(历史):
    Path("history.json").write_text(
        json.dumps(历史, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def 读取版本状态():
    路径 = Path("VERSION")
    if not 路径.exists():
        return {}
    内容 = 路径.read_text(encoding="utf-8").strip()
    if not 内容:
        return {}
    try:
        数据 = json.loads(内容)
        if isinstance(数据, dict):
            return {k: str(v) for k, v in 数据.items()}
    except Exception:
        pass
    return {"antigravity_2_0": 内容}


def 保存版本状态(状态):
    Path("VERSION").write_text(
        json.dumps(状态, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def 生成下载链接(产品键, 版本项, 平台键, 扩展名):
    版本 = 版本项["version"]
    执行ID = 清理执行ID(版本项["execution_id"])

    if 产品键 == "antigravity_2_0":
        基础 = f"https://storage.googleapis.com/antigravity-public/antigravity-hub/{版本}-{执行ID}"
        if 平台键 in ("darwin-arm", "darwin-x64"):
            return f"{基础}/{平台键}/Antigravity.dmg"
        if 平台键 == "windows-x64":
            文件名 = "Antigravity.exe" if 版本 == "2.0.0" else "Antigravity-x64.exe"
            return f"{基础}/windows-x64/{文件名}"
        if 平台键 == "windows-arm64":
            文件名 = "Antigravity.exe" if 版本 == "2.0.0" else "Antigravity-arm64.exe"
            return f"{基础}/windows-arm/{文件名}"
        if 平台键 == "linux-x64":
            return f"{基础}/linux-x64/Antigravity.tar.gz"
        if 平台键 == "linux-arm":
            return f"{基础}/linux-arm/Antigravity.tar.gz"

    文件名 = "Antigravity%20IDE" if 是新版IDE(版本) else "Antigravity"
    基础 = f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{版本}-{执行ID}"
    return f"{基础}/{平台键}/{文件名}.{扩展名}"


def 获取最新版(历史, 产品键):
    if not 历史.get(产品键):
        return None
    return max(历史[产品键], key=lambda x: 版本键(x["version"]))


def 生成快速下载表(产品键, 版本项):
    行 = [
        "| 平台 | 版本号 | 架构 | 下载链接 |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for 平台 in 平台列表:
        url = 生成下载链接(产品键, 版本项, 平台["键"], 平台["扩展名"])
        行.append(f"| **{平台['平台']}** | `{版本项['version']}` | {平台['架构']} | [点击下载]({url}) |")
    return "\n".join(行)


def 生成历史表(产品键, 历史列表, 当前版本):
    行 = [
        "| 版本号 | 构建 ID | Windows x64 | Windows ARM64 | macOS Apple Silicon | macOS Intel | Linux x64 | Linux ARM64 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for 项目 in reversed(历史列表):
        if 当前版本 and 项目["version"] == 当前版本:
            continue
        链接 = {}
        for 平台 in 平台列表:
            链接[平台["键"]] = 生成下载链接(产品键, 项目, 平台["键"], 平台["扩展名"])
        行.append(
            f"| `{项目['version']}` | `{项目['execution_id']}` | "
            f"[下载]({链接['windows-x64']}) | [下载]({链接['windows-arm64']}) | "
            f"[下载]({链接['darwin-arm']}) | [下载]({链接['darwin-x64']}) | "
            f"[下载]({链接['linux-x64']}) | [下载]({链接['linux-arm']}) |"
        )
    return "\n".join(行)


def 提取旧更新时间():
    路径 = Path("README.md")
    if not 路径.exists():
        return None
    匹配 = re.search(r"\*\*更新时间\*\*: `([^`]+)`", 路径.read_text(encoding="utf-8", errors="ignore"))
    return 匹配.group(1) if 匹配 else None


def 生成README内容(历史, 更新时间):
    最新 = {产品键: 获取最新版(历史, 产品键) for 产品键 in 产品配置}
    新版产品 = "antigravity_2_0"
    新版最新 = 最新.get(新版产品)

    内容 = f"""# Google Antigravity 版本监控

> [!TIP]
> 本仓库由自动化脚本维护，每小时直接同步官网 releases 接口。

**更新时间**: `{更新时间}`

## 当前新版: Antigravity 2.0

"""

    if 新版最新:
        内容 += f"""### 最新版本: `{新版最新['version']}`

完整版本: `{完整版本(新版最新)}`

### 快速下载

{生成快速下载表(新版产品, 新版最新)}

<details open>
<summary>Antigravity 2.0 历史版本</summary>

{生成历史表(新版产品, 历史[新版产品], 新版最新['version'])}

</details>

"""

    for 产品键 in README产品顺序:
        if 产品键 == 新版产品:
            continue
        配置 = 产品配置[产品键]
        最新项 = 最新[产品键]
        if not 最新项:
            continue
        内容 += f"""---

## {配置['显示名']}

> 该通道保留在底部作为旧版下载入口。

### 旧版最新版本: `{最新项['version']}`

完整版本: `{完整版本(最新项)}`

### 快速下载

{生成快速下载表(产品键, 最新项)}

<details open>
<summary>历史版本记录</summary>

{生成历史表(产品键, 历史[产品键], 最新项['version'])}

</details>

"""

    内容 += "---\n王校长，出色！\n"
    return 内容


def 合并远程版本(历史, 远程版本):
    变化产品 = []
    for 产品键, 版本列表 in 远程版本.items():
        原历史 = {项目["version"]: 项目["execution_id"] for 项目 in 历史.get(产品键, [])}
        新历史 = {项目["version"]: 项目["execution_id"] for 项目 in 历史.get(产品键, [])}
        for 项目 in 版本列表:
            新历史[项目["version"]] = 项目["execution_id"]

        if 新历史 != 原历史:
            变化产品.append(产品键)

        历史[产品键] = 排序去重(
            {"version": 版本, "execution_id": 执行ID}
            for 版本, 执行ID in 新历史.items()
        )
    return 变化产品


def 更新本地文件(历史, 变化产品, 需要初始化):
    当前状态 = 读取版本状态()
    新状态 = {
        产品键: 获取最新版(历史, 产品键)["version"]
        for 产品键 in 产品配置
        if 获取最新版(历史, 产品键)
    }

    版本变化 = 当前状态 != 新状态
    if 版本变化:
        print(f"检测到版本状态变化: {当前状态} -> {新状态}")
        保存版本状态(新状态)

    数据变化 = bool(变化产品) or 版本变化 or 需要初始化
    更新时间 = (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if 数据变化
        else (提取旧更新时间() or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    README内容 = 生成README内容(历史, 更新时间)
    README路径 = Path("README.md")
    需要更新README = (not README路径.exists()) or README路径.read_text(encoding="utf-8") != README内容

    if 需要更新README:
        README路径.write_text(README内容, encoding="utf-8")

    保存历史记录(历史)
    return 版本变化 or bool(变化产品), 需要更新README


def 写Github输出(键, 值):
    if "GITHUB_OUTPUT" not in os.environ:
        return
    值 = str(值)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
        if "\n" in 值:
            标记 = f"EOF_{键}"
            f.write(f"{键}<<{标记}\n{值}\n{标记}\n")
        else:
            f.write(f"{键}={值}\n")


def 写输出集合(历史, 需要初始化, 版本变化, README变化, 变化产品):
    最新 = {产品键: 获取最新版(历史, 产品键) for 产品键 in 产品配置}
    版本名 = " / ".join(
        f"{产品配置[产品键]['名称']} {最新[产品键]['version']}"
        for 产品键 in README产品顺序
        if 最新[产品键]
    )

    写Github输出("init", "true" if 需要初始化 else "false")
    写Github输出("history", "[]")
    写Github输出("version_changed", "true" if 版本变化 else "false")
    写Github输出("readme_changed", "true" if README变化 else "false")
    写Github输出("version", 版本名)


def 主程序():
    if len(sys.argv) > 1:
        raise SystemExit("当前脚本只同步版本信息，不再下载安装包。")

    需要初始化 = not Path("VERSION").exists()
    历史 = 加载历史记录()

    远程版本 = {}
    for 产品键 in 产品配置:
        print(f"正在获取 {产品配置[产品键]['名称']} 版本列表...")
        远程版本[产品键] = 获取远程版本(产品键)

    变化产品 = 合并远程版本(历史, 远程版本)
    版本变化, README变化 = 更新本地文件(历史, 变化产品, 需要初始化)
    写输出集合(历史, 需要初始化, 版本变化, README变化, 变化产品)

    if not 版本变化 and not README变化:
        print("版本未变，本地文件无需更新。")


if __name__ == "__main__":
    主程序()

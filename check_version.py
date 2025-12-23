import requests
import re
import os

def 获取最新版本():
    基础地址 = "https://antigravity.google"
    下载页面 = f"{基础地址}/download"
    请求头 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # 1. 获取下载页面 HTML
        响应 = requests.get(下载页面, headers=请求头, timeout=15)
        响应.raise_for_status()
        网页内容 = 响应.text
        
        # 2. 寻找 main-*.js 文件
        js文件匹配 = re.search(r'src="(main-[^"]+\.js)"', 网页内容)
        if not js文件匹配:
            print("错误：未能找到 main.js 文件")
            return None
        
        js地址 = f"{基础地址}/{js文件匹配.group(1)}"
        print(f"正在解析 JS 文件: {js地址}")
        
        # 3. 获取 JS 内容并提取版本号
        js响应 = requests.get(js地址, headers=请求头, timeout=15)
        js响应.raise_for_status()
        js内容 = js响应.text
        
        # 匹配版本号规律：x.y.z-digits
        版本匹配 = re.search(r'(\d+\.\d+\.\d+)-(\d+)', js内容)
        if 版本匹配:
            主版本 = 版本匹配.group(1)
            完整版本 = f"{主版本}-{版本匹配.group(2)}"
            return 主版本, 完整版本
        else:
            print("错误：未能从 JS 文件中提取到版本号")
            return None, None
    except Exception as e:
        print(f"请求失败: {e}")
        return None, None

def 生成README内容(版本, 完整版本, 历史列表):
    import datetime
    当前时间 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    内容 = f"""# Google Antigravity 版本监控

> [!TIP]
> 本仓库由自动化脚本维护，每小时自动同步一次官网最新版本。

## 🌟 当前最新版本: `{版本}`
**更新时间**: `{当前时间}`

### 🚀 快速下载 (最新版)
| 平台 | 架构 | 下载链接 |
| :--- | :--- | :--- |
| **Windows** | x64 | [点击下载](https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{完整版本}/windows-x64/Antigravity.exe) |
| **Windows** | ARM64 | [点击下载](https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{完整版本}/windows-arm64/Antigravity.exe) |
| **MacOS** | Apple Silicon | [点击下载](https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{完整版本}/darwin-arm/Antigravity.dmg) |
| **MacOS** | Intel | [点击下载](https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{完整版本}/darwin-x64/Antigravity.dmg) |
| **Linux** | - | [前往官网下载](https://antigravity.google/download/linux) |

## 📜 历史版本记录
| 版本号 | Windows (x64) | MacOS (M系列) | MacOS (Intel) |
| :--- | :--- | :--- | :--- |
"""
    # 倒序排列历史版本，让较新的排在上面
    for 项 in reversed(历史列表):
        v = 项["version"]
        fv = 项["full_version"]
        内容 += f"| `{v}` | [下载](https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{fv}/windows-x64/Antigravity.exe) | [下载](https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{fv}/darwin-arm/Antigravity.dmg) | [下载](https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{fv}/darwin-x64/Antigravity.dmg) |\n"

    内容 += "\n---\n王校长，出色！\n"
    return 内容

def 更新版本文件(新版本, 完整版本, 历史列表):
    版本文件路径 = "VERSION"
    README路径 = "README.md"
    旧版本 = ""
    README已存在 = os.path.exists(README路径)
    
    if os.path.exists(版本文件路径):
        with open(版本文件路径, "r", encoding="utf-8") as f:
            旧版本 = f.read().strip()
    
    # 生成新内容
    README内容 = 生成README内容(新版本, 完整版本, 历史列表)
    
    # 检查 README 是否需要更新 (不存在或者内容不一致)
    需要更新README = not README已存在
    if README已存在:
        with open(README路径, "r", encoding="utf-8") as f:
            if f.read() != README内容:
                需要更新README = True

    # 写入新内容
    with open(README路径, "w", encoding="utf-8") as f:
        f.write(README内容)
    
    # 只要版本变了或者 README 需要更新，就返回 True
    if 新版本 != 旧版本 or 需要更新README:
        if 新版本 != 旧版本:
            print(f"检测到新版本: {旧版本} -> {新版本}")
            with open(版本文件路径, "w", encoding="utf-8") as f:
                f.write(新版本)
        else:
            print("版本未变，但更新了 README.md")
        return True
    else:
        print(f"当前已是最新版本且 README 已是最新")
        return False

def 下载安装包(版本, 完整版本):
    下载任务 = [
        {"名": "Antigravity-Windows-x64.exe", "地址": f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{完整版本}/windows-x64/Antigravity.exe"},
        {"名": "Antigravity-Windows-ARM64.exe", "地址": f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{完整版本}/windows-arm64/Antigravity.exe"},
        {"名": "Antigravity-MacOS-Silicon.dmg", "地址": f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{完整版本}/darwin-arm/Antigravity.dmg"},
        {"名": "Antigravity-MacOS-Intel.dmg", "地址": f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{完整版本}/darwin-x64/Antigravity.dmg"}
    ]
    
    已下载文件 = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    for 任务 in 下载任务:
        文件名 = 任务["名"]
        url = 任务["地址"]
        print(f"正在备份安装包: {文件名}...")
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(文件名, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            已下载文件.append(文件名)
        except Exception as e:
            print(f"备份失败 ({文件名}): {e}")
            
    return 已下载文件

if __name__ == "__main__":
    # 历史版本数据
    历史版本列表 = [
        {"version": "1.11.2", "full_version": "1.11.2-6251250307170304"},
        {"version": "1.12.4", "full_version": "1.12.4-5388582906101760"},
        {"version": "1.13.3", "full_version": "1.13.3-4533425205018624"}
    ]

    最新主版本, 最新完整版本 = 获取最新版本()
    
    # 检查是否需要初始化
    # 如果 VERSION 不存在，或者 README 不存在，我们都认为需要一次完整的同步
    需要初始化 = not os.path.exists("VERSION")
    
    if 最新主版本:
        更新成功 = 更新版本文件(最新主版本, 最新完整版本, 历史版本列表)
        
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                if 需要初始化:
                    import json
                    # 关键优化：history 只包含比当前版更旧的版本，防止重复创建
                    历史旧版本 = [项 for 项 in 历史版本列表 if 项["version"] != 最新主版本]
                    f.write(f"init=true\n")
                    f.write(f"history={json.dumps(历史旧版本)}\n")
                
                # 只要是初始化或者版本更新，都执行备份并标记为 updated
                if 更新成功 or 需要初始化:
                    print(f"开始执行安装包备份流程 (原因: {'新版本' if 更新成功 else '初始化'})")
                    文件列表 = 下载安装包(最新主版本, 最新完整版本)
                    f.write(f"updated=true\nversion={最新主版本}\nfull_version={最新完整版本}\n")
                    f.write(f"assets={' '.join(文件列表)}\n")
                else:
                    f.write("updated=false\n")

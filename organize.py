#!/usr/bin/env python3
"""
文件批量归档器 (file-organizer)
================================

把一个乱糟糟的文件夹，按「文件类型」或「月份」自动归进子文件夹。

安全设计（重要）：
  - 默认只 **预览**，列出"会怎么移动"，一个文件都不动。
  - 只有显式加上 --go，才会真正移动。
  - 不覆盖、不删除任何文件。

用法：
  python organize.py <文件夹>              # 预览（按类型）
  python organize.py <文件夹> --go         # 真正执行
  python organize.py <文件夹> --by date    # 按月份归档
  python organize.py <文件夹> --by date --go

零第三方依赖，只用 Python 标准库。
"""

import argparse
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 扩展名 → 分类。想加自己的类型，往这里加就行。
CATEGORIES = {
    "图片": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic", ".tiff"},
    "视频": {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm", ".m4v", ".mpg"},
    "音频": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "文档": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".csv"},
    "压缩包": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "代码": {".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml",
             ".java", ".go", ".rs", ".c", ".cpp", ".sh", ".bat", ".sql"},
}

OTHER = "其他"


def category_of(path: Path) -> str:
    """根据扩展名判断分类。"""
    ext = path.suffix.lower()
    for name, exts in CATEGORIES.items():
        if ext in exts:
            return name
    return OTHER


def build_plan(target: Path, by: str) -> dict:
    """扫描文件夹，返回 {子文件夹名: [文件路径, ...]}。"""
    buckets = defaultdict(list)
    for item in sorted(target.iterdir()):
        # 跳过子文件夹和隐藏文件（.开头）
        if item.is_dir() or item.name.startswith("."):
            continue
        if by == "type":
            sub = category_of(item)
        else:  # by == "date"
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            sub = mtime.strftime("%Y-%m")
        buckets[sub].append(item)
    return buckets


def main() -> None:
    parser = argparse.ArgumentParser(
        description="文件批量归档器 —— 默认只预览，加 --go 才真正移动。"
    )
    parser.add_argument("folder", help="要整理的文件夹路径")
    parser.add_argument(
        "--by", choices=["type", "date"], default="type",
        help="归档方式：type=按文件类型（默认），date=按修改月份",
    )
    parser.add_argument(
        "--go", action="store_true",
        help="真正执行移动。不加这个参数就只预览。",
    )
    args = parser.parse_args()

    target = Path(args.folder).expanduser().resolve()
    if not target.is_dir():
        print(f"❌ 不是有效的文件夹：{target}")
        sys.exit(1)

    buckets = build_plan(target, args.by)
    total = sum(len(files) for files in buckets.values())

    if total == 0:
        print("📂 这个文件夹里没有需要整理的文件。")
        return

    way = "文件类型" if args.by == "type" else "修改月份"
    mode = "执行" if args.go else "预览（不会动任何文件）"

    print(f"📂 目标文件夹：{target}")
    print(f"🧭 归档方式：按{way}")
    print(f"⚙️  当前模式：{mode}")
    print(f"📊 共 {total} 个文件 → 将归入 {len(buckets)} 个子文件夹")
    print("-" * 50)

    for sub in sorted(buckets):
        files = buckets[sub]
        print(f"\n📁 {sub}/  （{len(files)} 个）")
        for f in files:
            print(f"     · {f.name}")

    if not args.go:
        print("\n" + "-" * 50)
        print("👆 以上只是预览，一个文件都没动。")
        print("   确认没问题后，命令末尾加上  --go  再跑一次即可真正执行。")
        return

    print("\n" + "-" * 50)
    for sub, files in buckets.items():
        dest = target / sub
        dest.mkdir(exist_ok=True)
        for f in files:
            shutil.move(str(f), str(dest / f.name))
    print(f"✅ 完成！{total} 个文件已归入 {len(buckets)} 个子文件夹。")


if __name__ == "__main__":
    main()

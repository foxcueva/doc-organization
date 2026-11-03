#!/usr/bin/env python3
"""kb_audit.py — 文档树一致性体检（只读，不修改任何文件）

检查四类问题：
  1. 孤儿文件：存在但没有任何索引引用
  2. 死链：索引里引用了，但文件不存在
  3. 超重文件：单文件 > --max-kb（默认 20KB），提示拆分/蒸馏
  4. 索引缺失：子目录里没有 00-索引.md

用法：
  python3 kb_audit.py                    # 体检 ./knowledge
  python3 kb_audit.py --root ./data      # 体检 data（解析反引号文件名表格）
  python3 kb_audit.py --root . --max-kb 50
"""
import argparse
import os
import re
import sys

WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
CODETICK = re.compile(r"`([^`\n]+\.(?:md|csv|json|ya?ml|txt))`")


def norm(p: str) -> str:
    return os.path.normpath(p.strip())


def collect(root: str):
    files, dirs = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
        dirs.append(dirpath)
        for f in filenames:
            if f.lower().endswith(".md"):
                files.append(os.path.join(dirpath, f))
    return files, dirs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="knowledge")
    ap.add_argument("--max-kb", type=int, default=20)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.root))
    if not os.path.isdir(root):
        sys.exit(f"目录不存在: {root}")

    files, dirs = collect(root)
    rel_files = {os.path.relpath(f, root) for f in files}
    basenames = {}
    for rel in rel_files:
        basenames.setdefault(os.path.basename(rel), []).append(rel)

    referenced, dead = set(), []
    parent = os.path.dirname(root)
    for f in files:
        if os.path.basename(f) != "00-索引.md":
            continue
        text = open(f, encoding="utf-8", errors="ignore").read()
        idx_dir = os.path.dirname(os.path.relpath(f, root))
        lowered = text.lower()
        targets = [m.group(1).split("|")[0].strip() for m in WIKILINK.finditer(text)]
        targets += [m.group(1).strip() for m in CODETICK.finditer(text)]
        # 索引表格里的裸文件名也算引用（如 | skill | ... | `skills/x/` |）
        for rel in rel_files:
            stem = os.path.splitext(os.path.basename(rel))[0]
            if stem.lower() in lowered or os.path.dirname(rel).lower() in lowered:
                referenced.add(rel)
        for t in targets:
            cands = [t] if t.endswith(".md") else [t + ".md", t]
            hit = None
            for c in cands:
                for base in (idx_dir, ""):
                    p = norm(os.path.join(base, c))
                    if p in rel_files:
                        hit = p
                        break
                if hit:
                    break
            if hit:
                referenced.add(hit)
            elif t in basenames:            # 同名文件在别处也算命中
                referenced.update(basenames[t])
            elif os.path.exists(os.path.join(parent, norm(t))):
                continue                     # 跨根引用（如 data/xxx.csv），不算死链
            else:
                dead.append((os.path.relpath(f, root), t))

    orphans = sorted(rel_files - referenced - {"00-索引.md"})
    heavy = [(r, os.path.getsize(os.path.join(root, r)) // 1024)
             for r in rel_files if os.path.getsize(os.path.join(root, r)) > args.max_kb * 1024]
    skip_dirs = {"_模板", "_templates", "assets", "images", "attachments"}
    no_index = [os.path.relpath(d, root) for d in dirs
                if d != root and os.path.basename(d) not in skip_dirs
                and not os.path.isfile(os.path.join(d, "00-索引.md"))]

    print(f"根目录: {root}")
    print(f"Markdown 文件: {len(files)}｜被索引引用: {len(referenced)}")
    print(f"\n孤儿文件 ({len(orphans)})")
    for o in orphans:
        print("  ?", o)
    print(f"\n死链 ({len(dead)})")
    for src, t in dead:
        print(f"  ✗ {src} -> {t}")
    print(f"\n超重文件 >{args.max_kb}KB ({len(heavy)})")
    for r, kb in sorted(heavy, key=lambda x: -x[1]):
        print(f"  ! {r} ({kb}KB)")
    print(f"\n缺 00-索引.md 的目录 ({len(no_index)})")
    for d in no_index:
        print("  +", d)

    bad = len(dead) + len(orphans)
    print(f"\n结论: {'通过' if bad == 0 else '需整理'}（孤儿 {len(orphans)} / 死链 {len(dead)}）")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

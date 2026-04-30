import argparse
import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"
BACKUP_DIR = ROOT / ".session_backups"
CHANGES_JSONL = MEMORY_DIR / "changes.jsonl"
RECENT_MD = MEMORY_DIR / "recent-changes.md"
DISTILLED_MD = MEMORY_DIR / "distilled-memory.md"
DISTILL_STATE = MEMORY_DIR / "distill_state.json"

ALWAYS_LOAD = [
    ROOT / "agent.md",
    ROOT / "memory.md",
    MEMORY_DIR / "load-order.md",
    DISTILLED_MD,
    RECENT_MD,
]

CATEGORY_LOAD = {
    "runtime": [
        MEMORY_DIR / "architecture.md",
        MEMORY_DIR / "constraints.md",
        MEMORY_DIR / "debug-status.md",
    ],
    "watermark": [
        MEMORY_DIR / "categories" / "watermark-and-remove.md",
        MEMORY_DIR / "constraints.md",
        MEMORY_DIR / "debug-status.md",
    ],
    "convert": [
        MEMORY_DIR / "categories" / "convert-audio-image.md",
        MEMORY_DIR / "debug-status.md",
    ],
    "pdf_file": [
        MEMORY_DIR / "categories" / "pdf-file-meta-zip.md",
        MEMORY_DIR / "constraints.md",
        MEMORY_DIR / "debug-status.md",
    ],
}


def ensure_layout():
    (MEMORY_DIR / "categories").mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    CHANGES_JSONL.touch(exist_ok=True)
    if not DISTILL_STATE.exists():
        DISTILL_STATE.write_text(
            json.dumps({"distilled_change_count": 0, "threshold": 30}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if not RECENT_MD.exists():
        RECENT_MD.write_text(
            "# 最近变更\n\n- 当前尚无未蒸馏的变更记录。\n",
            encoding="utf-8",
        )
    if not DISTILLED_MD.exists():
        DISTILLED_MD.write_text("# 蒸馏记忆\n", encoding="utf-8")


def load_state():
    ensure_layout()
    return json.loads(DISTILL_STATE.read_text(encoding="utf-8"))


def save_state(state):
    DISTILL_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_changes():
    ensure_layout()
    changes = []
    for line in CHANGES_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        changes.append(json.loads(line))
    return changes


def format_change_md(entries):
    lines = ["# 最近变更", ""]
    if not entries:
        lines.append("- 当前尚无未蒸馏的变更记录。")
        return "\n".join(lines) + "\n"
    for entry in reversed(entries):
        files = ", ".join(entry.get("files", [])) or "-"
        details = entry.get("details", "").strip() or "-"
        lines.append(f"## {entry['timestamp']} | {entry['category']}")
        lines.append(f"- 摘要：{entry['summary']}")
        lines.append(f"- 文件：{files}")
        lines.append(f"- 说明：{details}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def sync_recent_changes():
    state = load_state()
    changes = load_changes()
    pending = changes[state["distilled_change_count"] :]
    RECENT_MD.write_text(format_change_md(pending), encoding="utf-8")


def append_distilled_block(entries, start_index):
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry["category"]].append(entry)

    lines = [
        "",
        f"## 自动蒸馏 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 覆盖变更：第 {start_index} 到第 {start_index + len(entries) - 1} 条",
    ]
    for category in sorted(grouped):
        category_entries = grouped[category]
        summaries = []
        files = []
        for entry in category_entries:
            if entry["summary"] not in summaries:
                summaries.append(entry["summary"])
            for path in entry.get("files", []):
                if path not in files:
                    files.append(path)
        lines.append(f"- [{category}] 摘要：{'；'.join(summaries)}")
        lines.append(f"  关联文件：{', '.join(files) if files else '-'}")
    with DISTILLED_MD.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def distill(force=False):
    state = load_state()
    changes = load_changes()
    pending = changes[state["distilled_change_count"] :]
    threshold = int(state.get("threshold", 30))
    if not pending:
        sync_recent_changes()
        return {"distilled": False, "pending": 0, "reason": "no_pending_changes"}
    if not force and len(pending) < threshold:
        sync_recent_changes()
        return {"distilled": False, "pending": len(pending), "reason": "threshold_not_reached"}

    start_index = state["distilled_change_count"] + 1
    append_distilled_block(pending, start_index)
    state["distilled_change_count"] = len(changes)
    save_state(state)
    sync_recent_changes()
    return {"distilled": True, "pending": 0, "distilled_count": len(changes)}


def backup(files, keep=20):
    ensure_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = BACKUP_DIR / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "timestamp": timestamp,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "files": [],
    }

    for raw in files:
        src = Path(raw).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Missing file for backup: {src}")
        try:
            rel = src.relative_to(ROOT)
            dst = session_dir / rel
        except ValueError:
            dst = session_dir / "_external" / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        manifest["files"].append({"src": str(src), "backup": str(dst)})

    (session_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    prune_backups(keep)
    return manifest


def prune_backups(keep=20):
    ensure_layout()
    sessions = sorted([p for p in BACKUP_DIR.iterdir() if p.is_dir()], key=lambda p: p.name)
    removed = []
    if keep < 1:
        keep = 1
    for path in sessions[:-keep]:
        shutil.rmtree(path, ignore_errors=True)
        removed.append(str(path))
    return removed


def log_change(category, summary, files, details=""):
    ensure_layout()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": category,
        "summary": summary,
        "files": files,
        "details": details,
    }
    with CHANGES_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    sync_recent_changes()
    distill_result = distill(force=False)
    return {"entry": entry, "distill": distill_result}


def snapshot():
    state = load_state()
    changes = load_changes()
    pending = len(changes) - int(state.get("distilled_change_count", 0))
    payload = {
        "workspace": str(ROOT),
        "always_load": [str(p) for p in ALWAYS_LOAD],
        "categories": {key: [str(p) for p in value] for key, value in CATEGORY_LOAD.items()},
        "distillation": {
            "threshold": int(state.get("threshold", 30)),
            "distilled_change_count": int(state.get("distilled_change_count", 0)),
            "pending_changes": pending,
        },
    }
    return payload


def main():
    parser = argparse.ArgumentParser(description="Workspace backup and memory helper for Fengxi Toolbox.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Backup one or more files before editing.")
    backup_parser.add_argument("files", nargs="+")
    backup_parser.add_argument("--keep", type=int, default=20)

    prune_parser = subparsers.add_parser("prune-backups", help="Prune old backup sessions.")
    prune_parser.add_argument("--keep", type=int, default=20)

    log_parser = subparsers.add_parser("log-change", help="Append an important change and auto-distill when needed.")
    log_parser.add_argument("--category", required=True)
    log_parser.add_argument("--summary", required=True)
    log_parser.add_argument("--details", default="")
    log_parser.add_argument("--files", nargs="*", default=[])

    distill_parser = subparsers.add_parser("distill", help="Force a distillation pass.")
    distill_parser.add_argument("--force", action="store_true")

    subparsers.add_parser("snapshot", help="Print the recommended progressive memory loading plan.")

    args = parser.parse_args()

    if args.command == "backup":
        result = backup(args.files, keep=args.keep)
    elif args.command == "prune-backups":
        result = {"removed": prune_backups(keep=args.keep)}
    elif args.command == "log-change":
        result = log_change(args.category, args.summary, args.files, details=args.details)
    elif args.command == "distill":
        result = distill(force=args.force)
    else:
        result = snapshot()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


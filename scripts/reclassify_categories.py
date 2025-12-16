#!/usr/bin/env python3
"""
重分类论文标签脚本（旧标签 -> 新标签体系）

功能：
- 读取数据库中所有论文的 category
- 使用统一的 normalize_category 归一化到新标签
- 对未匹配/脏数据设置为 Uncategorized，并输出清单
- 生成重分类前后的统计对比和变更日志

使用方式：
    python scripts/reclassify_categories.py            # 实际写入
    python scripts/reclassify_categories.py --dry-run  # 仅查看影响，不写入
"""
import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from app import get_session, Paper
from taxonomy import CATEGORY_DISPLAY, CATEGORY_ORDER, normalize_category

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def counter_to_ordered_dict(counter: Counter) -> dict:
    """将计数结果按统一顺序输出（包含未分类）"""
    ordered = {cat: int(counter.get(cat, 0)) for cat in CATEGORY_ORDER}
    ordered["Uncategorized"] = int(counter.get("Uncategorized", 0))
    return ordered


def main(dry_run: bool = False):
    session = get_session()
    updated = 0
    total = 0
    unmatched = []
    changes = []
    try:
        papers = session.query(Paper).all()
        total = len(papers)

        before_counter = Counter()
        for paper in papers:
            before_counter[normalize_category(paper.category or "")] += 1

        for paper in papers:
            old_cat = paper.category or ""
            new_cat = normalize_category(old_cat)

            if new_cat == "Uncategorized" and old_cat.strip():
                unmatched.append(
                    {
                        "id": paper.id,
                        "title": (paper.title or "")[:120],
                        "old": old_cat,
                    }
                )

            if old_cat != new_cat:
                changes.append(
                    {
                        "id": paper.id,
                        "title": (paper.title or "")[:120],
                        "from": old_cat,
                        "to": new_cat,
                    }
                )
                if not dry_run:
                    paper.category = new_cat
                updated += 1

        if not dry_run:
            session.commit()

        after_counter = Counter()
        for paper in papers:
            after_counter[normalize_category(paper.category or "")] += 1

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = LOG_DIR / f"reclassify_categories_{timestamp}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": timestamp,
                    "dry_run": dry_run,
                    "total": total,
                    "updated": updated,
                    "before": counter_to_ordered_dict(before_counter),
                    "after": counter_to_ordered_dict(after_counter),
                    "unmatched": unmatched,
                    "changes": changes,
                    "display": CATEGORY_DISPLAY,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        print("=" * 60)
        print("重分类完成（dry_run=%s）" % dry_run)
        print(f"总数: {total}, 需要更新: {updated}")
        print(f"未匹配/脏数据: {len(unmatched)}")
        print(f"统计日志: {log_path}")
        if unmatched:
            sample = unmatched[:10]
            print("未匹配示例(前10条):")
            for item in sample:
                print(f"- {item['id']} | {item['old']} | {item['title']}")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"重分类失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="重分类论文标签到新标签体系")
    parser.add_argument(
        "--dry-run", action="store_true", help="只统计变更和日志，不写入数据库"
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)



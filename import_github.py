"""
xi-skill GitHub 语料导入
========================
把 data/raw/ 下面的外部语料导入 xi_corpus.db

目前支持:
    - xi_talk.csv (KengChiChang/xi-talk, 224 篇 2012-2017 讲话)

用法:
    python import_github.py xi_talk
"""

import csv
import re
import sys
import sqlite3
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper import init_db, detect_classical_ref


META_PATTERNS = [
    r"^[（(]新华社",
    r"^[（(]记者",
    r"^来源[:：]",
    r"^责任编辑",
    r"^编辑[:：]",
    r"^发布时间",
]


def is_meta_line(line: str) -> bool:
    return any(re.match(p, line) for p in META_PATTERNS)


def split_into_quotes(content: str) -> list:
    """按段落切分再按句号切分。10-250 字保留。去重。"""
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    quotes = []
    for line in lines:
        if is_meta_line(line):
            continue
        sentences = re.split(r"(?<=[。！？])", line)
        for sent in sentences:
            sent = sent.strip()
            if 10 <= len(sent) <= 250:
                quotes.append(sent)
    seen = set()
    deduped = []
    for q in quotes:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped


TYPE_TO_CATEGORY = {
    "党建": "party",
    "经济": "economic",
    "政治": "politics",
    "外交": "diplomacy",
    "文化": "culture",
    "社会": "society",
    "国防": "defense",
    "生态": "ecology",
}


def import_xi_talk(conn: sqlite3.Connection):
    csv_path = Path(__file__).parent / "data" / "raw" / "xi_talk.csv"
    if not csv_path.exists():
        print(f"❌ 文件不存在: {csv_path}")
        return

    print("=" * 60)
    print("📥 导入 KengChiChang/xi-talk (224 篇讲话 2012-2017)")
    print("=" * 60)

    article_count = 0
    quote_count = 0
    skipped = 0

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get("date", "").strip()
            type_cn = row.get("type", "").strip()
            type_en = row.get("type_en", "").strip()
            title = row.get("title", "").strip()
            link = row.get("link", "").strip()
            content = row.get("content", "").strip()

            if not content or len(content) < 200:
                skipped += 1
                continue

            # 清理空白
            content = re.sub(r"\n\s*\n", "\n", content)
            content = re.sub(r"[ \t]+", " ", content)

            aid = hashlib.sha256((link or title).encode()).hexdigest()[:16]

            existing = conn.execute(
                "SELECT 1 FROM articles WHERE id = ?", (aid,)
            ).fetchone()
            if existing:
                continue

            category = TYPE_TO_CATEGORY.get(type_cn, "speech")
            has_ref = 1 if detect_classical_ref(content) else 0
            tags = f"{type_cn},{type_en}"

            try:
                conn.execute(
                    "INSERT INTO articles "
                    "(id, url, title, content, source, date, category, speaker, tags, has_classical_ref, word_count) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (aid, link, title, content, "github_xi_talk", date, category,
                     "习近平", tags, has_ref, len(content))
                )
                article_count += 1
            except sqlite3.IntegrityError:
                continue

            # 切句入 quotes
            sents = split_into_quotes(content)
            new_quotes = 0
            for sent in sents:
                existing_q = conn.execute(
                    "SELECT 1 FROM quotes WHERE text = ?", (sent,)
                ).fetchone()
                if existing_q:
                    continue
                has_sent_ref = 1 if detect_classical_ref(sent) else 0
                conn.execute(
                    "INSERT INTO quotes "
                    "(text, source_article_id, source_desc, date, scene_type, topic_tags, has_classical_ref) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (sent, aid, title, date, "speech", tags, has_sent_ref)
                )
                new_quotes += 1
            quote_count += new_quotes

            if article_count % 20 == 0:
                conn.commit()
                print(f"  ... {article_count} 篇 / {quote_count} 条新语录")

    conn.commit()
    print()
    print(f"📊 xi_talk.csv 导入完成：")
    print(f"   文章: +{article_count} 篇 (跳过 {skipped})")
    print(f"   语录: +{quote_count} 条")


if __name__ == "__main__":
    conn = init_db()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")

    cmd = sys.argv[1] if len(sys.argv) > 1 else "xi_talk"

    if cmd == "xi_talk":
        import_xi_talk(conn)
    else:
        print(f"未知命令: {cmd}")
        print("可用: xi_talk")

    conn.close()

"""
xi-voice 语录检索工具
====================
从 xi_corpus.db 的 quotes 表中检索匹配语录。

用法:
    python quote_db.py --topic 人工智能 --scene speech --limit 10
    python quote_db.py --topic 改革 --limit 5
    python quote_db.py --topic 台湾 --scene diplomacy

参数:
    --topic   必需。检索的关键词
    --scene   可选。场景过滤: speech / party_congress / newyear / diplomacy / inspection / editorial / press / internal
    --limit   可选。结果条数，默认 10
    --min-len 可选。最短语句长度过滤，默认 15

无论从哪里调用都能找到 data/xi_corpus.db（repo 根目录）。
"""
import sqlite3
import argparse
import sys
from pathlib import Path

# DB 位于 repo 根目录的 data/xi_corpus.db
# xi-voice/tools/quote_db.py → parents[2] = repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "xi_corpus.db"


def search(topic: str, scene: str = None, limit: int = 10, min_len: int = 15) -> int:
    if not DB_PATH.exists():
        print(f"❌ 数据库不存在: {DB_PATH}", file=sys.stderr)
        print("请先按 data/raw/README.md 的步骤构建 xi_corpus.db", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    query = (
        "SELECT text, source_desc, date, scene_type FROM quotes "
        "WHERE text LIKE ? AND length(text) >= ?"
    )
    params = [f"%{topic}%", min_len]
    if scene:
        query += " AND scene_type = ?"
        params.append(scene)
    query += " ORDER BY length(text) ASC LIMIT ?"
    params.append(limit)

    results = conn.execute(query, params).fetchall()

    if not results:
        print(f"没找到包含「{topic}」的语录" + (f"（场景={scene}）" if scene else ""))
        conn.close()
        return 0

    scene_tag = f"（场景={scene}）" if scene else ""
    print(f"🔍 与「{topic}」相关的语录{scene_tag}：{len(results)} 条\n")
    for text, src, date, sc in results:
        print(f"[{sc or '?'}] {date or '?'}")
        print(f"  {text}")
        print(f"  来源: {src or '?'}")
        print()

    conn.close()
    return 0


def main():
    p = argparse.ArgumentParser(description="xi-voice 语录检索")
    p.add_argument("--topic", required=True, help="检索关键词")
    p.add_argument("--scene", default=None,
                   help="场景过滤: speech/party_congress/newyear/diplomacy/inspection/editorial/press/internal")
    p.add_argument("--limit", type=int, default=10, help="结果条数")
    p.add_argument("--min-len", type=int, default=15, help="最短语句长度")
    args = p.parse_args()
    sys.exit(search(args.topic, args.scene, args.limit, args.min_len))


if __name__ == "__main__":
    main()

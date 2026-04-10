"""
Papersnake/xi_talk → xi_corpus.db 导入脚本
预计: 14497条 → ~14000+ articles, ~200000+ quotes
"""
import sqlite3
import json
import hashlib
import re
from pathlib import Path
from html import unescape

DB_PATH = Path("data/xi_corpus.db")
INPUT_PATH = Path("data/raw/xi_talk_full.json")  # jsonl

# ═══ 日期提取 ═══
DATE_PATTERNS = [
    r"(\d{4})年(\d{1,2})月(\d{1,2})日",           # 2019年06月11日
    r"(\d{4})-(\d{1,2})-(\d{1,2})",                # 2019-06-11
    r"(\d{4})(\d{2})(\d{2})",                       # 20190611
]

def extract_date(text: str, article_html: str = "") -> str | None:
    """从正文或HTML中提取日期"""
    for source in [article_html[:2000], text[:1000]]:
        for pat in DATE_PATTERNS:
            m = re.search(pat, source)
            if m:
                y, mo, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
                if 2012 <= int(y) <= 2026:
                    return f"{y}-{mo}-{d}"
    return None

# ═══ HTML清洗 ═══
TAG_RE = re.compile(r"<[^>]+>")

def clean_html(html: str) -> str:
    """HTML → 纯文本 fallback（当text字段为空时用）"""
    text = TAG_RE.sub("", html)
    return unescape(text).strip()

# ═══ 分类器 ═══
def classify(title: str, text: str) -> tuple[str, str]:
    """返回 (category, speaker)"""
    t = title + text[:500]
    if "新年贺词" in t:
        return "newyear", "习近平"
    if any(k in t for k in ["二十大", "十九大", "十八大", "党代会", "全国代表大会"]):
        return "party_congress", "习近平"
    if any(k in t for k in ["考察", "调研"]):
        return "inspection", "习近平"
    if any(k in t for k in ["会见", "会晤", "出访", "峰会"]):
        return "diplomacy", "习近平"
    if any(k in t for k in ["社论", "评论员"]):
        return "editorial", "人民日报"
    if any(k in t for k in ["记者会", "答记者问"]):
        return "press", "外交部发言人"
    return "speech", "习近平"

# ═══ 古典引用检测 ═══
def has_classical(text: str) -> int:
    patterns = [r"[《][^》]{1,20}[》]", r"古人[云说曰]",
                r"诗[云曰]", r"[孔孟老庄]子[曰云]"]
    return 1 if any(re.search(p, text) for p in patterns) else 0

# ═══ 切句（入quotes表）═══
def split_quotes(text: str) -> list:
    """按句号/感叹号/问号切句，过滤太短的"""
    raw = re.split(r"[。！？]", text)
    return [s.strip() for s in raw
            if 15 <= len(s.strip()) <= 500]


def load_records(path: Path):
    """
    自动识别 jsonl / json-list / HF datasets dict 三种格式
    """
    text = path.read_text("utf-8")
    stripped = text.lstrip()
    # jsonl: 多行，每行一个 JSON 对象
    if stripped.startswith("{") and "\n{" in stripped[:5000]:
        return [json.loads(l) for l in text.splitlines() if l.strip()]
    # 整个是 JSON
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "train" in data:
            return data["train"]
        if isinstance(data, list):
            return data
        return [data]
    except json.JSONDecodeError:
        # 兜底 jsonl
        return [json.loads(l) for l in text.splitlines() if l.strip()]


# ═══ 主导入 ═══
def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")

    # 添加 article_html 列（如果不存在）
    try:
        conn.execute("ALTER TABLE articles ADD COLUMN article_html TEXT DEFAULT ''")
        print("  + 添加列 article_html")
    except sqlite3.OperationalError:
        pass  # 已存在

    # 加载已有title用于去重
    existing_titles = set(
        r[0] for r in conn.execute("SELECT title FROM articles").fetchall()
    )
    print(f"已有 {len(existing_titles)} 篇，开始导入...")

    data = load_records(INPUT_PATH)
    print(f"加载数据集 {len(data)} 条")

    art_count = 0
    quote_count = 0
    skip_count = 0

    for i, row in enumerate(data):
        title = (row.get("title") or "").strip()
        text = (row.get("text") or "").strip()
        article_html = row.get("article") or ""
        jhsjk_id = str(row.get("id", ""))
        author = row.get("author") or ""

        # text为空时从HTML提取
        if not text and article_html:
            text = clean_html(article_html)

        if not text or len(text) < 50:
            skip_count += 1
            continue

        # 去重：title完全匹配则跳过
        if title in existing_titles:
            skip_count += 1
            continue

        # 生成ID
        aid = hashlib.sha256(f"papersnake_{jhsjk_id}_{title}".encode()).hexdigest()[:16]

        # 提取日期
        date_str = extract_date(text, article_html)

        # 分类
        category, speaker = classify(title, text)

        # 古典引用
        classical = has_classical(text)

        # 写入articles
        url = f"http://jhsjk.people.cn/article/{jhsjk_id}" if jhsjk_id else ""
        try:
            conn.execute(
                """INSERT OR IGNORE INTO articles
                   (id, url, title, content, source, date, category,
                    speaker, tags, has_classical_ref, word_count, article_html)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (aid, url, title, text, "papersnake", date_str,
                 category, speaker, author, classical, len(text), article_html)
            )
            existing_titles.add(title)
            art_count += 1
        except Exception:
            continue

        # 切句入quotes
        quotes = split_quotes(text)
        for q in quotes:
            q_classical = has_classical(q)
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO quotes
                       (text, source_article_id, source_desc, date,
                        scene_type, topic_tags, has_classical_ref)
                       VALUES (?,?,?,?,?,?,?)""",
                    (q, aid, title[:50], date_str, category, "", q_classical)
                )
                quote_count += 1
            except Exception:
                pass

        # 进度
        if (i + 1) % 1000 == 0:
            conn.commit()
            print(f"  进度 {i+1}/{len(data)} | articles +{art_count} | quotes +{quote_count} | skip {skip_count}")

    conn.commit()
    conn.close()

    print(f"""
═══ 导入完成 ═══
📄 新增文章: {art_count}
💬 新增语录: {quote_count}
⏭️ 跳过: {skip_count}
""")


if __name__ == "__main__":
    main()

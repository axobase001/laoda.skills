"""
xi-skill 定向讲话抓取
====================
抓取固定 URL 列表的重要讲话：13 篇新年贺词 + 二十大/十九大报告
每篇入 articles 表作为全文，按段落拆句入 quotes 表

用法:
    python collect_speeches.py
"""

import re
import sys
import time
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scraper import init_db, fetch, article_id, detect_classical_ref

from bs4 import BeautifulSoup


# (url, title, date, scene_type, category, topic_tags)
SPEECHES = [
    # 13 篇新年贺词 (delivered on 12-31, for the following year)
    ("https://news.12371.cn/2013/12/31/ARTI1388487735102495.shtml",
     "2014年新年贺词", "2013-12-31", "newyear", "newyear", "新年贺词,2014"),
    ("https://news.12371.cn/2014/12/31/ARTI1420022919224108.shtml",
     "2015年新年贺词", "2014-12-31", "newyear", "newyear", "新年贺词,2015"),
    ("https://news.12371.cn/2015/12/31/ARTI1451560038016217.shtml",
     "2016年新年贺词", "2015-12-31", "newyear", "newyear", "新年贺词,2016"),
    ("https://news.12371.cn/2016/12/31/ARTI1483183171033213.shtml",
     "2017年新年贺词", "2016-12-31", "newyear", "newyear", "新年贺词,2017"),
    ("https://news.12371.cn/2017/12/31/ARTI1514719011830231.shtml",
     "2018年新年贺词", "2017-12-31", "newyear", "newyear", "新年贺词,2018"),
    ("https://www.12371.cn/2018/12/31/ARTI1546254656765588.shtml",
     "2019年新年贺词", "2018-12-31", "newyear", "newyear", "新年贺词,2019"),
    ("https://www.12371.cn/2019/12/31/ARTI1577791387078382.shtml",
     "2020年新年贺词", "2019-12-31", "newyear", "newyear", "新年贺词,2020"),
    ("https://www.12371.cn/2020/12/31/ARTI1609413305029488.shtml",
     "2021年新年贺词", "2020-12-31", "newyear", "newyear", "新年贺词,2021"),
    ("https://www.12371.cn/2021/12/31/ARTI1640949566377784.shtml",
     "2022年新年贺词", "2021-12-31", "newyear", "newyear", "新年贺词,2022"),
    ("https://www.12371.cn/2022/12/31/ARTI1672485507369806.shtml",
     "2023年新年贺词", "2022-12-31", "newyear", "newyear", "新年贺词,2023"),
    ("https://www.12371.cn/2023/12/31/ARTI1704021349027132.shtml",
     "2024年新年贺词", "2023-12-31", "newyear", "newyear", "新年贺词,2024"),
    ("https://www.12371.cn/2024/12/31/ARTI1735643989505764.shtml",
     "2025年新年贺词", "2024-12-31", "newyear", "newyear", "新年贺词,2025"),
    ("https://www.12371.cn/2025/12/31/ARTI1767180064399544.shtml",
     "2026年新年贺词", "2025-12-31", "newyear", "newyear", "新年贺词,2026"),

    # 党代会报告
    ("http://www.news.cn/politics/2022-10/25/c_1129079429.htm",
     "二十大报告：高举中国特色社会主义伟大旗帜 为全面建设社会主义现代化国家而团结奋斗",
     "2022-10-16", "party_congress", "party_congress", "二十大,党代会报告,理论"),
    ("http://www.xinhuanet.com/politics/19cpcnc/2017-10/27/c_1121867529.htm",
     "十九大报告：决胜全面建成小康社会 夺取新时代中国特色社会主义伟大胜利",
     "2017-10-18", "party_congress", "party_congress", "十九大,党代会报告,理论"),
]


def extract_content(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    content = ""
    for sel in [
        "#p_content", "#Content", "#ozoom",
        "#content", ".content", "#article", ".article",
        ".TRS_Editor", "#detail", "#p-detail", ".detail",
        ".article-content",
    ]:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 300:
                content = text
                break

    if len(content) < 300:
        paragraphs = soup.find_all("p")
        content = "\n".join(
            p.get_text(strip=True) for p in paragraphs
            if len(p.get_text(strip=True)) > 15
        )

    return content


META_PATTERNS = [
    r"^[（(]新华社",
    r"^[（(]记者",
    r"^来源[:：]",
    r"^责任编辑",
    r"^编辑[:：]",
    r"^发布时间",
    r"^字号",
    r"^打印",
    r"^收藏",
    r"^分享",
    r"^CCTV",
    r"^新华社北京",
]


def is_meta_line(line: str) -> bool:
    return any(re.match(p, line) for p in META_PATTERNS)


def split_into_quotes(content: str) -> list:
    """按段落切分，再按句号/问号/感叹号二次切分。保留 10-200 字的句子。"""
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    quotes = []
    for line in lines:
        if is_meta_line(line):
            continue
        # 按中文句末标点切分（保留标点）
        sentences = re.split(r"(?<=[。！？])", line)
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if 10 <= len(sent) <= 250:
                quotes.append(sent)
    # 去重（保持顺序）
    seen = set()
    deduped = []
    for q in quotes:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped


def collect_all(conn):
    article_count = 0
    quote_count = 0
    failed = []

    for url, title, date, scene_type, category, tags in SPEECHES:
        print(f"\n📥 {title}")
        print(f"   日期: {date}")
        print(f"   URL:  {url}")

        aid = article_id(url)
        existing = conn.execute(
            "SELECT word_count FROM articles WHERE id = ?", (aid,)
        ).fetchone()
        if existing:
            print(f"   ⏭️  已存在 ({existing[0]}字)，跳过")
            continue

        html = fetch(url)
        if not html:
            print("   ❌ 抓取失败")
            failed.append((title, url, "fetch_failed"))
            continue

        content = extract_content(html)
        if len(content) < 300:
            print(f"   ❌ 正文过短: {len(content)}字")
            failed.append((title, url, f"content_too_short:{len(content)}"))
            continue

        has_ref = 1 if detect_classical_ref(content) else 0
        source = "12371" if "12371" in url else "xinhua"

        try:
            conn.execute(
                "INSERT INTO articles "
                "(id, url, title, content, source, date, category, speaker, tags, has_classical_ref, word_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (aid, url, title, content, source, date, category, "习近平",
                 tags, has_ref, len(content))
            )
            article_count += 1
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  文章插入失败: {e}")
            continue

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
                (sent, aid, title, date, scene_type, tags, has_sent_ref)
            )
            new_quotes += 1

        quote_count += new_quotes
        conn.commit()
        print(f"   ✅ 正文 {len(content)}字 → 切出 {len(sents)} 句 (新增 {new_quotes} 条)")

        time.sleep(3)  # 礼貌延迟

    print("\n" + "=" * 60)
    print(f"📊 采集完成：{article_count} 篇讲话，{quote_count} 条新增语录")
    print("=" * 60)

    if failed:
        print(f"\n❌ 失败 {len(failed)} 篇：")
        for title, url, reason in failed:
            print(f"   - {title}: {reason}")


if __name__ == "__main__":
    conn = init_db()
    # 启用 WAL 以便和 scraper 并发
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    collect_all(conn)
    conn.close()

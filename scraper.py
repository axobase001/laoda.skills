"""
xi-skill 语料采集工具集
========================
三个采集器 + 一个统一数据库

使用方法:
    pip install requests beautifulsoup4 lxml --break-system-packages
    python scraper.py xinhua       # 采集新华社习近平相关报道
    python scraper.py mfa          # 采集外交部发言人答记者问
    python scraper.py quotes       # 手动录入/批量导入语录
    python scraper.py stats        # 查看数据库统计
    python scraper.py signal-scan  # 扫描已有语料中的信号词
"""

import sqlite3
import json
import re
import sys
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ============================================================
# 数据库
# ============================================================

DB_PATH = Path(__file__).parent / "data" / "xi_corpus.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,              -- sha256(url)[:16]
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,             -- xinhua / mfa / rmrb / manual
    date TEXT,                        -- YYYY-MM-DD
    category TEXT,                    -- speech / press / editorial / newyear / party_congress / diplomacy / internal
    speaker TEXT,                     -- 习近平 / 外交部发言人 / etc
    tags TEXT,                        -- 逗号分隔
    has_classical_ref INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    source_article_id TEXT,           -- FK -> articles.id
    source_desc TEXT,                 -- 人工标注来源
    date TEXT,
    scene_type TEXT,                  -- newyear / party_congress / diplomacy / inspection / internal
    topic_tags TEXT,
    has_classical_ref INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (source_article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase TEXT NOT NULL,             -- 官方表述
    translation TEXT NOT NULL,       -- 翻译/真实含义
    signal_level INTEGER DEFAULT 1,  -- 1-6
    signal_type TEXT,                -- escalation / retreat / personnel / economic / diplomatic
    context TEXT,                    -- 使用场景说明
    example_article_id TEXT,         -- 案例文章
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,              -- 事件名称
    date_start TEXT,
    date_end TEXT,
    trigger_event TEXT,              -- 触发事件
    decision TEXT,                   -- 实际决策
    retreat INTEGER DEFAULT 0,       -- 是否退让
    retreat_method TEXT,             -- 退让方式
    mental_models TEXT,              -- 涉及的心智模型（逗号分隔）
    retreat_triggers TEXT,           -- 激活的退让条件（JSON）
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    title, content, tags,
    content='articles',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
    INSERT INTO articles_fts(rowid, title, content, tags)
    VALUES (new.rowid, new.title, new.content, new.tags);
END;
"""


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


# ============================================================
# 通用工具
# ============================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch(url: str, retry=3, delay=2) -> str | None:
    for i in range(retry):
        try:
            r = SESSION.get(url, timeout=15)
            r.encoding = r.apparent_encoding or "utf-8"
            if r.status_code == 200:
                return r.text
            print(f"  [WARN] {url} → {r.status_code}")
        except Exception as e:
            print(f"  [ERR] {url} → {e}")
        if i < retry - 1:
            time.sleep(delay * (i + 1))
    return None


def detect_classical_ref(text: str) -> bool:
    """检测是否包含古典引用（简单规则）"""
    patterns = [
        r"[《][^》]{1,20}[》]",  # 书名号引用
        r"古人[云说曰]",
        r"[唐宋元明清]代",
        r"诗[云曰]",
        r"[孔孟荀老庄]子[曰云说]",
        r"所谓[「「]",
    ]
    return any(re.search(p, text) for p in patterns)


# ============================================================
# 采集器 1: 新华社
# ============================================================

def scrape_xinhua(conn: sqlite3.Connection, pages: int = 5):
    """
    采集新华社"习近平"相关报道
    入口: http://www.news.cn/politics/leaders/xijinping/
    备用: 新华社搜索 API
    """
    print("=" * 60)
    print("📡 新华社采集器")
    print("=" * 60)

    base_url = "http://www.news.cn"
    search_url = "http://so.news.cn/getNews"

    total_saved = 0

    for page in range(pages):
        print(f"\n--- 第 {page + 1}/{pages} 页 ---")

        params = {
            "keyword": "习近平",
            "curPage": page,
            "sortField": 0,  # 按时间排序
            "searchFields": 1,  # 标题+正文
        }

        html = fetch(f"{search_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
        if not html:
            # 备用：直接爬列表页
            print("  搜索API不可用，尝试列表页...")
            html = fetch(f"{base_url}/politics/leaders/xijinping/index.htm")
            if not html:
                print("  列表页也不可用，跳过")
                continue

        soup = BeautifulSoup(html, "lxml")

        # 新华社页面结构经常变，这里用多种选择器兜底
        links = []
        for selector in [
            "div.searchPart a[href]",
            "ul.dataList li a[href]",
            "div.tit a[href]",
            "h3 a[href]",
            ".domPC a[href]",
        ]:
            found = soup.select(selector)
            if found:
                links.extend(found)
                break

        if not links:
            # 最后兜底：找所有包含 /202 的链接（新华社URL格式）
            links = [a for a in soup.find_all("a", href=True)
                     if "/202" in a["href"] and "习近平" in (a.get_text() or "")]

        print(f"  找到 {len(links)} 条链接")

        for a in links[:20]:  # 每页最多处理20条
            href = a.get("href", "")
            if not href.startswith("http"):
                href = base_url + href

            # 去重
            aid = article_id(href)
            existing = conn.execute("SELECT 1 FROM articles WHERE id = ?", (aid,)).fetchone()
            if existing:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue

            # 抓正文
            article_html = fetch(href)
            if not article_html:
                continue

            article_soup = BeautifulSoup(article_html, "lxml")

            # 正文选择器（新华社常用）
            content = ""
            for sel in ["#detail", ".detail", "#p-detail", ".article", ".content"]:
                el = article_soup.select_one(sel)
                if el:
                    content = el.get_text(separator="\n", strip=True)
                    break

            if not content or len(content) < 100:
                # 兜底：取所有 <p> 标签
                paragraphs = article_soup.find_all("p")
                content = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)

            if len(content) < 100:
                continue

            # 提取日期
            date_str = None
            date_el = article_soup.select_one(".time, .date, .pub_time, .header-time span")
            if date_el:
                date_match = re.search(r"(\d{4})[-.年/](\d{1,2})[-.月/](\d{1,2})", date_el.get_text())
                if date_match:
                    date_str = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"

            # 自动分类
            category = "speech"
            if "新年贺词" in title:
                category = "newyear"
            elif "记者会" in title or "答记者问" in title:
                category = "press"
            elif "社论" in title or "评论员" in title:
                category = "editorial"
            elif "出访" in title or "会见" in title or "会晤" in title:
                category = "diplomacy"
            elif "考察" in title or "调研" in title:
                category = "inspection"

            has_ref = 1 if detect_classical_ref(content) else 0

            try:
                conn.execute(
                    "INSERT INTO articles (id, url, title, content, source, date, category, speaker, tags, has_classical_ref, word_count) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (aid, href, title, content, "xinhua", date_str, category, "习近平", "", has_ref, len(content))
                )
                total_saved += 1
                print(f"  ✅ {title[:40]}... ({len(content)}字)")
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        time.sleep(3)  # 礼貌延迟

    print(f"\n📊 新华社采集完成，新增 {total_saved} 篇")


# ============================================================
# 采集器 2: 外交部发言人
# ============================================================

def scrape_mfa(conn: sqlite3.Connection, pages: int = 5):
    """
    采集外交部发言人定期记者会
    入口: https://www.mfa.gov.cn/web/fyrbt_673021/jzhsl_673025/
    """
    print("=" * 60)
    print("📡 外交部发言人采集器")
    print("=" * 60)

    base_url = "https://www.mfa.gov.cn"
    list_url = f"{base_url}/web/fyrbt_673021/jzhsl_673025/"

    total_saved = 0

    for page in range(pages):
        print(f"\n--- 第 {page + 1}/{pages} 页 ---")

        if page == 0:
            page_url = list_url
        else:
            page_url = f"{list_url}index_{page}.shtml"

        html = fetch(page_url)
        if not html:
            print("  页面不可用，跳过")
            continue

        soup = BeautifulSoup(html, "lxml")

        # 只匹配真实记者会 URL 格式: /2026XX/tYYYYMMDD_NNNN.shtml
        conf_re = re.compile(r"/?\d{6}/t\d{8}_\d+\.shtml$")
        links = [a for a in soup.find_all("a", href=True) if conf_re.search(a["href"])]

        print(f"  找到 {len(links)} 条链接")

        for a in links[:40]:
            href = a.get("href", "")
            href = urljoin(page_url, href)

            aid = article_id(href)
            if conn.execute("SELECT 1 FROM articles WHERE id = ?", (aid,)).fetchone():
                continue

            title = a.get_text(strip=True)
            article_html = fetch(href)
            if not article_html:
                continue

            article_soup = BeautifulSoup(article_html, "lxml")

            content = ""
            for sel in ["#News_Body_Txt_A", ".News_Body_Txt", "#content", ".article-content", ".TRS_Editor"]:
                el = article_soup.select_one(sel)
                if el:
                    content = el.get_text(separator="\n", strip=True)
                    break

            if len(content) < 50:
                paragraphs = article_soup.find_all("p")
                content = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 10)

            if len(content) < 50:
                continue

            date_str = None
            date_match = re.search(r"(\d{4})[-.年/](\d{1,2})[-.月/](\d{1,2})", title + " " + article_html[:2000])
            if date_match:
                date_str = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"

            # 提取发言人姓名
            speaker = "外交部发言人"
            for name in ["毛宁", "汪文斌", "林剑", "华春莹", "赵立坚", "耿爽", "陆慷", "洪磊"]:
                if name in content[:200]:
                    speaker = name
                    break

            try:
                conn.execute(
                    "INSERT INTO articles (id, url, title, content, source, date, category, speaker, tags, has_classical_ref, word_count) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (aid, href, title, content, "mfa", date_str, "press", speaker, "", 0, len(content))
                )
                total_saved += 1
                print(f"  ✅ {title[:40]}... ({len(content)}字)")
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        time.sleep(3)

    print(f"\n📊 外交部采集完成，新增 {total_saved} 篇")


# ============================================================
# 语录管理
# ============================================================

# 预置种子语录（装完即可用）
SEED_QUOTES = [
    # (text, source_desc, date, scene_type, topic_tags)
    ("中华民族伟大复兴的中国梦，就是要实现国家富强、民族振兴、人民幸福。",
     "十二届全国人大一次会议", "2013-03-17", "party_congress", "中国梦,民族复兴"),
    ("打铁还需自身硬。",
     "十八届中央政治局常委见面会", "2012-11-15", "party_congress", "反腐,党建"),
    ("人民对美好生活的向往，就是我们的奋斗目标。",
     "十八届中央政治局常委见面会", "2012-11-15", "party_congress", "民生,执政理念"),
    ("撸起袖子加油干。",
     "2017年新年贺词", "2016-12-31", "newyear", "奋斗,口号"),
    ("幸福都是奋斗出来的。",
     "2018年新年贺词", "2017-12-31", "newyear", "奋斗"),
    ("我们都在努力奔跑，我们都是追梦人。",
     "2019年新年贺词", "2018-12-31", "newyear", "奋斗,中国梦"),
    ("不忘初心，牢记使命。",
     "十九大报告", "2017-10-18", "party_congress", "党建,初心"),
    ("绿水青山就是金山银山。",
     "浙江考察", "2005-08-15", "inspection", "环保,发展"),
    ("房子是用来住的，不是用来炒的。",
     "中央经济工作会议", "2016-12-16", "speech", "房地产,经济"),
    ("中国人民不好惹，惹翻了是不好办的。",
     "纪念抗美援朝70周年大会", "2020-10-23", "speech", "外交,强硬"),
    ("别看你今天闹得欢，小心今后拉清单。",
     "内部讲话流出", "2014-01-01", "internal", "反腐,威慑"),
    ("亲自指挥，亲自部署。",
     "疫情防控讲话", "2020-02-03", "speech", "COVID,领导"),
    ("些小吾曹州县吏，一枝一叶总关情。",
     "引用郑板桥诗", "2014-05-09", "speech", "民生,典故引用"),
    ("不要人夸颜色好，只留清气满乾坤。",
     "十九届中央政治局常委见面会", "2017-10-25", "party_congress", "典故引用,执政理念"),
    ("我将无我，不负人民。",
     "会见外宾", "2019-03-22", "diplomacy", "执政理念,个人风格"),
    ("勿谓言之不预也。",
     "人民日报引用（中美贸易战）", "2019-05-29", "editorial", "外交,最高级别警告"),
    ("人类命运共同体。",
     "联合国日内瓦总部演讲", "2017-01-18", "diplomacy", "外交,理念"),
    ("一带一路不是中国一家的独奏，而是沿线国家的合唱。",
     "一带一路国际合作高峰论坛", "2017-05-14", "diplomacy", "一带一路,外交"),
    ("关键核心技术是要不来、买不来、讨不来的。",
     "两院院士大会", "2018-05-28", "speech", "科技,自主创新"),
    ("江山就是人民，人民就是江山。",
     "建党百年讲话", "2021-07-01", "speech", "执政理念,党建"),
]


def seed_quotes(conn: sqlite3.Connection):
    """导入种子语录"""
    count = 0
    for text, source_desc, date, scene_type, tags in SEED_QUOTES:
        existing = conn.execute("SELECT 1 FROM quotes WHERE text = ?", (text,)).fetchone()
        if existing:
            continue
        has_ref = 1 if detect_classical_ref(text) else 0
        conn.execute(
            "INSERT INTO quotes (text, source_desc, date, scene_type, topic_tags, has_classical_ref) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (text, source_desc, date, scene_type, tags, has_ref)
        )
        count += 1
    conn.commit()
    print(f"📝 种子语录导入完成，新增 {count} 条")


# ============================================================
# 信号词典种子数据
# ============================================================

SEED_SIGNALS = [
    # (phrase, translation, level, type, context)
    # 升级信号
    ("表示关切", "注意到了，还没打算动", 1, "escalation", "外交场合最低级别回应"),
    ("强烈不满", "开始认真了", 2, "escalation", "标准外交抗议"),
    ("严正交涉", "正式警告", 3, "escalation", "约见对方外交官"),
    ("坚决反对", "会有具体反制措施", 4, "escalation", "通常伴随实际行动"),
    ("不惜一切代价", "准备动真格", 5, "escalation", "极少使用，出现即严重"),
    ("勿谓言之不预", "历史上这句话出现后都打了", 6, "escalation", "1962印度/1979越南前均出现"),
    ("中方将采取一切必要措施", "真的会动手", 5, "escalation", "通常24-72小时内有行动"),
    ("搬起石头砸自己的脚", "认为对方会先撑不住", 3, "escalation", "带有嘲讽性质的警告"),
    ("伤害了中国人民的感情", "标准抗议模板，力度不大", 2, "escalation", "高频使用，实际信号弱"),
    ("保留采取进一步措施的权利", "还没决定怎么做", 3, "escalation", "给自己留选项"),
    ("玩火自焚", "强硬警告", 4, "escalation", "多用于台湾问题"),
    ("悬崖勒马", "给对方最后机会", 4, "escalation", "暗示下一步升级"),

    # 退让信号
    ("在前进中不断完善", "政策出了问题，在调整", 0, "retreat", "从不直接承认错误"),
    ("因时因势优化调整", "原来的搞不下去了", 0, "retreat", "COVID政策转向时使用"),
    ("实事求是", "要换方向了", 0, "retreat", "历史上多次作为政策转向信号"),
    ("不折腾", "之前折腾过头了", 0, "retreat", "胡锦涛时期用语，习较少用"),
    ("稳中求进", "先别动了，稳住", 0, "retreat", "经济下行时的标准表述"),
    ("底线思维", "要做最坏打算", 0, "retreat", "可能是收缩信号"),
    ("战略定力", "别人怎么说我们不动", 0, "retreat", "可能是掩盖犹豫的表述"),

    # 人事信号
    ("另有任用", "平调或明升暗降", 0, "personnel", "不一定是坏事但通常不是好事"),
    ("因个人原因辞职", "被迫离开", 0, "personnel", "几乎从来不是真的个人原因"),
    ("严重违纪违法", "要进秦城了", 0, "personnel", "反腐标准用语，意味着落马"),
    ("配合组织调查", "已被控制人身自由", 0, "personnel", "通常是双规/留置"),
    ("主动投案", "可能有人举报或同案犯已落网", 0, "personnel", "近年开始使用，暗示从宽"),

    # 经济信号
    ("高质量发展", "GDP增速不再是首要目标", 0, "economic", "2017年后的核心经济表述"),
    ("新质生产力", "旧增长模式到头了", 0, "economic", "2023年开始的新概念"),
    ("供给侧结构性改革", "要砍产能/去杠杆", 0, "economic", "2015-2018年核心政策"),
    ("共同富裕", "要动富人的蛋糕", 0, "economic", "2021年开始强调"),
    ("防止资本无序扩张", "互联网大厂要挨整", 0, "economic", "2020-2022年监管风暴信号"),
    ("房住不炒", "不救房地产（但后来松动了）", 0, "economic", "信号强度随时间衰减"),
    ("适度宽松的货币政策", "要放水了", 0, "economic", "罕见表述，出现即大动作"),
    ("稳就业", "失业率可能很严重", 0, "economic", "越强调什么越缺什么"),

    # 外交
    ("老朋友", "关系好且有利用价值", 0, "diplomatic", "普京、基辛格等"),
    ("合作伙伴", "标准外交关系，无特殊含义", 0, "diplomatic", "最常用外交定性"),
    ("互利共赢", "标准套话，无实际信号", 0, "diplomatic", "万能外交用语"),
    ("不干涉内政", "这个话题到此为止，别再说了", 0, "diplomatic", "终止讨论的信号"),
    ("中国内政不容干涉", "比上一条更强硬", 0, "diplomatic", "通常针对台湾/香港/新疆"),
    ("友好协商", "还有得谈", 0, "diplomatic", "正面信号"),
    ("搁置争议共同开发", "现在打不过/不想打", 0, "diplomatic", "南海问题常用"),
]


def seed_signals(conn: sqlite3.Connection):
    """导入信号词典种子数据"""
    count = 0
    for phrase, translation, level, stype, context in SEED_SIGNALS:
        existing = conn.execute("SELECT 1 FROM signals WHERE phrase = ?", (phrase,)).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO signals (phrase, translation, signal_level, signal_type, context) "
            "VALUES (?, ?, ?, ?, ?)",
            (phrase, translation, level, stype, context)
        )
        count += 1
    conn.commit()
    print(f"📡 信号词典种子导入完成，新增 {count} 条")


# ============================================================
# 信号扫描器
# ============================================================

def signal_scan(conn: sqlite3.Connection):
    """扫描已有语料，标记匹配的信号词"""
    signals = conn.execute("SELECT phrase, translation, signal_level, signal_type FROM signals").fetchall()
    articles = conn.execute("SELECT id, title, content, source, date FROM articles").fetchall()

    print("=" * 60)
    print(f"🔍 信号扫描：{len(signals)} 个信号词 × {len(articles)} 篇文章")
    print("=" * 60)

    hits = []
    for aid, title, content, source, date in articles:
        for phrase, translation, level, stype in signals:
            count = content.count(phrase)
            if count > 0:
                hits.append((level, phrase, translation, count, title[:30], source, date))

    hits.sort(key=lambda x: (-x[0], -x[3]))

    level_emoji = {0: "⚪", 1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🔴", 6: "⛔"}

    print(f"\n检出 {len(hits)} 处信号命中：\n")
    for level, phrase, translation, count, title, source, date in hits[:50]:
        emoji = level_emoji.get(level, "⚪")
        print(f"  {emoji} Lv{level} [{phrase}] ×{count} → {translation}")
        print(f"       📄 {title}... ({source}, {date})")

    if len(hits) > 50:
        print(f"\n  ... 及另外 {len(hits) - 50} 处命中")


# ============================================================
# 统计
# ============================================================

def show_stats(conn: sqlite3.Connection):
    print("=" * 60)
    print("📊 xi-skill 数据库统计")
    print("=" * 60)

    articles_count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    quotes_count = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    signals_count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    decisions_count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]

    print(f"\n  📄 文章:   {articles_count}")
    print(f"  💬 语录:   {quotes_count}")
    print(f"  📡 信号词: {signals_count}")
    print(f"  🧠 决策:   {decisions_count}")

    if articles_count > 0:
        print("\n  --- 文章来源分布 ---")
        for source, count in conn.execute(
            "SELECT source, COUNT(*) FROM articles GROUP BY source ORDER BY COUNT(*) DESC"
        ).fetchall():
            print(f"    {source}: {count}")

        print("\n  --- 文章分类分布 ---")
        for cat, count in conn.execute(
            "SELECT category, COUNT(*) FROM articles GROUP BY category ORDER BY COUNT(*) DESC"
        ).fetchall():
            print(f"    {cat}: {count}")

        total_words = conn.execute("SELECT SUM(word_count) FROM articles").fetchone()[0] or 0
        classical_count = conn.execute("SELECT COUNT(*) FROM articles WHERE has_classical_ref = 1").fetchone()[0]
        print(f"\n  📖 总字数:        {total_words:,}")
        print(f"  📚 含古典引用:    {classical_count}/{articles_count} ({classical_count/articles_count*100:.0f}%)")

    if signals_count > 0:
        print("\n  --- 信号词类型分布 ---")
        for stype, count in conn.execute(
            "SELECT signal_type, COUNT(*) FROM signals GROUP BY signal_type ORDER BY COUNT(*) DESC"
        ).fetchall():
            print(f"    {stype}: {count}")

    if quotes_count > 0:
        print("\n  --- 语录场景分布 ---")
        for scene, count in conn.execute(
            "SELECT scene_type, COUNT(*) FROM quotes GROUP BY scene_type ORDER BY COUNT(*) DESC"
        ).fetchall():
            print(f"    {scene}: {count}")


# ============================================================
# CLI
# ============================================================

USAGE = """
用法: python scraper.py <command>

命令:
  xinhua       采集新华社报道（默认5页）
  mfa          采集外交部发言人记者会（默认5页）
  quotes       导入种子语录
  signals      导入信号词典种子数据
  signal-scan  扫描语料中的信号词
  stats        查看数据库统计
  init         初始化数据库 + 导入所有种子数据
  all          运行全部采集 + 导入

选项:
  --pages N    设置采集页数（默认5）

示例:
  python scraper.py init              # 首次使用：初始化 + 种子数据
  python scraper.py xinhua --pages 10 # 采集新华社10页
  python scraper.py all --pages 3     # 全部采集3页
  python scraper.py signal-scan       # 扫描信号词
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return

    cmd = sys.argv[1]
    pages = 5
    if "--pages" in sys.argv:
        idx = sys.argv.index("--pages")
        if idx + 1 < len(sys.argv):
            pages = int(sys.argv[idx + 1])

    conn = init_db()

    if cmd == "init":
        seed_quotes(conn)
        seed_signals(conn)
        show_stats(conn)
    elif cmd == "xinhua":
        scrape_xinhua(conn, pages)
    elif cmd == "mfa":
        scrape_mfa(conn, pages)
    elif cmd == "quotes":
        seed_quotes(conn)
    elif cmd == "signals":
        seed_signals(conn)
    elif cmd == "signal-scan":
        signal_scan(conn)
    elif cmd == "stats":
        show_stats(conn)
    elif cmd == "all":
        seed_quotes(conn)
        seed_signals(conn)
        scrape_xinhua(conn, pages)
        scrape_mfa(conn, pages)
        signal_scan(conn)
        show_stats(conn)
    else:
        print(f"未知命令: {cmd}")
        print(USAGE)

    conn.close()


if __name__ == "__main__":
    main()

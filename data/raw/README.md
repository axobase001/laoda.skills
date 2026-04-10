# 数据获取 / Data Acquisition

**[中文](#中文) | [English](#english)**

---

## 中文

本目录只随仓库分发**轻量种子数据**，完整语料需要用户自行获取和构建。

### 随仓库附带的文件

| 文件 | 大小 | 内容 |
|---|---|---|
| `xi_talk.csv` | 2.5 MB | [KengChiChang/xi-talk](https://github.com/KengChiChang/xi-talk) 早期数据集，2012-2017，176 篇精选文章 |
| `umaru_urls.txt` | 3.7 KB | 75 个 jhsjk.people.cn 文章 URL |
| `xxnb_urls.txt` | 6.5 KB | 165 个 jhsjk.people.cn 文章 URL |

### 核心语料（必需，需自行下载）

**[Papersnake/xi_talk](https://huggingface.co/datasets/Papersnake/xi_talk)** —
14,497 篇文章，覆盖 2012-11 至 2025-03 全部时段。132 MB，Parquet → JSONL。

```bash
pip install datasets
python3 -c "
from datasets import load_dataset
ds = load_dataset('Papersnake/xi_talk')
ds['train'].to_json('data/raw/xi_talk_full.json', force_ascii=False)
print(f'总条数: {len(ds[\"train\"])}')
"
```

### 构建数据库

```bash
# 1. 初始化 + 种子数据（语录 20 条 + 信号词典 50 条）
python scraper.py init

# 2. 导入 Papersnake 核心语料（~15 分钟，产出 ~10,000 篇 + ~285,000 条语录）
python import_papersnake.py

# 3. 导入 KengChiChang/xi-talk（可选，补充早期精选数据）
python import_github.py

# 4. 定向抓取新年贺词 + 党代会报告
python collect_speeches.py

# 5. 外交部发言人记者会（可选，补充信号词扫描源）
python scraper.py mfa --pages 29

# 6. 信号扫描 + 统计验证
python scraper.py signal-scan
python scraper.py stats
```

### 预期结果

```
📄 文章:     ~11,000
💬 语录:    ~300,000
📡 信号词:       50
📖 总字数: ~18,000,000
📚 含古典引用: ~60%
```

---

## English

This directory only ships **lightweight seed data**. The full corpus must be
downloaded and built by the user.

### Files included in the repo

| File | Size | Content |
|---|---|---|
| `xi_talk.csv` | 2.5 MB | [KengChiChang/xi-talk](https://github.com/KengChiChang/xi-talk) early dataset, 2012-2017, 176 curated speeches |
| `umaru_urls.txt` | 3.7 KB | 75 jhsjk.people.cn article URLs |
| `xxnb_urls.txt` | 6.5 KB | 165 jhsjk.people.cn article URLs |

### Core corpus (required, download yourself)

**[Papersnake/xi_talk](https://huggingface.co/datasets/Papersnake/xi_talk)** —
14,497 articles covering 2012-11 through 2025-03. 132 MB, Parquet → JSONL.

```bash
pip install datasets
python3 -c "
from datasets import load_dataset
ds = load_dataset('Papersnake/xi_talk')
ds['train'].to_json('data/raw/xi_talk_full.json', force_ascii=False)
print(f'Total records: {len(ds[\"train\"])}')
"
```

### Build the database

```bash
# 1. Initialize + seed data (20 quotes + 50 signal words)
python scraper.py init

# 2. Import Papersnake core corpus (~15 min, yields ~10,000 articles + ~285,000 quotes)
python import_papersnake.py

# 3. Import KengChiChang/xi-talk (optional, early curated data)
python import_github.py

# 4. Scrape New Year addresses + Party Congress reports
python collect_speeches.py

# 5. MFA press briefings (optional, additional signal-scan source)
python scraper.py mfa --pages 29

# 6. Signal scan + stats verification
python scraper.py signal-scan
python scraper.py stats
```

### Expected result

```
📄 Articles:   ~11,000
💬 Quotes:    ~300,000
📡 Signals:        50
📖 Chars:  ~18,000,000
📚 Classical refs: ~60%
```

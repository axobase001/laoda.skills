# 习近平.SKILL 🔍

**[中文](./README.md) | [English](./README_EN.md)**

> 从 **18,244,458 字** 官方语料中提炼政治信号。不猜，不编，用数据说话。

在 **11,001 篇文章、299,824 条语录** 中，我们发现：

- 「**勿谓言之不预**」在 13 年间 **零次出现** —— 这个零本身就是 Lv6 信号
- 「**中方将采取一切必要措施**」2021 年前零次，2022 年后 **33 次** —— regime shift
- 全库包含明确时间 ultimatum 的声明仅 **9 篇 / 0.08%** —— 出现即严重
- 「**强烈不满+严正交涉+强烈抗议**」三连击仅 **2 次 / 0.018%** —— 自动 Lv5

本项目遵循 [AgentSkills 开放标准](https://github.com/anthropics/skills)。

---

## 数据规模

| 指标 | 数值 |
|---|---|
| 文章总数 | **11,001** |
| 语录总数 | **299,824** |
| 总字数 | **18,244,458** |
| 信号词典 | **50** 条（6 级分类，数据验证） |
| 时间跨度 | **2012-11 ~ 2025-03** |
| 含古典引用 | **61%** |
| 数据来源 | 人民网、新华社、外交部、12371 |

---

## 核心发现

### 信号通胀理论 (Signal Inflation)

同一信号词的使用频率上升 → 信号等级下降。外交辞令跟货币一样会通胀。

「强烈不满」2025 年出现 33 次（历史基线 1-3 次），已稀释为模板默认表达。
因此它从 Lv2 降级到 Lv1。**用得越多，信号越弱。**

### 三连击规则

「强烈不满 + 严正交涉 + 强烈抗议」同时出现 = 全库 **2 / 11,001**（0.018%）。

- 2024-01-16 菲律宾总统马科斯恭贺台湾选举（政治领域，两步分述）
- 2025-12-08 日本战斗机闯中方演训区"雷达照射"（军事领域，并列紧凑）

**军事领域语法更紧凑**（"严正交涉**和**强烈抗议"并列）vs 政治领域分步升级——语法结构本身携带信号。

### Ultimatum 规则

中国外交话语几乎从不给 deadline。

「最后期限」+「最后通牒」+「截止」合计 **9 / 11,001**（0.08%）。
任何 ultimatum 式表达出现 → 自动 Lv5，无视前后语气。

机制解释见 `xi-mind` 的 Mental Model #6：**战略耐心**——习近平从不把选项锁死。

### 零出现规则

**Lv6「勿谓言之不预」在全库零次出现。**

历史使用：1962 年对印、1979 年对越——每次出现后都开战。
这个零不是遗漏，是结构性保留。出现即战争倒计时。

### Temporal Pressure（唯一 case）

中英使馆新馆舍拖延 7 年——全库唯一的"时间跨度 + 被动截止日期 + 信用攻击"三要素组合。
这是一种新的信号类型，详见 `xi-decoder/prompts/context_rules.md`。

---

## 三个子 Skill

| Skill | 代号 | 数据基础 | 状态 |
|---|---|---|---|
| 语言模拟器 | `xi-voice` | 299,824 条语录 + 五层表达 DNA | 可用 |
| 决策预测器 | `xi-mind` | 6 套心智模型 + 退让触发框架 | 骨架（`decisions` 表待填） |
| 话语解码器 | `xi-decoder` | **50 条信号词典 + 5 条硬规则 + context_rules.md** | **可用，核心功能** |

---

## 项目结构

```
laoda.skills/                       # 项目显示名: 习近平.SKILL
├── README.md / README_EN.md       # 双语说明
├── ACKNOWLEDGMENTS.md              # 致谢
├── .gitignore
│
├── scraper.py                      # 统一数据库 + MFA 采集器
├── collect_speeches.py             # 新年贺词 + 党代会报告定向抓取
├── import_github.py                # KengChiChang/xi_talk 导入器
├── import_papersnake.py            # Papersnake/xi_talk (HF) 导入器
│
├── xi-voice/                       # Skill 1: 语言模拟器
│   └── SKILL.md
│
├── xi-mind/                        # Skill 2: 决策预测器
│   └── SKILL.md
│
├── xi-decoder/                     # Skill 3: 话语解码器
│   ├── SKILL.md
│   └── prompts/
│       └── context_rules.md        # ✅ 方法论基石（5 条定理）
│
├── shared/                         # 共享资源（传记/意识形态/政治体制）
│
└── data/
    ├── xi_corpus.db                # SQLite 主库 (gitignored, 本地生成)
    └── raw/
        ├── README.md               # 数据获取指南 ← 从这里开始
        ├── xi_talk.csv             # KengChiChang 种子数据 (2.5 MB)
        ├── umaru_urls.txt
        └── xxnb_urls.txt
```

---

## 快速安装

```bash
# 1. Clone 仓库
git clone https://github.com/axobase001/laoda.skills.git
cd laoda.skills

# 2. 装依赖
pip install requests beautifulsoup4 lxml datasets

# 3. 构建数据库（详细步骤见 data/raw/README.md）
python scraper.py init                 # 初始化 + 种子
python import_papersnake.py            # ~15 分钟，产出 ~11000 篇 / ~300000 语录
python scraper.py signal-scan          # 信号扫描
python scraper.py stats                # 验证

# 4. 作为 Claude Code skill 使用
cp -r xi-decoder ~/.claude/skills/xi-decoder
```

完整数据构建流程见 [`data/raw/README.md`](./data/raw/README.md)。

---

## 使用示例

```
# xi-voice: 语言模拟器
你 ❯ /xi-voice 谈谈人工智能
习 ❯ 人工智能是新一轮科技革命和产业变革的重要驱动力量。我们要牢牢把握...

# xi-mind: 决策预测器
你 ❯ /xi-mind 如果台海发生军事冲突，习近平会怎么决策？
分析 ❯ 🎯 核心模型: 历史遗产意识 + 底线思维 | 退让概率分析...

# xi-decoder: 话语解码器
你 ❯ /xi-decoder "中方将采取一切必要措施，坚定维护自身正当合法权益"
解码 ❯ 🔴 信号等级 Lv5 | [中方将采取一切必要措施] 通常 24-72 小时内有行动
         频次分析: 2021 前零次 → 2022 起 33 次，regime shift 信号
```

---

## 数据源

### 公开语料

- 人民网 `jhsjk.people.cn` 金句数据库（经 Papersnake 打包为 HuggingFace 数据集）
- 新华社政策报道
- 外交部发言人记者会实录
- 中国共产党新闻网 12371.cn（新年贺词 + 党代会报告）
- 政府工作报告

### 分析文献

- Kerry Brown, *The World According to Xi*
- Richard McGregor, *The Party*; *Xi Jinping: The Backlash*
- Elizabeth Economy, *The Third Revolution*
- Alice Miller, Joseph Fewsmith 等，*China Leadership Monitor* 系列

详细致谢见 [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md)。

---

## ⚠️ 免责声明

本项目仅供学术研究和娱乐用途。
本人对任何政治人物没有个人立场，亦无任何政治诉求。
请勿用于非法用途。请遵守所在地法律法规。
使用本项目的一切后果由使用者自行承担。

## License

MIT

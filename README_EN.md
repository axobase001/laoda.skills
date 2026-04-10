# xijinping.SKILL 🔍

**[中文](./README.md) | [English](./README_EN.md)**

> Distilling political signals from **18,244,458 characters** of official corpus.
> No guessing, no fabrication — let the data speak.

Across **11,001 articles and 299,824 quotes**, we found:

- **"勿谓言之不预"** (*"Don't say we didn't warn you"*) — **zero occurrences** in 13 years. The zero itself is a Lv6 signal.
- **"中方将采取一切必要措施"** (*"China will take all necessary measures"*) — zero before 2021, **33 times** after 2022. A regime shift.
- Only **9 out of 11,001 statements (0.08%)** contain explicit time ultimatums — rare by design.
- The triple hit **"strong dissatisfaction + stern representations + strong protest"** occurs only **2 times / 0.018%** — automatic Lv5.

This project follows the [AgentSkills open standard](https://github.com/anthropics/skills).

---

## Data Scale

| Metric | Value |
|---|---|
| Total articles | **11,001** |
| Total quotes | **299,824** |
| Total characters | **18,244,458** |
| Signal lexicon | **50** terms (6-level taxonomy, data-validated) |
| Time span | **2012-11 ~ 2025-03** |
| With classical references | **61%** |
| Sources | People's Daily, Xinhua, MFA, 12371 |

---

## Core Findings

### Theorem 1: Signal Inflation

Higher usage frequency of a signal word → lower actual signal level.
Diplomatic rhetoric, like currency, is subject to inflation.

"强烈不满" (*"strong dissatisfaction"*) appeared **33 times** in 2025 vs. a
historical baseline of 1–3 per year. It has been diluted into a boilerplate
template, so we downgraded it from Lv2 to Lv1. **The more it's used, the weaker
the signal.**

### Theorem 2: Triple Hit

"强烈不满 + 严正交涉 + 强烈抗议" appearing together =
**2 out of 11,001** (0.018%) across the entire corpus.

- **2024-01-16** Philippine President Marcos congratulating Taiwan's election
  winner (political, stepwise escalation)
- **2025-12-08** Japanese fighter entering China's exercise zone — "radar
  illumination" incident (military, compact parallel phrasing)

**Military-domain syntax is more compact** ("severe representations **and** strong
protest" in parallel) vs. political domain stepwise escalation — the grammar
itself carries signal.

### Theorem 3: Ultimatum Rule

Chinese diplomatic rhetoric almost never gives deadlines.

"最后期限" + "最后通牒" + "截止" combined = **9 / 11,001** (0.08%).
Any ultimatum-style expression → **automatic Lv5**, regardless of surrounding tone.

The mechanism is explained by Mental Model #6 in `xi-mind`: **Strategic Patience**
— Xi Jinping never locks in his options.

### Theorem 4: Zero Rule

**Lv6 "勿谓言之不预" has zero occurrences across the entire corpus.**

Historical usage: 1962 (vs. India), 1979 (vs. Vietnam) — every time it appeared,
war followed. This zero is not an omission; it's structural reservation.
Its appearance would be a war countdown.

### Theorem 5: Temporal Pressure (single case)

The UK-China embassy construction delay spans **7 years** — the only case in the
entire corpus combining time-span + passive deadline + credit attack.
A new signal type, detailed in `xi-decoder/prompts/context_rules.md`.

---

## The Three Skills

| Skill | ID | Data Foundation | Status |
|---|---|---|---|
| Voice Simulator | `xi-voice` | 299,824 quotes + 5-layer expression DNA | Ready |
| Decision Predictor | `xi-mind` | 6 mental models + retreat-trigger framework | Scaffold (`decisions` table pending) |
| Discourse Decoder | `xi-decoder` | **50-term signal lexicon + 5 hard rules + context_rules.md** | **Ready, core function** |

---

## Project Structure

```
laoda.skills/                        # Display name: 习近平.SKILL
├── README.md / README_EN.md        # Bilingual docs
├── ACKNOWLEDGMENTS.md               # Credits
├── .gitignore
│
├── scraper.py                       # Unified DB + MFA scraper
├── collect_speeches.py              # New Year + Party Congress targeted scraper
├── import_github.py                 # KengChiChang/xi_talk importer
├── import_papersnake.py             # Papersnake/xi_talk (HF) importer
│
├── xi-voice/                        # Skill 1: Voice Simulator
│   └── SKILL.md
│
├── xi-mind/                         # Skill 2: Decision Predictor
│   └── SKILL.md
│
├── xi-decoder/                      # Skill 3: Discourse Decoder
│   ├── SKILL.md
│   └── prompts/
│       └── context_rules.md         # ✅ Methodology cornerstone (5 theorems)
│
├── shared/                          # Shared resources (bio / ideology / polity)
│
└── data/
    ├── xi_corpus.db                 # SQLite main DB (gitignored, built locally)
    └── raw/
        ├── README.md                # Data acquisition guide ← start here
        ├── xi_talk.csv              # KengChiChang seed data (2.5 MB)
        ├── umaru_urls.txt
        └── xxnb_urls.txt
```

---

## Quick Install

```bash
# 1. Clone the repo
git clone https://github.com/axobase001/laoda.skills.git
cd laoda.skills

# 2. Install dependencies
pip install requests beautifulsoup4 lxml datasets

# 3. Build the database (detailed steps in data/raw/README.md)
python scraper.py init                 # Initialize + seed data
python import_papersnake.py            # ~15 min, yields ~11000 articles / ~300000 quotes
python scraper.py signal-scan          # Signal scan
python scraper.py stats                # Verify

# 4. Use as a Claude Code skill
cp -r xi-decoder ~/.claude/skills/xi-decoder
```

Full data-build workflow: see [`data/raw/README.md`](./data/raw/README.md).

---

## Usage Examples

```
# xi-voice: Voice Simulator
you ❯ /xi-voice talk about artificial intelligence
xi  ❯ 人工智能是新一轮科技革命和产业变革的重要驱动力量。我们要牢牢把握...
      (AI is a key driver of the new scientific and industrial revolution...)

# xi-mind: Decision Predictor
you ❯ /xi-mind If military conflict breaks out in the Taiwan Strait, how would Xi Jinping decide?
analysis ❯ 🎯 Core models: Historical Legacy + Bottom-Line Thinking | Retreat probability analysis...

# xi-decoder: Discourse Decoder
you ❯ /xi-decoder "中方将采取一切必要措施，坚定维护自身正当合法权益"
decoded ❯ 🔴 Signal Lv5 | [China will take all necessary measures] typically means action within 24-72h
           Frequency: zero before 2021 → 33 after 2022, regime shift signal
```

---

## Data Sources

### Public corpora

- People's Daily `jhsjk.people.cn` (packaged as HuggingFace dataset by Papersnake)
- Xinhua News Agency policy coverage
- MFA spokesperson press briefing transcripts
- 12371.cn (New Year addresses + Party Congress reports)
- Government Work Reports

### Analytical literature

- Kerry Brown, *The World According to Xi*
- Richard McGregor, *The Party*; *Xi Jinping: The Backlash*
- Elizabeth Economy, *The Third Revolution*
- Alice Miller, Joseph Fewsmith et al., *China Leadership Monitor* series

Full credits in [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md).

---

## ⚠️ Disclaimer

This project is for academic research and entertainment only.
The author holds no personal political stance and makes no political claims.
Do not use for illegal purposes. Comply with the laws of your jurisdiction.
Users are solely responsible for any consequences of their use.

## License

MIT

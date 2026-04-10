# 习近平.SKILL 🐻

> 把习近平「蒸馏」成三个 AI Skill：说什么、为什么说、下一步会做什么。

本项目遵循 [AgentSkills 开放标准](https://github.com/anthropics/skills)。

## 三个子 Skill

| Skill | 代号 | 定位 | 一句话 |
|-------|------|------|--------|
| 语言模拟器 | `xi-voice` | 娱乐 | 输入话题，输出习式讲话 |
| 决策预测器 | `xi-mind` | 实用 | 输入情境，预判决策走向和退让条件 |
| 话语解码器 | `xi-decoder` | 分析 | 输入官方文本，解码政治信号 |

## 项目结构

```
xi-skill/
├── README.md
├── xi-voice/                    # Skill 1: 语言模拟器
│   ├── SKILL.md
│   ├── prompts/
│   │   ├── xi_persona.md        # 人格定义（表达DNA）
│   │   └── style_guide.md       # 句式模板、修辞模式
│   ├── tools/
│   │   ├── quote_db.py          # 语录数据库
│   │   └── scraper.py           # 语料采集（新华社/学习强国）
│   └── data/
│       ├── xi_quotes.db         # SQLite 语录库
│       └── classical_refs.json  # 古诗词典故引用库
│
├── xi-mind/                     # Skill 2: 决策预测器
│   ├── SKILL.md
│   ├── prompts/
│   │   ├── mental_models.md     # 心智模型（6-8套）
│   │   ├── decision_instincts.md # 决策本能
│   │   └── retreat_triggers.md  # 退让触发条件
│   ├── tools/
│   │   └── scenario_analyzer.py # 情境分析引擎
│   └── data/
│       ├── decisions_timeline.json  # 关键决策时间线
│       └── personnel_patterns.json  # 人事任命模式
│
├── xi-decoder/                  # Skill 3: 话语解码器
│   ├── SKILL.md
│   ├── prompts/
│   │   ├── signal_lexicon.md    # 政治信号词典
│   │   └── context_rules.md    # 语境解读规则
│   ├── tools/
│   │   └── decoder.py           # 文本解码引擎
│   └── data/
│       ├── signal_dict.json     # 信号词 → 含义映射
│       └── historical_signals.json # 历史信号案例库
│
├── shared/                      # 共享资源
│   ├── biography.md             # 人物传记摘要
│   ├── ideology_map.md          # 意识形态图谱
│   └── china_context.md         # 中国政治体制速查
│
└── requirements.txt
```

## 快速安装

```bash
# Claude Code 全局安装
git clone https://github.com/YOUR_USERNAME/xi-skill.git ~/.claude/skills/xi-skill

# 或单独安装某个子 skill
cp -r xi-skill/xi-voice ~/.claude/skills/xi-voice
```

## 使用示例

```
# xi-voice: 语言模拟器
你 ❯ /xi-voice 谈谈人工智能
习 ❯ 人工智能是新一轮科技革命和产业变革的重要驱动力量。我们要牢牢把握...

# xi-mind: 决策预测器
你 ❯ /xi-mind 如果台海发生军事冲突，习近平会怎么决策？
分析 ❯ 🟢 退让概率: 低 | 触发条件分析...

# xi-decoder: 话语解码器
你 ❯ /xi-decoder "要坚持底线思维，做好较长时间应对外部环境变化的思想准备和工作准备"
解码 ❯ 信号等级: 🟡 中度预警 | 关键词拆解...
```

## 数据源

### 公开语料
- 新华社全文数据库
- 学习强国APP语料
- 政府工作报告（2013-至今）
- 新年贺词全文
- 党代会报告（十八大、十九大、二十大）
- 外交部记者会实录

### 分析文献
- Kerry Brown《习近平：无所适从的强人》《The World According to Xi》
- Richard McGregor《The Party》《Xi Jinping: The Backlash》
- Elizabeth Economy《The Third Revolution》《The World According to China》
- 《习近平谈治国理政》（一至四卷，官方出版）
- Alice Miller, Joseph Fewsmith 等人的 China Leadership Monitor 系列分析

### 行为数据
- 反腐运动打击时间线与人事关联
- 一带一路项目启停数据
- COVID 清零→放开决策时间线
- 对台军演与外交信号时间线
- 中美博弈关键节点

## ⚠️ 免责声明

本项目仅供学术研究和娱乐用途。
本人对任何政治人物没有个人立场，亦无任何政治诉求。
请勿用于非法用途。请遵守所在地法律法规。
使用本项目的一切后果由使用者自行承担。

## License

MIT

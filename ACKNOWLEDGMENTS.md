# 致谢 / Acknowledgments

本项目的语料数据来自以下开源贡献者和数据集，在此致以诚挚感谢。
This project's corpus comes from the following open contributors and datasets. Sincere thanks to all of them.

## 核心语料 / Core Corpora

- **[Papersnake/xi_talk](https://huggingface.co/datasets/Papersnake/xi_talk)**
  14,497 篇文章，覆盖 2012-2025，源自人民网金句数据库 (jhsjk.people.cn) 完整快照。
  本项目的信号分析、时序发现和方法论验证均基于此数据集。
  这是目前公开可获取的最完整的习近平相关中文语料库。

  14,497 articles covering 2012–2025, a complete snapshot of the People's Daily
  "jhsjk" database. This is the largest publicly available Chinese corpus on the
  subject, and all signal analysis, temporal discoveries, and methodology
  validation in this project are built on it.

- **[KengChiChang/xi-talk](https://github.com/KengChiChang/xi-talk)**
  早期 xi_talk.csv（2012-2017），176 篇精选文章。
  本项目的第一批导入数据，验证了数据管线的可行性。

  Early xi_talk.csv (2012-2017), 176 curated articles. The first dataset
  imported in this project; it validated the data pipeline end-to-end.

## 新年贺词 & 党代会报告 / New Year Addresses & Party Congress Reports

- **中国共产党新闻网 (12371.cn)** — 新年贺词全文（2013-2025）及十九大、二十大报告。
  New Year addresses (2013-2025), 19th and 20th Party Congress reports.

## 外交部发言人语料 / MFA Spokesperson Corpus

- **中华人民共和国外交部 (mfa.gov.cn)** — 发言人定期记者会实录。
  Regular press briefing transcripts.

## 分析方法参考 / Methodology References

- **[KirinJin2046/trump-skill](https://github.com/KirinJin2046/trump-skill)**
  Trump 决策预测模型的架构设计和 TACO 分析框架为 xi-mind 的心智模型方法论
  提供了直接参考，特别是"退让触发条件四要素"框架。

  The TACO analysis framework and decision-prediction architecture in trump-skill
  directly informed xi-mind's mental-model methodology, especially the
  "four retreat triggers" framework.

- **[wwwttlll/Trump-skill](https://github.com/wwwttlll/Trump-skill)**
  AgentSkills 标准的政治人物语言模拟 skill 先例，五层人格定义的结构设计启发了 xi-voice。

  The pioneering political-persona skill under the AgentSkills standard; the
  five-layer persona structure inspired xi-voice.

- **[HughYau/qiushi-skill](https://github.com/HughYau/qiushi-skill)**
  将政治方法论转化为 AI agent 技能的先驱项目。
  "这不是 Politics，这是 Methodology"——我们深以为然。

  A pioneering attempt at turning political methodology into AI agent skills.
  *"This is not Politics, this is Methodology"* — a sentiment we wholeheartedly share.

## 研究文献 / Research Literature

信号词典和心智模型的构建参考了以下学术著作。
The signal lexicon and mental models draw on the following scholarship:

- Kerry Brown, *The World According to Xi*; 《习近平：无所适从的强人》
- Richard McGregor, *The Party*; *Xi Jinping: The Backlash*
- Elizabeth Economy, *The Third Revolution*; *The World According to China*
- Alice Miller, Joseph Fewsmith, et al., *China Leadership Monitor* series

## 工具 / Tools

- 本项目构建过程中使用了 [Claude](https://claude.ai) (Anthropic) 进行数据分析、
  信号词典设计和方法论推演。数据采集和导入脚本由 Claude Code (Wren) 编写。

  This project was built with [Claude](https://claude.ai) (Anthropic) for data
  analysis, signal-lexicon design, and methodology reasoning. The scraping and
  import scripts were written by Claude Code (Wren).

---

*本项目仅供学术研究用途。所有语料均来自公开渠道。*
*This project is for academic research only. All corpora come from publicly available sources.*

# doc-organization

OpenClaw skill，管文档 / 知识库整理的：分区、索引、命名、归档、体检。

An OpenClaw skill that keeps your documents and knowledge base in order — zones, one index, fixed naming, an archive flow, and a read-only audit script.

## For agents: install in one step

If you are an OpenClaw agent and the user asked you to install this skill, run:

```bash
git clone --depth 1 https://github.com/foxcueva/doc-organization.git ~/.openclaw/workspace/skills/doc-organization
```

Then tell the user to start a new session (skill metadata reloads on new session). No config, no dependencies.

## 它解决什么

为文档归纳提供一种便捷方式。

1. **先分区，再动手** —— 每个文件先判定属于「流水 / 活数据 / 知识 / 冷档」哪一层。层定了，放哪、能不能删、要不要进索引，就全定了
2. **索引只有一个入口** —— 人只看索引（MOC），要用哪条再点开。索引一过期，整个库等于白建
3. **命名不靠灵感** —— 日期、序号、关键词三件套，照着写就行
4. **改完内容当轮补索引** —— 内容和索引一起改完，不隔夜

## 四层分区（判定表）

| 层 | 目录 | 放什么 | 判定问句 | 生命周期 |
|---|---|---|---|---|
| 流水 | `memory/YYYY-MM-DD.md` | 当天发生的事、对话脉络、踩坑 | 「三个月后还会查吗？」 | 长期，季度蒸馏 |
| 活数据 | `data/` | 会变的清单、进度、账目、码表 | 「它会变吗？」 | 头部写录入时间 + 时效 |
| 知识 | `knowledge/<域>/` | 可复用的方法、口径、流程 | 「下次还要用吗？」 | 长期，90 天未读标休眠 |
| 冷档 | `archive/<域>/` | 原件、完成的项目、失效条目 | 「还会改吗？」 | 只增不改 |

最容易犯的错：把时效性数据当知识存。价格、榜单、卡组码、追踪表 → 一律 `data/`；知识库里只放「怎么判断」这类能复用的东西。

## 目录

```
doc-organization/
├── SKILL.md                      # 触发词、分区判定、流程、收尾清单
├── README.md                     # 当前你正在看的
├── references/
│   └── anti-patterns.md          # 8 条真实反例（垃圾桶索引 / 归档当删除 …）
└── scripts/
    └── kb_audit.py               # 只读体检：孤儿 / 死链 / 超重 / 缺索引
```

## 快速验证

```bash
python3 scripts/kb_audit.py --root ~/.openclaw/workspace/knowledge
```

只读，不动文件。输出四类问题：

- **孤儿**：文件在，但没有索引提到它
- **死链**：索引里写了，文件却不存在
- **超重**：单文件 >20KB（`--max-kb` 可调）
- **缺索引**：子目录没有 `00-索引.md`

退出码 0 表示干净，1 表示要整理，挂 CI 或 cron 正合适。


## License

MIT
# MQWW × CBDB 女性人物与作品关系网络 — Handoff

> 更新时间：2026-08-23
> 项目目录：`/Users/sousekilyu/Documents/Github/women-poets-imperial-china`
> 本文用于把当前阶段的研究设计、已完成工作、验证结果和后续任务交给下一次会话/协作者。

当前 public 网站：<https://sousekil.github.io/women-poets-imperial-china/>

## 1. 项目目标

以 MQWW（Ming Qing Women's Writings）中的女性人物为主体，尽可能匹配到 CBDB 人物 ID，提取 CBDB 的亲缘与社会关系，并以 MQWW 的作品为入口，查看作品关联女性及其分层关系网络。

核心研究原则：

- 姓名相同不是同一人物的充分证据；所有后续连接使用 `poetID` / `c_personid`，不能按姓名继续 join。
- CBDB 直接关系、MQWW 作品—人物关系、作品—诗作—人物传递关系必须分层保存。
- 共同收录或共同出现不等于现实社会关系。
- 中心度表示数据库记录中的连接结构，不直接等同于历史影响力。
- 所有匹配和边都应保留来源记录、证据、置信度和推导规则。
- 原始 CBDB/MQWW 数据库不进入 public GitHub 仓库。

## 2. 计划路线

### 当前状态摘要（2026-08-22）

- 关系 code、方向、籍贯口径审计：已完成，见 `research-validity/01-codebook-semantics`。
- KIN/ASSOC 规范化分层网络：已完成并集成主 worktree；KIN typed-undirected 318,397，ASSOC typed-undirected 84,233。
- KIN/ASSOC 中心性 v2：已完成；typed degree、投影路径指标和无向 k-core 分开记录。
- 稳健性审查：B3 输入计数差异已解决；B1 路径采样不稳定、B2 来源/年份缺失、B4 strength 命名边界仍限制强历史解释。
- 证据卡：KIN/ASSOC 首轮 15 张、作品层第二轮 13 张已完成，raw/edge 追溯资产已保存。
- 作品层中心性：已完成；`work_direct` 3,242 边、`work_via_poem` 87,874 边；via 层 3,999 首无作者诗作为限制记录。
- 人工匹配验证：`02-human-validation` 已启动但尚未产生人工金标准；L3 仍等待评价口径。

### 阶段 A：资料审计与安全边界（已完成）

1. 确认实际数据位置、文件版本、大小和重复副本。
2. 检查 MQWW CSV 与 Access 数据规模和字段。
3. 区分原始资料与仓库派生数据。
4. 记录来源、引用和公开发布限制。

### 阶段 B：人物匹配（L0/L1/L2 已完成）

1. L0：排除 `無名氏`、`王氏` 等泛称。
2. L1：`NameHZ == c_name_chn` 精确姓名基线，结合 `c_female` 和候选唯一性分级。
3. L2：使用 MQWW 字、号、其他字号查询 `ALTNAME_DATA` 和 `CBDB_NAME_LIST`。
4. 年代、地域和真重名的进一步消歧仍待做。

### 阶段 C：关系与作品网络（第一版已完成）

1. 核对 `KIN_DATA`、`ASSOC_DATA` 和真实 code 表。
2. 提取 A 级女性的 CBDB 亲缘/社会直接边。
3. 构建 MQWW 作品—人物二部边。
4. 构建作品—诗作—人物传递边。
5. 为所有节点和边保存来源及推导规则。

### 阶段 D：网站 MVP（第一版已完成，需继续验收和改进）

1. 纯静态 HTML + Canvas + 原生 JavaScript。
2. 加载仓库内派生 CSV，不连接原始数据库。
3. 人物搜索、作品选择、关系层筛选、详情面板。
4. 作品选择后高亮相关人物。
5. 页面明确显示数据来源、匹配置信度和研究限制。

### 阶段 E：研究质量与发布（待完成）

1. L2 候选人工复核和抽样精确率/召回率评估。
2. L3 姓+名拆分匹配。
3. 核对籍贯编码和关系编码的研究口径。
4. B 级人物的敏感度分析。
5. 网络指标、社区和时间分析。
6. 网站性能优化、可访问性测试和 GitHub Pages 发布。

## 3. 已完成文件

### 数据与方法文档

- `data/README.md`
  - 外部原始数据实际路径、来源、版本、大小和公开限制。
  - 原始资料不复制入仓库的规则。
- `docs/data_dictionary.md`
  - CBDB/MQWW 实测规模和字段口径。
  - 注意：`c_addr_type == 1` 作为籍贯仍应与 `ADDR_CODES` 进一步核对。
- `docs/matching_method.md`
  - L0/L1/L2 方案、A/B/C/D 置信度、风险与验证设计。
- `docs/review_network_design.R`
  - 网络层和可视化的设计审查记录。
  - 其中关系类型的部分映射属于建议，正式分析前仍需以 code table 和数据字典为准。

### 匹配管线

- `python/match_mqww_cbdb.py`
  - L0/L1；CBDB 用 SQLite `file:<path>?mode=ro` 和 `PRAGMA query_only=ON`。
- `python/test_match_mqww_cbdb.py`
  - 标准库 unittest。
- `python/match_mqww_cbdb_l2.py`
  - L2 字、号、别名召回；别名命中不会自动升级为 A。
- `python/test_match_mqww_cbdb_l2.py`
- `python/README.md`

### 派生匹配结果

- `data/derived/person_matches_baseline.csv`
- `data/derived/match_baseline_summary.txt`
- `data/derived/person_matches_l2_candidates.csv`
- `data/derived/match_l2_summary.txt`

### 关系网络管线与结果

- `python/build_network_derived.py`
- `data/derived/network/network_nodes.csv`
- `data/derived/network/direct_edges.csv`
- `data/derived/network/work_nodes.csv`
- `data/derived/network/work_person_edges.csv`

### 网站 MVP

- `index.html`
- `assets/app.js`
- `assets/style.css`

网站读取：

```text
data/derived/network/network_nodes.csv
data/derived/network/direct_edges.csv
data/derived/network/work_nodes.csv
data/derived/network/work_person_edges.csv
```

## 4. 已验证的真实结果

### 原始资料审计

实际外部资料位于：

```text
/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/
├── cbdb202409.db
├── latest.7z
├── mqww_2023.accdb
└── mqww_mingqing_women_writings/cycle/
```

主要规模：

- CBDB `BIOG_MAIN`：641,568 行；女性标记约 55,889 行。
- CBDB `KIN_DATA`：540,631 行。
- CBDB `ASSOC_DATA`：187,878 行。
- MQWW `poet.csv`：7,751 行。
- MQWW `poem.csv`：92,094 行。
- MQWW `work.csv`：431 行。

`latest.7z` 内的 `latest.db` 与 `cbdb202409.db` 疑似同版本副本；删除前仍应自行计算 SHA-256，当前没有删除。

### L1 基线

全量运行结果：

```text
MQWW 记录：7,751
唯一 NameHZ：7,612
C（L0 泛称）：144
A：3,140
B：3,001
D：1,466
L1 命中 A+B：6,141（79.2%）
女性标记命中：4,295（55.4%）
```

### L2 别名召回

全量状态严格合计 7,751：

```text
existing_l1_match：6,141
skip_l0：144
review_multi_candidate：344
review_unique_female：49
review_unique_nonfemale：77
no_alias_match：228
no_alias_value：768
```

新增待复核候选共 470 条。它们不是确认匹配。

### 网络派生数据

```text
network_nodes.csv：11,935
直接关系 direct_edges.csv：12,407
  kin：9,268
  assoc：3,139
作品 work_nodes.csv：441
作品—人物 work_person_edges.csv：91,116
  direct：3,242
  via_poem：87,874
```

独立检查结果：

- 四个文件行数与报告一致；
- `direct_edges.csv` 的 `relation_label_chn` 缺失数为 0；
- `source_record_id` 缺失数为 0；
- 节点引用完整性报告为 0 缺失；
- 原始 Data 目录未修改。

### 测试与网站 smoke test

L1 测试：

```bash
PYTHONPATH=python python3 -m unittest -v python/test_match_mqww_cbdb.py
```

结果：8 项通过。

L2 测试：

```bash
PYTHONPATH=python python3 -m unittest -v python/test_match_mqww_cbdb_l2.py
```

结果：2 项通过。

网站静态服务器验证：

```bash
cd /Users/sousekilyu/Documents/Github/women-poets-imperial-china
/opt/homebrew/bin/python3.14 -m http.server 8877
```

已确认 HTTP 200：

- `index.html`
- `assets/app.js`
- `assets/style.css`
- 四个网络派生 CSV

说明：端口 8765/8766 已被其他服务占用或启动上下文不正确，因此使用 8877 完成验证。浏览器交互和 Canvas 视觉效果尚未完成端到端人工验收。

GitHub Pages 已启用，来源为 `main` 分支根目录；本次推送后已确认状态为 `built`。线上验证返回 HTTP 200：

```text
https://sousekil.github.io/women-poets-imperial-china/
```

已验证线上资源：

```text
index.html
assets/app.js
data/derived/network/network_nodes.csv
```

## 5. 当前工作区与 Git 状态

此前的论文和分析资料已经完整移动到 `backup/legacy-research/`，包括旧根目录文档、R 脚本、`style/`、`output/`、旧 R 数据对象以及 Agent/editor 配置目录。当前仓库存在先前已有的未提交改动，包括：

```text
（此前旧文件已归档；本次新增文件仍未提交。）
```

本阶段新增的文档、脚本、派生数据、网站文件和 `backup/legacy-research/` 归档内容尚未提交或推送。提交前必须逐项检查，不要盲目执行 `git add .`。

仓库是：

```text
https://github.com/SousekiL/women-poets-imperial-china
```

当前已知为 public，remote 已关联。


## 6. Git 与 iCloud 超时记录

最近已确认成功提交并推送：

```text
70cb715 docs: refine work type network evidence notes
```

`main` 与 `origin/main` 当前同步。`docs/wang-zhenyi-wechat-article-outline.md` 已增加别集、合刻、总集三类作品网络的公众号章节、可复算数字和安全图注。

本仓库位于 iCloud 同步目录，之前出现过两类 Git 异常：

1. `.git/index.lock` 导致提交失败；
2. iCloud 同步 `.git/objects/pack/*.pack` 时发生 `Operation timed out`，一度无法确认提交/推送状态。

后续检查确认文档提交已创建并成功推送。遇到同类问题时：

- 不要强制覆盖 `.git`；
- 不要删除 `.git/objects/pack`；
- 不要执行 `git reset --hard`；
- 等待 iCloud 完成本地化，或将仓库迁移到非 iCloud 目录后再操作；
- 只有确认没有运行中的 Git 进程时，才处理残留的 `index.lock`。

提交前检查：

```bash
git status --short --branch
ls -l .git/index.lock 2>/dev/null || true
ps aux | grep '[g]it'
```

当前工作区仍有与本次文档提交无关的未提交修改，包括 `.DS_Store`、部分网络派生数据、`python/build_network_derived.py`。`docs/mvp_handoff.md` 已在本次 handoff 文档提交中纳入；其余文件不得在更新 handoff 时一并提交，不要使用 `git add .`。

## 7. 在其他软件中打开项目

如果使用 VS Code、Cursor、Zed 或其他代码编辑器，选择仓库根目录：

```text
/Users/sousekilyu/Documents/Github/women-poets-imperial-china
```

截图中的 `New worktree` 不是打开当前项目的必要选项。除非明确需要隔离开发分支，否则选择 `Local`，打开上面的项目根目录，并继续使用 `main` 分支。

不要选择或直接打开：

```text
.git/
backup/legacy-research/
/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/
```

原始 CBDB/MQWW 数据目录必须保持本地只读，不能复制到项目或 public GitHub。

只查看线上网站：

```text
https://sousekil.github.io/women-poets-imperial-china/
```

本地运行网站：

```bash
cd /Users/sousekilyu/Documents/Github/women-poets-imperial-china
python3 -m http.server 8877
```

然后访问 `http://127.0.0.1:8877/`。继续开发前先阅读 `README.md`、`docs/HANDOFF.md` 和 `docs/data_dictionary.md`；只提交明确属于当前任务的文件。

## 8. 后续 TODO（按优先级）

### P0：先解决数据与研究质量

- [ ] 核对 `KINSHIP_CODES`、`ASSOC_CODES` 的完整语义和方向，不只看中文标签。
- [ ] 核对 `BIOG_ADDR_DATA.c_addr_type` 与 `ADDR_CODES`，确认籍贯口径。
- [ ] 对 L2 的 470 条候选进行分层抽样人工复核。
- [ ] 为 A/B/C/D 各抽样至少 30 条，记录姓名、年代、地域和原始来源证据。
- [ ] 计算基于人工样本的 precision/recall，并修订匹配规则。
- [ ] 实现 L3 姓+名拆分匹配，但不得自动提升置信度。
- [ ] 明确 `confidence` 是研究工作流分数，不是历史事实概率。

### P1：完善网络数据

- [ ] 把关系边按 kin、assoc、work_direct、work_via_poem 分层导出 JSON。
- [ ] 增加边的时间字段和时间精度标志。
- [ ] 明确 direct/reversed 的展示语义，避免把记录方向误当作关系语义方向。
- [ ] 为作品—人物边保留 role、date、wcID/wpID/poemID 的可读来源信息。
- [ ] 评估是否纳入 B 级女性，并与 A-only 结果做敏感度比较。
- [ ] 抽查网络中高连接人物，回到原始 CBDB 记录进行证据卡片核验。

### P1：完善网站 MVP

- [ ] 修复根目录测试入口，使 `python3 -m unittest discover` 能运行全部 Python 测试。
- [ ] 优先将 CSV 转成轻量 JSON 或按作品/朝代分片，减少浏览器解析 10 MB CSV 的开销。
- [ ] 作品筛选后同时显示作品相关女性和她们的 CBDB 关系邻居；当前第一版主要显示作品相关节点。
- [ ] 增加边详情面板：relation code、中文标签、source record、derivation rule、confidence。
- [ ] 加入作品关系类型筛选：作者/序作者/题辞/主要作者/经诗作传递。
- [ ] 增加加载失败、空结果和孤儿节点的明确提示。
- [ ] 做键盘操作、移动端布局、颜色对比度和 Canvas 替代文本检查。
- [ ] 在真实浏览器中验收搜索、作品选择、图层切换和节点详情。
- [ ] 检查 GitHub Pages 部署状态和线上页面内容。

### P2：研究分析与发布

- [ ] 分别计算各层 degree/strength、betweenness、closeness、PageRank、k-core。
- [ ] 比较不同关系层和 A/B 匹配阈值下的排名稳定性。
- [ ] 进行文献记录强度偏差诊断。
- [ ] 做年代窗口、地域和社区分析，并披露缺失年代的影响。
- [ ] 清理或确认现有工作区改动后，再有选择地提交。
- [ ] 检查数据许可、引用和派生数据公开范围。
- [ ] 配置 GitHub Pages 前先进行 public 发布前审查；绝不上传原始 CBDB/MQWW 数据库。

## 7. 推荐恢复/继续命令

从仓库根目录：

```bash
# 查看状态，勿使用 git add .
git status --short

# 运行匹配测试
PYTHONPATH=python python3 -m unittest -v python/test_match_mqww_cbdb.py
PYTHONPATH=python python3 -m unittest -v python/test_match_mqww_cbdb_l2.py

# 重新生成 L1/L2 派生结果（只读外部库）
python3 python/match_mqww_cbdb.py
python3 python/match_mqww_cbdb_l2.py

# 重新生成关系网络
python3 python/build_network_derived.py

- 本地查看网站
/opt/homebrew/bin/python3.14 -m http.server 8877
# 浏览器打开 http://127.0.0.1:8877/

# 线上网站
# https://sousekil.github.io/women-poets-imperial-china/
```

## 8. 不要做的事情

- 不要把 `cbdb202409.db`、`latest.7z`、`mqww_2023.accdb` 或全量原始 CSV 加入 public repo。
- 不要删除重复副本，除非先做 SHA-256 并确认可回滚。
- 不要按姓名直接连接后继续分析。
- 不要把共同作品/诗作关系写成现实社会关系。
- 不要把中心度写成历史影响力。
- 不要清理或覆盖本 handoff 创建前已经存在的工作区改动。

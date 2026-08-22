# MQWW 女性诗人 → CBDB 人物 匹配分层方案

> 目标：把 MQWW `poet.csv` 的女性诗人（键 `poetID`/`NameHZ`）映射到 CBDB 人物（键 `c_personid`），用于亲属/社会网络与出版数据的联合分析。
> 版本：v1（2026-08-22）。基线数据为当日只读实测。

## 1. 输入与键

| 数据 | 键 | 匹配字段 |
|------|----|---------|
| MQWW poet.csv（7,751 行，7,612 个唯一 NameHZ） | poetID | NameHZ、ZiHZ、HaoHZ、OtherZiHaoHZ、StartYear/EndYear |
| CBDB BIOG_MAIN（641,568 行，475,566 个唯一 c_name_chn） | c_personid | c_name_chn、c_female、c_birthyear/c_deathyear、c_choronym_code |
| CBDB ALTNAME_DATA（196,850 行） | c_personid | c_alt_name_chn（字/号/别称） |
| CBDB CBDB_NAME_LIST（2,046,020 行） | c_personid | name（含别名/异写索引） |
| CBDB BIOG_ADDR_DATA + ADDR_CODES | c_personid | 籍贯（c_addr_type==1，注意该假设需核对） |
| MQWW cycle.csv / region.csv | — | 公历年份转换（1368–1911）、今地对照 |

## 2. 分层匹配管线

按层依次执行，高层（置信度强）优先，低层仅在高层未命中或需消歧时启用：

### L0 预筛：泛称排除
- `NameHZ ∈ {無名氏, 王氏, 李氏, 張氏, …}` 等无唯一标识的泛称记录（89 组、139 条，占 poet.csv 1.8%）。
- 处理：默认排除出自动匹配；如需保留，仅作弱证据，不进入网络分析。

### L1 精确姓名匹配（基线）
- 规则：`NameHZ == c_name_chn` 且 `c_female == 1` → **A 级（高置信）**。
- 实测：7,612 个唯一名中 **6,129（80.5%）** 命中 BIOG_MAIN.c_name_chn；其中 **4,292（56.4%）** 落在女性记录（c_female=1）内。
- 若 `NameHZ` 精确命中但 CBDB 无女性标记 → 降为 B 级（见第 3 节），人工复核。

### L2 别名扩展（提高召回）
- 用 `ZiHZ`（字）、`HaoHZ`（号）、`OtherZiHaoHZ` 匹配 `ALTNAME_DATA.c_alt_name_chn`，或直接查 `CBDB_NAME_LIST`。
- 命中后回连 BIOG_MAIN 验证 c_female 与年代窗口。
- 预期：在 L1 基础上再提升数个百分点的召回（别名命中需 A/B 分级复核）。

### L3 结构拆分匹配（兜底）
- 将 `NameHZ` 拆为 姓+名，匹配 `c_surname_chn + c_mingzi_chn`（仅当 CBDB 姓名分字段完整时）。
- 仅用于 L1/L2 未命中且姓名结构清晰的记录。

### 消歧约束（作用于 L1–L3）
1. **朝代窗口**：取 MQWW `StartYear`–`EndYear`（缺失时用 cycle.csv 的 1368–1911 全窗），要求 CBDB `c_fl_earliest_year`/`c_fl_latest_year` 与之相容。
2. **籍贯**：MQWW `regionID` → 今地 → CBDB `BIOG_ADDR_DATA(c_addr_type==1)` 地址，匹配加分；冲突时降级。
3. **女性标记**：`c_female==1` 为强证据；非女性命中必须有日期+籍贯双证据才接受。
4. **真重名**（如 沈英×3、吳蕙×3）：同一 NameHZ 对应多个 c_personid 时，必须按日期/地区交叉验证后择一，否则保留多映射并标记人工复核。

## 3. 置信度分级

| 级别 | 定义 | 使用 |
|------|------|------|
| A | 精确姓名 + c_female=1 + 唯一命中（或消歧后唯一） | 直接进入网络分析 |
| B | 精确姓名但非女性，或别名命中、或多人候选 | 需人工复核或仅用于敏感度分析 |
| C | 泛称/无唯一标识（L0） | 排除 |
| D | 未命中（L1–L3 均失败） | 记录未匹配原因，不丢弃 |

## 4. 验证与评估

1. **抽样人工核对**：每级各抽 ≥30 条，核对姓名、年代、籍贯与来源（BIOG_SOURCE_DATA）。
2. **指标**：报告精确率（P）/召回率（R）——以人工核对样本为基准；L1 实测基线 P≈100%（精确字符串），R 受限于 CBDB 收录覆盖。
3. **覆盖度报告**：输出 `poetID, c_personid, level(A/B/C/D), evidence{name,year,region}` 映射表（CSV），写入仓库派生数据（不含原始库内容）。
4. **往返验证**：映射表反向统计每个 c_personid 命中的 MQWW poetID 数，发现一对多异常。

## 5. 风险与陷阱

- **共同收录 ≠ 现实关系**：两库"同时收录"某诗人不等于库内关系字段存在；关系分析只应使用 KIN_DATA/ASSOC_DATA 的显式边。
- **异体字/繁简**：CBDB 用繁体，MQWW 亦繁体为主，但仍需归一化（如 著/着、并/並）再匹配。
- **泛称与假名**：無名氏/某氏类记录无法可靠匹配，误匹配会污染网络。
- **同名不同人**：明清同名女性常见，无日期/籍贯证据的匹配一律降级。
- **覆盖偏差**：CBDB 对女性（尤其普通民妇）收录不完整；未命中不代表人物不存在，报告中须披露未匹配率（实测基线：精确命中率 80.5%，女性记录内 56.4%）。

## 6. 实施建议

- 用 ID 列（poetID/c_personid）做所有连接，**绝不按姓名做后续 join**。
- 匹配脚本设为只读访问 CBDB（`mode=ro` URI），输出仅派生映射表。
- 映射表随成果保留，便于复现与同行复核。

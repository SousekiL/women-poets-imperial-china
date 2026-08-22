# 数据字典 — CBDB / MQWW 字段口径

> 字段口径基于 2026-08-22 只读审计实测（`PRAGMA table_info` 与 CSV 解析），对应文件见 `data/README.md`。
> 原始库路径：`/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/`

## 1. 规模总表（实测行数）

### 1.1 CBDB（cbdb202409.db，SQLite）

| 表 | 行数 | 用途 |
|----|------|------|
| BIOG_MAIN | 641,568 | 人物基本信息（56 字段，含女性标记） |
| CBDB_NAME_LIST | 2,046,020 | 人物姓名索引（c_personid, name, source） |
| POSTING_DATA | 1,977,174 | 除授（官职任命）数据 |
| BIOG_SOURCE_DATA | 727,472 | 资料来源 |
| KIN_DATA | 540,631 | 亲属关系 |
| BIOG_ADDR_DATA | 440,059 | 人物-地点关系（含籍贯） |
| ENTRY_DATA | 253,437 | 入仕（科举等）数据 |
| ALTNAME_DATA | 196,850 | 别名（字/号/别称） |
| ASSOC_DATA | 187,878 | 社会关系 |
| STATUS_DATA | 60,912 | 师承/身份状态 |
| TEXT_CODES | 57,387 | 著作/文本著录 |
| ADDRESSES | 51,267 | 地址实体 |
| **女性记录（BIOG_MAIN.c_female=1）** | **55,889** | 占 8.7% |
| **去重中文姓名（c_name_chn）** | **475,566** | — |

### 1.2 MQWW（mqww_2023.accdb ↔ cycle/ CSV 同数据）

| CSV 文件 | 行数 | 列数 |
|----------|------|------|
| poet.csv | 7,751 | 22 |
| poem.csv | 92,094 | 13 |
| poempagelinks.csv | 153,737 | 3 |
| workpoemlinks.csv | 91,873 | 3 |
| poempoetlinks.csv | 88,604 | 3 |
| huwenkai.csv | 4,022 | 5 |
| workpoetlinks.csv | 3,446 | 5 |
| cycle.csv | 3,277 | 6 |
| poetregionlinks.csv | 5,968 | 3 |
| subworkpoemlinks.csv | 13,024 | 3 |
| region.csv | 1,398 | 7 |
| work.csv | 431 | 36 |
| subworkpoetlinks.csv | 363 | 5 |
| subwork.csv | 244 | 4 |
| poetpagelinks.csv | 19 | 3 |

> 注：`wc -l` 计数会因字段内嵌换行而虚高（如 accdb 导出）；上表为 csv 解析器精确行数。

## 2. CBDB 核心表字段口径

### 2.1 BIOG_MAIN（人物基本信息，56 字段）

| 字段 | 类型 | 口径 |
|------|------|------|
| c_personid | INTEGER | 人物唯一 ID（主键，脚本中统一转字符串） |
| c_name / c_name_chn | CHAR | 姓名（罗马字 / 汉字） |
| c_female | BOOLEAN | 女性标记（1=女性）；用于 MQWW→CBDB 匹配（见 `matching_method.md`） |
| c_index_year / c_index_year_type_code | INT/CHAR | 索引年份及类型 |
| c_birthyear / c_deathyear | INTEGER | 生卒年（另有 c_by_nh_code/c_dy_nh_code 年号与 c_by_range/c_dy_range 范围字段） |
| c_fl_earliest_year / c_fl_latest_year | INTEGER | 生活年代最早/最晚年份（含干支年号附注字段） |
| c_surname / c_surname_chn | CHAR | 姓（拼音 / 汉字） |
| c_mingzi / c_mingzi_chn | CHAR | 名（拼音 / 汉字） |
| c_surname_proper / c_mingzi_proper / c_name_proper | CHAR | 规范字形姓/名/姓名 |
| c_surname_rm / c_mingzi_rm / c_name_rm | CHAR | 罗马字姓/名/姓名 |
| c_choronym_code | INTEGER | 郡望/籍贯代码（关联 ADDR_CODES） |
| c_ethnicity_code / c_household_status_code / c_tribe | INT/CHAR | 族属、户等、部族 |
| c_notes | CHAR | 备注 |
| c_created_by/date, c_modified_by/date | CHAR | 维护元数据 |

其余字段（生卒月日干支、c_self_bio 等）见库内 `PRAGMA table_info(BIOG_MAIN)` 全表。

### 2.2 关系/地点/文本表（关键字段）

| 表 | 关键字段 | 口径 |
|----|---------|------|
| KIN_DATA | c_personid, c_kin_id, c_kin_code | 亲属关系；c_kin_code 关联 KINSHIP_CODES |
| ASSOC_DATA | c_personid, c_assoc_id, c_assoc_code, c_kin_id, c_assoc_kin_id, c_assoc_year, c_addr_id, c_litgenre_code | 社会关系；c_assoc_code 关联 ASSOC_CODES |
| BIOG_ADDR_DATA | c_personid, c_addr_id, c_addr_type, c_sequence, c_firstyear, c_lastyear | 人物-地点关系；**c_addr_type==1 被脚本假设为籍贯**（见 r/_cbdb_read.R，需与 ADDR_CODES 核对） |
| ALTNAME_DATA | c_personid, c_alt_name, c_alt_name_chn, c_alt_name_type_code, c_sequence | 别名；c_alt_name_type_code 关联 ALTNAME_CODES（字/号等） |
| CBDB_NAME_LIST | c_personid, name, source | 姓名索引（含别名/异写，匹配用） |
| POSTING_DATA | c_personid, c_posting_id | 除授；明细见 POSTED_TO_OFFICE_DATA / POSTED_TO_ADDR_DATA |
| ENTRY_DATA | c_personid, c_entry_code, c_year, c_exam_rank, c_kin_id, c_assoc_id | 入仕 |
| TEXT_CODES | c_textid, c_title_chn, c_title, c_text_type_id, c_period, c_pub_year, c_pub_loc, c_publisher | 著作著录 |
| DYNASTIES | c_dy, c_dynasty, c_dynasty_chn, c_start, c_end | 朝代对照（起止年） |
| KIN_MOURNING / KIN_MOURNING_STEPS | — | 五服等级亲属关系（分析亲属远近） |

## 3. MQWW CSV 字段口径

### 3.1 poet.csv（22 列）— 女性诗人传记

`poetID, NameHZ, NamePY, HaoHZ, HaoPY, ZiHZ, ZiPY, OtherZiHaoHZ, OtherZiHaoPY, MaritalStatus, Notes, Sex, LifeSpan, StartYear, EndYear, EthnicGroup, MainWorks, ispoet, HuWenKai, zhuLu, xuZuoZhe, baZuoZhe`

| 字段 | 口径 |
|------|------|
| poetID | 诗人唯一 ID |
| NameHZ / NamePY | 姓名（汉字 / 拼音） |
| HaoHZ / ZiHZ / OtherZiHaoHZ（及 PY） | 号 / 字 / 其他字号 |
| MaritalStatus | 婚姻状况 |
| Sex | 性别 |
| LifeSpan / StartYear / EndYear | 生卒/活动年代 |
| MainWorks | 主要作品 |
| ispoet | 是否为诗人标记 |
| HuWenKai | 胡文楷索引关联（对应 huwenkai.csv 的 hwkID） |
| zhuLu / xuZuoZhe / baZuoZhe | 著录 / 序作者 / 跋作者 |

### 3.2 poem.csv（13 列）— 诗作

`poemID, poetassubjectID, changheshuxinpoetID, tempID, TitleHZ, TitlePY, GenreHZ, GenrePY, Form, TunePatternSubtitle, TunePatternSubtitlePY, Refs, Notes`

`poetassubjectID` = 诗题下的诗人 ID；`changheshuxinpoetID` = 唱和/书信关联诗人；`Form` = 体裁；`TunePatternSubtitle` = 词牌副题。

### 3.3 work.csv（36 列）— 文献著录（书目元数据）

`workID, AlephSysNo, Owner, OwnerCallNo, OwnerSysNo, TitleHZ, TitlePY, UniformTitle, VariantTitle, PubStatement, PubPlaceHZ, PubPlacePY, PubNameHZ, PubNamePY, DateXF, PubStartYear, PubEndYear, DateDynastyHZ, DateDynastyPY, DateEmperorHZ, DateEmperorPY, DateCycleHZ, DateCyclePY, NumberCe, NumberJuan, Description, Summary, FormattedContents, Notes, Preface, Colophon, Illustrations, InscriptionalVerse, Fanli, Refs, worktype`

关键口径：`AlephSysNo` = 图书馆系统索书号；`Owner` = 馆藏机构（如 HYC=哈佛燕京）；`DateXF` = 刊刻年份（公历）；`NumberCe`/`NumberJuan` = 册数/卷数；`FormattedContents` = 卷次内容；`worktype` = 著作类型（别集/总集等）。

### 3.4 其余表

| 文件 | 字段 |
|------|------|
| region.csv | regionID, parentRegionID, regionHZ, regionPY, VariantName, PresentdayEquivalent, PresentdayEquivalentPY（今地对照） |
| cycle.csv | cycleID, Dynasty, MinorDynasty, StemBranch, Year, YearXF（干支纪年→公历，覆盖 1368–1911） |
| huwenkai.csv | hwkID, NamePY, NameHZ, Region, Page（胡文楷《历代妇女著作考》索引） |
| 链接表 | 两列实体 ID + 行 ID（如 poempoetlinks: pmptID, poemID, poetID；workpoetlinks/subworkpoetlinks 另有 role, date） |

## 4. 口径注意事项

1. **c_addr_type==1 = 籍贯**：`r/_cbdb_read.R` 中的假设（filter c_addr_type == 1），正式使用时须与 `ADDR_CODES` 对照确认。
2. **c_female**：布尔字段，CBDB 女性标记用于匹配置信分层。
3. **ID 类型**：脚本将 c_personid / c_kin_id / c_assoc_id 统一转为字符串，避免 R 整数溢出（CBDB ID 超过 2^31 的须用字符串/64 位）。
4. **年代字段**：生卒/活动年代存在"年份+年号+范围"三套并列表述，取数时统一到公历整数。
5. **MQWW 重名**：poet.csv 有 89 组重名 NameHZ（139 条），多为泛称（無名氏 11、王氏 10、李氏 7），匹配时须按 ID 而非姓名引用。
6. **accdb ↔ CSV 一致性**：2026-08-22 比对 poet/work 各差 1 行（CSV 多 1 行），其余表完全一致；后续若更新需复比对。

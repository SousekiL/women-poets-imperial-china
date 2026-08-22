# data/ — 数据规范与安全归档说明

> 本文件说明本仓库 `data/` 目录内容、项目依赖的外部原始数据位置、版本、来源与公开发布限制。
> 审计日期：2026-08-22。所有原始资料保存在 `/Users/sousekilyu/Documents/Data/` 下，**本仓库不复制、不提交原始数据库**。

## 1. 仓库内 data/（派生研究数据）

本目录只存放**由原始数据库加工生成的派生数据**（R 工作区对象与小型 CSV），不含任何原始数据库副本：

| 文件 | 大小 | 内容 |
|------|------|------|
| `df.network.1.Rda` / `df.network.2.Rda` | 21.2 KB / 153.3 KB | 亲属/社会网络数据（R 对象） |
| `df.poet.network.1.Rda` / `df.poet.network.2.Rda` | 14.2 KB / 76.5 KB | 诗人网络数据 |
| `jinshi_results.Rda` | 294.0 KB | 进士/精英网络分析结果 |
| `poets_buff_results.Rda` | 112.0 KB | 诗人缓冲分析结果 |
| `provincial_shape.Rda` | 8.7 MB | 省级区划形状数据 |
| `.zmc_2.Rda` / `.lqz_2.Rda` | 3.1 KB / 932 B | 内部中间数据 |
| `chn.csv` / `eng.csv` / `zmc_chn.csv` | ~1 KB | 术语/对照小表 |

## 2. 外部原始数据（只读引用，位于 Data 目录）

项目研究依赖的原始数据**不在本仓库内**，路径如下（均为只读引用，禁止修改）：

| 数据 | 绝对路径 | 大小 | 版本/日期 | 说明 |
|------|---------|------|-----------|------|
| CBDB 主库 | `/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/cbdb202409.db` | 1,959,792,640 B（≈1.83 GiB） | 2024-09 版；文件 mtime 2024-11-04 | SQLite，约 80 张表，BIOG_MAIN 641,568 条传记记录 |
| CBDB 压缩副本 | 同目录 `latest.7z` | 176,488,000 B（≈168.3 MiB） | 2024-11-04 | 内含 `latest.db`，字节大小与 cbdb202409.db 完全一致（1,959,792,640 B）→ 同版本冗余副本，可校验后删除 |
| MQWW 主库 | 同目录 `mqww_2023.accdb` | 23,552,000 B（≈22.5 MiB） | MQWW 2023 版；mtime 2024-11-03 | MS Access，15 张表，与 CSV 导出同数据（poet/work 各差 1 行） |
| MQWW CSV 导出 | 同目录 `mqww_mingqing_women_writings/cycle/`（15 个 CSV，合计约 15 MB） | — | 2024 年导出 | 关系型导出：poet 7,751 行、poem 92,094 行、work 431 行等（精确行数见 `docs/data_dictionary.md`） |

### 路径迁移提示

`r/_cbdb_read.R` 中 MQWW 读取路径仍为旧路径：
```
/Users/sousekilyu/Documents/Meta Data/CBDB/mqww/cycle/*.csv   # 已失效
```
现实际路径：
```
/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/mqww_mingqing_women_writings/cycle/*.csv
```
运行旧脚本前需更新路径。

## 3. 来源与获取方式

- **CBDB（中国历代人物传记资料库）**：哈佛大学费正清中心/哈佛-燕京学社等共建。官方下载页：`https://cbdb.hsites.harvard.edu/download-cbdb-standalone-database`（注册下载，含更新订阅）。
- **MQWW（明清妇女著作）**：麦吉尔大学（McGill）与哈佛燕京合作。官网：`https://digital.library.mcgill.ca/mingqing/`（开放获取）。

## 4. 授权与公开发布限制

目录内**无任何 LICENSE/README 文件**，合规依据官方条款：

| 数据 | 官方授权 | 本地可做的事 | 公开发布限制 |
|------|---------|-------------|-------------|
| CBDB | 官方免费下载，研究用途，要求署名 | 本地分析、派生研究数据（聚合/网络指标） | 不建议公开重分发原始 `.db`；发布成果需引用 CBDB |
| MQWW | 开放获取，研究用途 | 本地分析、引用著录 | 不建议公开重分发原始 `.accdb` 或全量 CSV；图像资源受馆藏版权约束 |

- **隐私风险低**：数据均为 1912 年前已故历史人物，无在世个人数据。
- **主要风险为版权**：数据库为机构编译性成果（编辑元数据、扫描著录），受版权与使用条款约束；成果发表时须引用原始数据库。
- **仓库规则**：不提交原始 `.db`/`.accdb`/全量 CSV 进 git；如需共享派生数据，仅提交聚合结果与 ID 映射（见 `docs/matching_method.md`）。

### 引用格式建议

- CBDB: Harvard University, Academia Sinica, and Peking University. *China Biographical Database (CBDB)*. https://cbdb.hsites.harvard.edu/
- MQWW: McGill University Library. *Ming Qing Women's Writings*. https://digital.library.mcgill.ca/mingqing/

## 5. 建议的归档布局（供人工执行，尚未实施）

原始目录保持只读，建议在同级新建归档区（如 `biography_literature_CBDB_china_historical/archive/`）：

```
archive/
├── README.md          # 来源 URL、版本、下载日期、引用格式
├── LICENSE-NOTICE.md  # 两条数据库的授权与限制声明
├── cbdb202409.db      # CBDB 唯一正本（latest.7z 校验 sha256 后移除或降级为 provenance）
└── mqww/
    ├── cycle_csv/     # CSV 为正本（可移植、易被代码消费）
    └── mqww_2023.accdb # 标注为 derived 源档
```

## 6. 审计发现（2026-08-22，只读实测）

- 用户提供的 `/cbdb` 子目录**不存在**；实际为父目录下 4 项（见第 2 节）。
- 重复项 3 类：`latest.7z` 与 `.db` 同字节大小（冗余副本）；`.accdb` 与 `cycle/` CSV 同数据（两种格式）；`poet.csv` 内 89 组重名（139 条，多为 無名氏/王氏/李氏 等泛称）。
- 超大文件：仅 `cbdb202409.db`（1.8 GiB）；MQWW 全量约 15 MB。
- 垃圾文件：目录内 `.DS_Store` 2 个，归档时清理。
- 文档差异：`/Users/sousekilyu/Documents/Data/DATA_CATALOG.md` 记载 CBDB ~530,000 条，实测 BIOG_MAIN 641,568 条，**目录文档已过时**。

# python/ — 数据处理脚本

## match_mqww_cbdb.py

只读 MQWW→CBDB 姓名匹配管线（L0 泛称排除 + L1 精确匹配基线）。

- **只读**：CBDB 以 SQLite read-only URI（`file:...?mode=ro`）+ `PRAGMA query_only=ON` 打开；不写原库、不复制原始数据。
- **输出**（派生数据，仅此两项）：
  - `data/derived/person_matches_baseline.csv` — 逐诗人匹配结果（poetID、NameHZ、level A/B/C/D、候选数、女性候选数、女性标记、候选 personid 列表、reason）
  - `data/derived/match_baseline_summary.txt` — 汇总统计
- **方法**：见 `docs/matching_method.md`。

### 运行

```bash
# 仓库根目录执行（默认路径指向外部原始数据）
python3 python/match_mqww_cbdb.py

# 自定义路径
python3 python/match_mqww_cbdb.py \
  --db /path/to/cbdb202409.db \
  --mqww-poet /path/to/cycle/poet.csv \
  --out data/derived/person_matches_baseline.csv
```

### 测试

```bash
cd python && python3 -m unittest -v test_match_mqww_cbdb
```

依赖：仅 Python 3.9+ 标准库。

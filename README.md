# MQWW × CBDB 女性人物与作品关系网络

本项目以 MQWW（明清妇女著作）女性人物为主体，尝试匹配 CBDB 人物 ID，提取亲缘与社会关系，并以作品为入口探索女性人物之间的分层关系网络。

## 在线网站

GitHub Pages：<https://sousekil.github.io/women-poets-imperial-china/>

如果页面刚刚更新，GitHub Pages 可能需要几分钟完成部署。

## 当前内容

- `index.html` + `assets/`：静态网站 MVP；
- `data/derived/`：不含原始数据库的派生匹配和网络数据；
- `python/`：只读数据处理脚本和测试；
- `docs/data_dictionary.md`：数据字典；
- `docs/matching_method.md`：人名匹配方法；
- `docs/HANDOFF.md`：完整项目交接文档、验证结果和后续 TODO；
- `backup/legacy-research/`：本项目此前的论文、R 分析、旧输出和旧摘要归档。

## 本地运行

```bash
python3 python/match_mqww_cbdb.py
python3 python/match_mqww_cbdb_l2.py
python3 python/build_network_derived.py
PYTHONPATH=python python3 -m unittest discover -s python -p 'test_*.py' -v
python3 -m http.server 8877
```

然后打开 <http://127.0.0.1:8877/>。

默认脚本读取本机外部原始资料：

```text
/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/
```

原始 CBDB SQLite、MQWW Access 和全量原始 CSV 不在本仓库中，也不应上传到 public GitHub。脚本以 SQLite read-only URI 和 `PRAGMA query_only=ON` 读取 CBDB。

## 研究口径

- 姓名相同不是同一人物的充分证据；后续连接使用 `poetID` / `c_personid`；
- CBDB 亲缘/社会关系、MQWW 直接作品关系、作品—诗作—人物传递关系分层显示；
- 共同收录不等于现实社会关系；
- 网络中心度表示数据库记录中的连接结构，不直接等同于历史影响力；
- 匹配候选、来源记录、置信度和推导规则应保留，以便复核。

## 数据来源

- CBDB：<https://cbdb.hsites.harvard.edu/download-cbdb-standalone-database>
- MQWW：<https://digital.library.mcgill.ca/mingqing/>

# MQWW 网站 MVP handoff

## 已实现

- `index.html`：纯静态入口，提供人物搜索、作品选择、关系层筛选、Canvas 图谱、详情面板和来源/置信度说明。
- `assets/app.js`：仅请求派生 CSV，不访问原始数据库：
  - `data/derived/network/network_nodes.csv`
  - `data/derived/network/direct_edges.csv`
  - `data/derived/network/work_nodes.csv`
  - `data/derived/network/work_person_edges.csv`
- `assets/style.css`：响应式深色界面、图例、筛选器和详情栏。

CBDB 直接关系与 MQWW 作品/诗作关系保持独立层次和颜色；页面明确说明共同收录不等于现实关系，节点详情保留匹配等级与置信度。

## Smoke test

在仓库根目录运行：

```bash
python3 -m http.server 8877 --directory /Users/sousekilyu/Documents/Github/women-poets-imperial-china
```

随后请求入口及四份数据，全部 HTTP 200：

| 请求 | 状态 | 字节数 |
|---|---:|---:|
| `/index.html` | 200 | 1,748 |
| `/data/derived/network/network_nodes.csv` | 200 | 707,829 |
| `/data/derived/network/direct_edges.csv` | 200 | 1,208,401 |
| `/data/derived/network/work_nodes.csv` | 200 | 59,507 |
| `/data/derived/network/work_person_edges.csv` | 200 | 9,714,824 |

## 注意事项

- 当前为 MVP，Canvas 使用确定性网格坐标，尚未加入 D3 力导向布局或拖拽重排。
- 页面不会加载 CBDB/MQWW 原始数据库。
- 未提交、未推送，也未修改原始数据。

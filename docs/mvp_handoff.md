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

## 公众号叙事与截图审核

王贞仪文章建议按“搜索人物 → 人物匹配 → 关系分层 → 作品证据 → 资料边界 → 全局网络 → 方法限制”组织。截图应逐张承担一个问题：

1. 搜索“王贞仪”，展示人物入口。
2. 打开人物详情，展示 MQWW/CBDB ID、A 级匹配和置信度；图注应说明这是匹配结果，不是完整传记。
3. 分别展示亲属与社会关系层，写作时使用“24 条派生 CBDB 边（8 条亲属、16 条社会）”，不要写成 24 位人物或 24 次现实交往。
4. 选择《德风亭初集》，区分 1 条直接“主要作者”边与 371 条经作品—诗作—诗人传递边；390 是诗作关联记录，不是社会关系数。
5. 以 MQWW Notes 中的科学著作题名作为资料线索，并明确这些题名尚未全部进入当前 `work_nodes`，不能表述为图谱已逐项独立验证。
6. 清除筛选后展示整体星云，再说明共同收录不等于现实关系。

作品类型截图适合放在个案作品视图之后、整体星云之前：别集 378 部/约 3,043 人最适合承接《德风亭初集》；合刻 11 部/270 人用于说明编纂共现；总集 25 部/3,618 人用于说明汇聚规模。三组数字均应标注为当前派生数据中的作品记录与关联人物统计，不是独立作者人口、版本数或影响力排名；人物可能跨类型重复出现，数字不可直接相加。

## 注意事项

- 当前为 MVP，Canvas 使用确定性网格坐标，尚未加入 D3 力导向布局或拖拽重排。
- 页面不会加载 CBDB/MQWW 原始数据库。
- 1916 年应解释为《德风亭初集》的书目出版/著录信息，不自动等同于创作年份。
- 未提交、未推送，也未修改原始数据。

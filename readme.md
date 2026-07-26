# 站内搜索引擎：C++ / WebAssembly / GitHub Pages

这是一个站内搜索引擎项目。原始版本使用 Python 爬虫、C++ 文档解析、正排索引、倒排索引、相关性排序和 cpp-httplib HTTP 服务；新增的 WebAssembly 版本可以完全运行在浏览器中，并由 GitHub Pages 免费托管。

## 在线架构

```text
Crawler/raw.txt
      │
      ├─ scripts/raw_to_documents.py
      ▼
web/data/documents.json
      │
      ▼
JavaScript 加载公开文档
      │
      ▼
C++ SearchEngine → Emscripten → WebAssembly
      │
      ▼
浏览器本地完成倒排索引、查询和排序
```

在线版本不需要常驻服务器。GitHub Actions 在推送后自动编译 C++ 并部署 GitHub Pages。

## 核心能力

- Python 站内爬虫
- C++ HTML 预处理
- 正排索引与倒排索引
- 标题与正文加权排序
- UTF-8 中文单字和二元词项检索
- C++ 编译为 WebAssembly
- GitHub Actions 自动测试、构建和发布
- GitHub Pages 在线演示

## 本地验证 C++ 搜索核心

```bash
./scripts/test_native.sh
```

## 本地构建 WebAssembly

先安装并激活 Emscripten SDK，然后执行：

```bash
./scripts/build_wasm.sh
python3 -m http.server 8000 --directory web
```

浏览器访问 `http://localhost:8000`。不要直接双击 `web/index.html`，因为浏览器需要通过 HTTP 加载 `.wasm` 和 JSON。

## 使用爬虫产生的完整数据

原有 parser 会生成 `Crawler/raw.txt`，每行包含标题、正文和 URL。转换为网页数据：

```bash
python3 scripts/raw_to_documents.py \
  --input Crawler/raw.txt \
  --output web/data/documents.json
```

数据量较大时可以先限制文档数验证部署：

```bash
python3 scripts/raw_to_documents.py --limit 1000
```

## 开启 GitHub Pages

1. 合并新增文件到 `master`。
2. 打开仓库 `Settings → Pages`。
3. 在 `Build and deployment` 中将 `Source` 设为 `GitHub Actions`。
4. 打开 `Actions` 查看 `Build and deploy WebAssembly search demo`。
5. 部署完成后访问：`https://ahhhhwei.github.io/search-engine/`。

## 目录

```text
wasm/
├── search_engine.hpp
├── search_engine.cpp
├── bindings.cpp
└── native_smoke_test.cpp

web/
├── index.html
├── app.js
├── style.css
├── data/documents.json
└── dist/                 # Actions 构建生成

scripts/
├── build_wasm.sh
├── test_native.sh
└── raw_to_documents.py

.github/workflows/pages.yml
```

## 原生服务版本

原有 `src/http_server.cc`、`src/index.hpp` 和 `src/searcher.hpp` 仍然保留，用于展示传统后端部署方式；WebAssembly 版本是独立在线演示入口，不破坏原有实现。

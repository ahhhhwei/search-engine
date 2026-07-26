"use strict";

const RECORD_SEPARATOR = "\u001e";
const FIELD_SEPARATOR = "\u001f";

const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const searchButton = document.getElementById("search-button");
const statusElement = document.getElementById("status");
const resultsElement = document.getElementById("results");
const resultSummary = document.getElementById("result-summary");
const documentCount = document.getElementById("document-count");
const termCount = document.getElementById("term-count");
const elapsedTime = document.getElementById("elapsed-time");

let searchModule = null;

function cleanField(value) {
  return String(value ?? "").replace(/[\u001e\u001f]/g, " ");
}

function buildPayload(documents) {
  return documents
    .map((document) => [document.title, document.url, document.content]
      .map(cleanField)
      .join(FIELD_SEPARATOR))
    .join(RECORD_SEPARATOR);
}

function appendHighlightedText(parent, text, query) {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) {
    parent.textContent = text;
    return;
  }

  const lowerText = text.toLocaleLowerCase();
  const lowerQuery = normalizedQuery.toLocaleLowerCase();
  let cursor = 0;
  let position = lowerText.indexOf(lowerQuery);

  while (position !== -1) {
    parent.append(document.createTextNode(text.slice(cursor, position)));
    const mark = document.createElement("mark");
    mark.textContent = text.slice(position, position + normalizedQuery.length);
    parent.append(mark);
    cursor = position + normalizedQuery.length;
    position = lowerText.indexOf(lowerQuery, cursor);
  }
  parent.append(document.createTextNode(text.slice(cursor)));
}

function renderResults(response, query) {
  resultsElement.replaceChildren();
  elapsedTime.textContent = `${response.elapsed_ms.toFixed(3)} ms`;
  resultSummary.textContent = `命中 ${response.total} 篇文档，显示 ${response.results.length} 条`;

  if (response.results.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "没有匹配结果。可尝试缩短关键词或使用页面上方的示例查询。";
    resultsElement.append(empty);
    return;
  }

  for (const item of response.results) {
    const article = document.createElement("article");
    article.className = "result-card";

    const title = document.createElement("a");
    title.className = "result-card__title";
    title.href = item.url;
    title.target = "_blank";
    title.rel = "noopener noreferrer";
    appendHighlightedText(title, item.title, query);

    const description = document.createElement("p");
    appendHighlightedText(description, item.desc, query);

    const footer = document.createElement("div");
    footer.className = "result-card__footer";

    const url = document.createElement("span");
    url.textContent = item.url;
    const score = document.createElement("span");
    score.textContent = `相关度 ${item.score}`;
    footer.append(url, score);

    article.append(title, description, footer);
    resultsElement.append(article);
  }
}

function executeSearch(query) {
  const normalized = query.trim();
  if (!searchModule || !normalized) return;

  try {
    const response = JSON.parse(searchModule.search(normalized, 20));
    renderResults(response, normalized);
    const url = new URL(window.location.href);
    url.searchParams.set("q", normalized);
    history.replaceState(null, "", url);
  } catch (error) {
    console.error(error);
    statusElement.textContent = `搜索失败：${error.message}`;
  }
}

async function initialize() {
  try {
    if (typeof createSearchEngine !== "function") {
      throw new Error("未找到 WebAssembly 模块工厂，请确认 dist/search_engine.js 已生成");
    }

    const [module, dataResponse] = await Promise.all([
      createSearchEngine({
        locateFile: (path) => `./dist/${path}`,
      }),
      fetch("./data/documents.json", { cache: "no-cache" }),
    ]);

    if (!dataResponse.ok) {
      throw new Error(`文档数据下载失败（HTTP ${dataResponse.status}）`);
    }

    const documents = await dataResponse.json();
    if (!Array.isArray(documents) || documents.length === 0) {
      throw new Error("documents.json 中没有可检索文档");
    }

    const loaded = module.loadDocuments(buildPayload(documents));
    if (!loaded) throw new Error("C++ 搜索引擎未能建立索引");

    searchModule = module;
    documentCount.textContent = module.documentCount().toLocaleString();
    termCount.textContent = module.termCount().toLocaleString();
    statusElement.textContent = "搜索引擎已就绪；查询在当前浏览器内完成。";
    queryInput.disabled = false;
    searchButton.disabled = false;
    queryInput.focus();

    const initialQuery = new URL(window.location.href).searchParams.get("q");
    if (initialQuery) {
      queryInput.value = initialQuery;
      executeSearch(initialQuery);
    }
  } catch (error) {
    console.error(error);
    statusElement.textContent = `初始化失败：${error.message}`;
    resultSummary.textContent = "构建或部署配置需要检查";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  executeSearch(queryInput.value);
});

document.querySelectorAll("[data-query]").forEach((button) => {
  button.addEventListener("click", () => {
    queryInput.value = button.dataset.query;
    executeSearch(button.dataset.query);
  });
});

initialize();

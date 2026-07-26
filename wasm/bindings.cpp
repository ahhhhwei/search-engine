#include "search_engine.hpp"

#include <emscripten/bind.h>

#include <algorithm>
#include <cstddef>
#include <string>

namespace {
browser_search::SearchEngine g_engine;

bool LoadDocuments(const std::string& payload) {
    return g_engine.LoadDocuments(payload);
}

std::string Search(const std::string& query, int top_k) {
    const int safe_top_k = std::clamp(top_k, 1, 100);
    return g_engine.Search(query, static_cast<std::size_t>(safe_top_k));
}

int DocumentCount() {
    return static_cast<int>(g_engine.DocumentCount());
}

int TermCount() {
    return static_cast<int>(g_engine.TermCount());
}
}  // namespace

EMSCRIPTEN_BINDINGS(browser_search_module) {
    emscripten::function("loadDocuments", &LoadDocuments);
    emscripten::function("search", &Search);
    emscripten::function("documentCount", &DocumentCount);
    emscripten::function("termCount", &TermCount);
}

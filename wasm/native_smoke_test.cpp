#include "search_engine.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

int main() {
    const std::string payload =
        "倒排索引\x1fhttps://example.com/index\x1f倒排索引用于从关键词快速定位文档。"
        "\x1eWebAssembly\x1fhttps://example.com/wasm\x1fWebAssembly 让 C++ 在浏览器中运行。"
        "\x1eGitHub Pages\x1fhttps://example.com/pages\x1fGitHub Pages 可以托管静态网站。";

    browser_search::SearchEngine engine;
    if (!engine.LoadDocuments(payload)) {
        std::cerr << "failed to load documents\n";
        return EXIT_FAILURE;
    }

    const std::string result = engine.Search("倒排索引", 10);
    if (result.find("倒排索引") == std::string::npos ||
        result.find("\"total\":1") == std::string::npos) {
        std::cerr << "unexpected search result: " << result << '\n';
        return EXIT_FAILURE;
    }

    std::cout << result << '\n';
    return EXIT_SUCCESS;
}

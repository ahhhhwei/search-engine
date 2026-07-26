#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace browser_search {

class SearchEngine {
public:
    bool LoadDocuments(const std::string& payload);
    std::string Search(const std::string& query, std::size_t top_k = 10) const;

    std::size_t DocumentCount() const noexcept;
    std::size_t TermCount() const noexcept;

private:
    struct Document {
        std::string title;
        std::string url;
        std::string content;
    };

    struct Posting {
        std::uint32_t doc_id = 0;
        int weight = 0;
    };

    std::vector<Document> documents_;
    std::unordered_map<std::string, std::vector<Posting>> inverted_index_;

    static std::vector<std::string> Tokenize(const std::string& text);
    static std::string NormalizeForSubstring(const std::string& text);
    static std::string BuildSnippet(const std::string& content,
                                    const std::vector<std::string>& matched_terms);
    static std::string JsonEscape(const std::string& text);
};

}  // namespace browser_search

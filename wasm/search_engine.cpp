#include "search_engine.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <iomanip>
#include <sstream>
#include <unordered_set>
#include <utility>

namespace browser_search {
namespace {

constexpr char kRecordSeparator = '\x1e';
constexpr char kFieldSeparator = '\x1f';
constexpr int kTitleWeight = 10;
constexpr int kContentWeight = 1;
constexpr int kExactTitleBonus = 30;

bool IsUtf8Continuation(unsigned char ch) {
    return (ch & 0xC0U) == 0x80U;
}

bool IsCjk(std::uint32_t codepoint) {
    return (codepoint >= 0x3400U && codepoint <= 0x4DBFU) ||
           (codepoint >= 0x4E00U && codepoint <= 0x9FFFU) ||
           (codepoint >= 0xF900U && codepoint <= 0xFAFFU);
}

std::size_t Utf8CodepointLength(unsigned char first) {
    if ((first & 0x80U) == 0U) return 1;
    if ((first & 0xE0U) == 0xC0U) return 2;
    if ((first & 0xF0U) == 0xE0U) return 3;
    if ((first & 0xF8U) == 0xF0U) return 4;
    return 1;
}

std::uint32_t DecodeUtf8(const std::string& text, std::size_t pos, std::size_t length) {
    const auto first = static_cast<unsigned char>(text[pos]);
    if (length == 1) return first;

    std::uint32_t codepoint = first & ((1U << (7U - static_cast<unsigned int>(length))) - 1U);
    for (std::size_t i = 1; i < length && pos + i < text.size(); ++i) {
        const auto next = static_cast<unsigned char>(text[pos + i]);
        if (!IsUtf8Continuation(next)) return first;
        codepoint = (codepoint << 6U) | (next & 0x3FU);
    }
    return codepoint;
}

void AppendCjkRunTokens(const std::vector<std::string>& run,
                        std::vector<std::string>* tokens) {
    if (run.empty()) return;
    for (const auto& character : run) tokens->push_back(character);
    for (std::size_t i = 0; i + 1 < run.size(); ++i) {
        tokens->push_back(run[i] + run[i + 1]);
    }
}

std::vector<std::string> Split(const std::string& text, char separator) {
    std::vector<std::string> parts;
    std::size_t begin = 0;
    while (begin <= text.size()) {
        const std::size_t end = text.find(separator, begin);
        if (end == std::string::npos) {
            parts.push_back(text.substr(begin));
            break;
        }
        parts.push_back(text.substr(begin, end - begin));
        begin = end + 1;
    }
    return parts;
}

}  // namespace

bool SearchEngine::LoadDocuments(const std::string& payload) {
    documents_.clear();
    inverted_index_.clear();

    const auto records = Split(payload, kRecordSeparator);
    for (const auto& record : records) {
        if (record.empty()) continue;
        const auto fields = Split(record, kFieldSeparator);
        if (fields.size() != 3 || fields[0].empty()) continue;

        Document document{fields[0], fields[1], fields[2]};
        const auto doc_id = static_cast<std::uint32_t>(documents_.size());
        documents_.push_back(std::move(document));

        std::unordered_map<std::string, int> weights;
        for (const auto& token : Tokenize(documents_.back().title)) {
            weights[token] += kTitleWeight;
        }
        for (const auto& token : Tokenize(documents_.back().content)) {
            weights[token] += kContentWeight;
        }

        for (const auto& [term, weight] : weights) {
            inverted_index_[term].push_back(Posting{doc_id, weight});
        }
    }

    return !documents_.empty();
}

std::string SearchEngine::Search(const std::string& query, std::size_t top_k) const {
    const auto start_time = std::chrono::steady_clock::now();

    std::vector<std::string> query_tokens;
    std::unordered_set<std::string> seen;
    for (const auto& token : Tokenize(query)) {
        if (!token.empty() && seen.insert(token).second) query_tokens.push_back(token);
    }

    struct Candidate {
        std::uint32_t doc_id = 0;
        int score = 0;
        std::vector<std::string> matched_terms;
    };

    std::unordered_map<std::uint32_t, Candidate> candidates;
    for (const auto& term : query_tokens) {
        const auto it = inverted_index_.find(term);
        if (it == inverted_index_.end()) continue;
        for (const auto& posting : it->second) {
            auto& candidate = candidates[posting.doc_id];
            candidate.doc_id = posting.doc_id;
            candidate.score += posting.weight;
            candidate.matched_terms.push_back(term);
        }
    }

    const std::string normalized_query = NormalizeForSubstring(query);
    if (!normalized_query.empty()) {
        for (auto& [doc_id, candidate] : candidates) {
            if (NormalizeForSubstring(documents_[doc_id].title).find(normalized_query) !=
                std::string::npos) {
                candidate.score += kExactTitleBonus;
            }
        }
    }

    std::vector<Candidate> ranked;
    ranked.reserve(candidates.size());
    for (auto& [_, candidate] : candidates) ranked.push_back(std::move(candidate));
    std::sort(ranked.begin(), ranked.end(), [](const Candidate& lhs, const Candidate& rhs) {
        if (lhs.score != rhs.score) return lhs.score > rhs.score;
        return lhs.doc_id < rhs.doc_id;
    });

    if (top_k == 0) top_k = 10;
    if (ranked.size() > top_k) ranked.resize(top_k);

    const auto elapsed = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - start_time).count();

    std::ostringstream out;
    out << "{\"total\":" << candidates.size()
        << ",\"elapsed_ms\":" << std::fixed << std::setprecision(3) << elapsed
        << ",\"results\":[";

    for (std::size_t i = 0; i < ranked.size(); ++i) {
        const auto& candidate = ranked[i];
        const auto& document = documents_[candidate.doc_id];
        if (i != 0) out << ',';
        out << "{\"title\":\"" << JsonEscape(document.title)
            << "\",\"url\":\"" << JsonEscape(document.url)
            << "\",\"desc\":\"" << JsonEscape(BuildSnippet(document.content,
                                                                  candidate.matched_terms))
            << "\",\"score\":" << candidate.score << '}';
    }
    out << "]}";
    return out.str();
}

std::size_t SearchEngine::DocumentCount() const noexcept {
    return documents_.size();
}

std::size_t SearchEngine::TermCount() const noexcept {
    return inverted_index_.size();
}

std::vector<std::string> SearchEngine::Tokenize(const std::string& text) {
    std::vector<std::string> tokens;
    std::string ascii_token;
    std::vector<std::string> cjk_run;

    auto flush_ascii = [&]() {
        if (!ascii_token.empty()) {
            tokens.push_back(ascii_token);
            ascii_token.clear();
        }
    };
    auto flush_cjk = [&]() {
        AppendCjkRunTokens(cjk_run, &tokens);
        cjk_run.clear();
    };

    for (std::size_t i = 0; i < text.size();) {
        const auto first = static_cast<unsigned char>(text[i]);
        if (first < 0x80U) {
            flush_cjk();
            if (std::isalnum(first) != 0 || first == '_' || first == '+' || first == '#') {
                ascii_token.push_back(static_cast<char>(std::tolower(first)));
            } else {
                flush_ascii();
            }
            ++i;
            continue;
        }

        flush_ascii();
        std::size_t length = Utf8CodepointLength(first);
        if (i + length > text.size()) length = 1;
        const std::uint32_t codepoint = DecodeUtf8(text, i, length);
        const std::string character = text.substr(i, length);
        if (IsCjk(codepoint)) {
            cjk_run.push_back(character);
        } else {
            flush_cjk();
        }
        i += length;
    }

    flush_ascii();
    flush_cjk();
    return tokens;
}

std::string SearchEngine::NormalizeForSubstring(const std::string& text) {
    std::string normalized;
    normalized.reserve(text.size());
    for (unsigned char ch : text) {
        if (ch < 0x80U) {
            if (std::isspace(ch) == 0) normalized.push_back(static_cast<char>(std::tolower(ch)));
        } else {
            normalized.push_back(static_cast<char>(ch));
        }
    }
    return normalized;
}

std::string SearchEngine::BuildSnippet(const std::string& content,
                                       const std::vector<std::string>& matched_terms) {
    if (content.empty()) return "";

    std::size_t match_position = std::string::npos;
    std::size_t match_length = 0;
    for (const auto& term : matched_terms) {
        const std::size_t position = content.find(term);
        if (position < match_position) {
            match_position = position;
            match_length = term.size();
        }
    }
    if (match_position == std::string::npos) match_position = 0;

    std::size_t begin = match_position > 90 ? match_position - 90 : 0;
    while (begin < content.size() && IsUtf8Continuation(static_cast<unsigned char>(content[begin]))) {
        ++begin;
    }

    std::size_t end = std::min(content.size(), match_position + match_length + 180);
    while (end > begin && end < content.size() &&
           IsUtf8Continuation(static_cast<unsigned char>(content[end]))) {
        --end;
    }

    std::string snippet = content.substr(begin, end - begin);
    if (begin > 0) snippet.insert(0, "…");
    if (end < content.size()) snippet.append("…");
    return snippet;
}

std::string SearchEngine::JsonEscape(const std::string& text) {
    std::ostringstream out;
    for (unsigned char ch : text) {
        switch (ch) {
            case '\"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\b': out << "\\b"; break;
            case '\f': out << "\\f"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (ch < 0x20U) {
                    out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                        << static_cast<int>(ch) << std::dec << std::setfill(' ');
                } else {
                    out << static_cast<char>(ch);
                }
        }
    }
    return out.str();
}

}  // namespace browser_search

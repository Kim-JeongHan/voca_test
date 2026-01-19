#include "voca_test/voca_wasm.hpp"

#include "voca_test/voca_session.hpp"

#include <cstdlib>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

namespace {

char* strdup_alloc(const std::string& s)
{
    char* buf = static_cast<char*>(std::malloc(s.size() + 1));
    if (buf) {
        std::memcpy(buf, s.c_str(), s.size() + 1);
    }
    return buf;
}

std::vector<std::pair<std::string, std::string>> parseCSV(const std::string& csv_text)
{
    std::vector<std::pair<std::string, std::string>> words;
    std::istringstream stream(csv_text);
    std::string line;
    while (std::getline(stream, line)) {
        if (line.empty()) {
            continue;
        }
        std::size_t comma_pos = line.find(',');
        if (comma_pos == std::string::npos) {
            continue;
        }
        std::string word = line.substr(0, comma_pos);
        std::string meaning = line.substr(comma_pos + 1);

        // Trim whitespace
        while (!word.empty() && (word.back() == ' ' || word.back() == '\r')) {
            word.pop_back();
        }
        while (!meaning.empty() && (meaning.back() == ' ' || meaning.back() == '\r')) {
            meaning.pop_back();
        }

        if (!word.empty() && !meaning.empty()) {
            words.emplace_back(word, meaning);
        }
    }
    return words;
}

std::vector<int> parseIndices(const std::string& indices_str)
{
    std::vector<int> indices;
    std::istringstream stream(indices_str);
    std::string token;
    while (std::getline(stream, token, ',')) {
        try {
            indices.push_back(std::stoi(token));
        } catch (...) {
            // Skip invalid indices
        }
    }
    return indices;
}

} // namespace

extern "C" {

VocaSessionHandle voca_session_create()
{
    return new voca::VocaSession();
}

void voca_session_destroy(VocaSessionHandle handle)
{
    delete static_cast<voca::VocaSession*>(handle);
}

int voca_session_load_csv(VocaSessionHandle handle, const char* csv_text)
{
    if (!handle || !csv_text) {
        return 0;
    }
    auto* session = static_cast<voca::VocaSession*>(handle);
    auto words = parseCSV(csv_text);
    int count = static_cast<int>(words.size());
    session->setWords(std::move(words));
    return count;
}

void voca_session_start(VocaSessionHandle handle)
{
    if (!handle) {
        return;
    }
    static_cast<voca::VocaSession*>(handle)->start();
}

void voca_session_start_indices(VocaSessionHandle handle, const char* indices)
{
    if (!handle || !indices) {
        return;
    }
    auto* session = static_cast<voca::VocaSession*>(handle);
    session->start(parseIndices(indices));
}

char* voca_session_get_prompt(VocaSessionHandle handle)
{
    if (!handle) {
        return strdup_alloc("{}");
    }
    auto* session = static_cast<voca::VocaSession*>(handle);
    return strdup_alloc(session->getPromptJson());
}

char* voca_session_submit(VocaSessionHandle handle, const char* answer)
{
    if (!handle || !answer) {
        return strdup_alloc("{}");
    }
    auto* session = static_cast<voca::VocaSession*>(handle);
    return strdup_alloc(session->submitAnswer(answer));
}

char* voca_session_summary(VocaSessionHandle handle)
{
    if (!handle) {
        return strdup_alloc("{}");
    }
    auto* session = static_cast<voca::VocaSession*>(handle);
    return strdup_alloc(session->summaryJson());
}

char* voca_session_export_wrong(VocaSessionHandle handle)
{
    if (!handle) {
        return strdup_alloc("");
    }
    auto* session = static_cast<voca::VocaSession*>(handle);
    return strdup_alloc(session->exportWrongCSV());
}

int voca_session_is_finished(VocaSessionHandle handle)
{
    if (!handle) {
        return 1;
    }
    return static_cast<voca::VocaSession*>(handle)->isFinished() ? 1 : 0;
}

void voca_free_string(char* str)
{
    std::free(str);
}

} // extern "C"

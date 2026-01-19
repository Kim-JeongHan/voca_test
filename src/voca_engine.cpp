#include "voca_test/voca_engine.hpp"

#include <algorithm>
#include <regex>

namespace voca {

bool VocaTestEngine::isCorrect(const std::string& answer, const std::string& correct) const
{
    std::string normalized_answer = removeWhitespace_(answer);
    std::string stripped_correct = stripQuotes_(correct);
    std::string normalized_correct = removeWhitespace_(stripped_correct);

    if (containsComma_(normalized_correct)) {
        std::vector<std::string> answers = splitAndSort_(normalized_answer);
        std::vector<std::string> responses = splitAndSort_(normalized_correct);
        return answers == responses;
    }

    return normalized_answer == normalized_correct;
}

std::string VocaTestEngine::removeWhitespace_(const std::string& s) const
{
    static const std::regex pattern("\\s+");
    return std::regex_replace(s, pattern, "");
}

std::string VocaTestEngine::stripQuotes_(const std::string& s) const
{
    if (s.size() >= 2 && s.front() == '"' && s.back() == '"') {
        return s.substr(1, s.size() - 2);
    }
    if (!s.empty() && s.front() == '"') {
        return s.substr(1);
    }
    if (!s.empty() && s.back() == '"') {
        return s.substr(0, s.size() - 1);
    }
    return s;
}

bool VocaTestEngine::containsComma_(const std::string& s) const
{
    return s.find(',') != std::string::npos;
}

std::vector<std::string> VocaTestEngine::splitAndSort_(const std::string& input) const
{
    std::vector<std::string> result;
    std::regex pattern(",");
    std::sregex_token_iterator iter(input.begin(), input.end(), pattern, -1);
    std::sregex_token_iterator end;
    for (; iter != end; ++iter) {
        result.push_back(*iter);
    }
    std::sort(result.begin(), result.end());
    return result;
}

} // namespace voca

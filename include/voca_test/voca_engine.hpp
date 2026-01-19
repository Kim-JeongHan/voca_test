#pragma once

#include <string>
#include <vector>

namespace voca {

class VocaTestEngine {
public:
    bool isCorrect(const std::string& answer, const std::string& correct) const;

private:
    std::string removeWhitespace_(const std::string& s) const;
    std::string stripQuotes_(const std::string& s) const;
    bool containsComma_(const std::string& s) const;
    std::vector<std::string> splitAndSort_(const std::string& input) const;
};

} // namespace voca

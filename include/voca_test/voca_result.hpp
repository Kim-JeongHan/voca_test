#pragma once

#include <string>
#include <vector>

namespace voca {

struct WrongVoca {
    std::string word;
    std::string correct;
    int wrong_count = 0;
};

class VocaResult {
public:
    void markCorrect();
    void markWrong(const WrongVoca& w);
    void recordWrongAttempt(const WrongVoca& w);
    int wrongCount(const std::string& word, const std::string& correct) const;
    int score() const;
    int total() const;
    const std::vector<WrongVoca>& wrongList() const;
    void reset();

private:
    int correct_ = 0;
    int total_ = 0;
    std::vector<WrongVoca> wrong_;
};

} // namespace voca

#pragma once

#include <string>
#include <vector>

namespace voca {

struct WrongVoca {
    std::string word;
    std::string correct;
};

class VocaResult {
public:
    void markCorrect();
    void markWrong(const WrongVoca& w);
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

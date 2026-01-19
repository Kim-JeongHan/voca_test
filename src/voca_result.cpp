#include "voca_test/voca_result.hpp"

namespace voca {

void VocaResult::markCorrect()
{
    ++correct_;
    ++total_;
}

void VocaResult::markWrong(const WrongVoca& w)
{
    ++total_;
    recordWrongAttempt(w);
}

int VocaResult::score() const
{
    return correct_;
}

int VocaResult::total() const
{
    return total_;
}

const std::vector<WrongVoca>& VocaResult::wrongList() const
{
    return wrong_;
}

void VocaResult::recordWrongAttempt(const WrongVoca& w)
{
    for (auto& item : wrong_) {
        if (item.word == w.word && item.correct == w.correct) {
            ++item.wrong_count;
            return;
        }
    }

    WrongVoca item{w.word, w.correct, 1};
    wrong_.push_back(item);
}

int VocaResult::wrongCount(const std::string& word, const std::string& correct) const
{
    for (const auto& item : wrong_) {
        if (item.word == word && item.correct == correct) {
            return item.wrong_count;
        }
    }
    return 0;
}

void VocaResult::reset()
{
    correct_ = 0;
    total_ = 0;
    wrong_.clear();
}

} // namespace voca

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
    wrong_.push_back(w);
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

void VocaResult::reset()
{
    correct_ = 0;
    total_ = 0;
    wrong_.clear();
}

} // namespace voca

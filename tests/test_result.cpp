#include "voca_test/voca_result.hpp"

#include <cassert>
#include <iostream>

int main()
{
    voca::VocaResult result;
    result.markCorrect();
    result.markWrong({"apple", "사과"});
    result.recordWrongAttempt({"apple", "사과"});
    result.markCorrect();

    assert(result.score() == 2);
    assert(result.total() == 3);
    assert(result.wrongList().size() == 1);
    assert(result.wrongList()[0].word == "apple");
    assert(result.wrongList()[0].wrong_count == 2);

    result.reset();
    assert(result.score() == 0);
    assert(result.total() == 0);
    assert(result.wrongList().empty());

    std::cout << "test_result passed\n";
    return 0;
}

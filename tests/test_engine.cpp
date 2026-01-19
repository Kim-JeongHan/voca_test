#include "voca_test/voca_engine.hpp"

#include <cassert>
#include <iostream>

int main()
{
    voca::VocaTestEngine engine;
    assert(engine.isCorrect("apple", "apple"));
    assert(engine.isCorrect("a,b", "b,a"));
    assert(engine.isCorrect(" dog ", "\"dog\""));
    assert(!engine.isCorrect("cat", "dog"));

    std::cout << "test_engine passed\n";
    return 0;
}

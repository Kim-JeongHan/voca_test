#include "voca_test/voca_loader.hpp"

#include <cassert>
#include <iostream>
#include <utility>
#include <vector>

int main()
{
    voca::VocaLoader loader;
    std::vector<std::pair<std::string, std::string>> out;
    bool ok = loader.loadCSV("../tests/data/test_words", out);
    assert(ok);
    assert(out.size() == 3);
    assert(out[0].first == "apple");
    assert(out[0].second == "사과");

    std::cout << "test_loader passed\n";
    return 0;
}

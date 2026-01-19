#include "voca_test/voca_engine.hpp"
#include "voca_test/voca_loader.hpp"
#include "voca_test/voca_repository.hpp"
#include "voca_test/voca_result.hpp"

#include <cassert>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

int main()
{
    voca::VocaLoader loader;
    std::vector<std::pair<std::string, std::string>> data;
    bool ok = loader.loadCSV("../tests/data/test_words", data);
    assert(ok);

    voca::VocaRepository repo;
    repo.set(std::move(data));

    voca::VocaTestEngine engine;
    voca::VocaResult result;

    const auto& words = repo.data();
    for (std::size_t i = 0; i < words.size(); ++i) {
        const auto& item = words[i];
        std::string answer = (i == 1) ? "틀림" : item.second;
        if (engine.isCorrect(answer, item.second)) {
            result.markCorrect();
        } else {
            result.markWrong({item.first, item.second});
            result.recordWrongAttempt({item.first, item.second});
        }
    }

    assert(result.total() == 3);
    assert(result.score() == 2);
    assert(result.wrongList().size() == 1);
    assert(result.wrongList()[0].word == "banana");
    assert(result.wrongList()[0].wrong_count == 2);

    std::cout << "test_regression passed\n";
    return 0;
}

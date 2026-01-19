#pragma once

#include <string>
#include <vector>
#include <utility>

#include "voca_test/voca_engine.hpp"
#include "voca_test/voca_loader.hpp"
#include "voca_test/voca_repository.hpp"
#include "voca_test/voca_result.hpp"
#include "voca_test/voca_saver.hpp"

class TestVoca
{
public:
    TestVoca(const std::string& filepath, const int& number);
    TestVoca(const std::string& filepath, const std::vector<std::string>& filename);
    void runTest();

private:
    void testOnce_(const std::vector<std::pair<std::string, std::string>>& words,
                   voca::VocaResult& result);
    void printScore_(int score, int total_score);
    void printWrongVoca_(const std::vector<voca::WrongVoca>& wrong_words);
    bool mode_();
    void shuffle_(std::size_t words_size);
    std::string makeBaseName_() const;
    std::string makeHint_(const std::string& correct, int wrong_count) const;

    std::string filepath_;
    std::vector<std::string> voca_file_;
    int file_number_ = 0;
    std::vector<int> indices_;
    const int test_size_ = 100;

    voca::VocaLoader loader_;
    voca::VocaRepository repo_;
    voca::VocaTestEngine engine_;
    voca::VocaSaver saver_;
};

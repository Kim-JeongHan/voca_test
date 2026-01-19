#pragma once

#include <deque>
#include <string>
#include <vector>
#include <utility>

#include "voca_test/voca_engine.hpp"
#include "voca_test/voca_loader.hpp"
#include "voca_test/voca_repository.hpp"
#include "voca_test/voca_result.hpp"
#include "voca_test/voca_saver.hpp"

struct WrongDeckInfo {
    std::string filename;
    std::string display_name;
    std::string timestamp;
};

class TestVoca
{
public:
    TestVoca(const std::string& filepath, const int& number);
    TestVoca(const std::string& filepath, const std::vector<std::string>& filename);
    void runTest();

private:
    enum class TestResult { Completed, Interrupted, WrongDeckCleared };

    TestResult testOnce_(const std::vector<std::pair<std::string, std::string>>& words,
                         voca::VocaResult& result,
                         std::deque<int>& remaining_main,
                         std::deque<voca::WrongVoca>& remaining_retry);
    void printScore_(int score, int total_score);
    void printWrongVoca_(const std::vector<voca::WrongVoca>& wrong_words);
    int mode_();
    void shuffle_(std::size_t words_size);
    std::string makeBaseName_() const;
    std::string makeHint_(const std::string& correct, int wrong_count) const;

    std::vector<WrongDeckInfo> listWrongDecks_() const;
    void showWrongDeckMenu_();
    void runWrongDeck_(const std::string& wrong_file);
    void saveSessionState_(const std::deque<int>& main_queue,
                           const std::deque<voca::WrongVoca>& retry_queue) const;
    bool loadSessionState_(std::deque<int>& main_queue,
                           std::deque<voca::WrongVoca>& retry_queue) const;
    void clearSessionState_() const;
    std::string sessionFilePath_() const;
    bool deleteWrongDeck_(const std::string& filename);
    void updateWrongDeck_(const std::string& filename,
                          const std::vector<voca::WrongVoca>& remaining);

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

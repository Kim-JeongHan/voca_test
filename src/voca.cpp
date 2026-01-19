#include "voca_test/voca.hpp"

#include <algorithm>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <utility>
#include <vector>

TestVoca::TestVoca(const std::string& filepath, const int& number)
    : TestVoca(filepath, std::vector<std::string>{std::to_string(number)})
{
}

TestVoca::TestVoca(const std::string& filepath, const std::vector<std::string>& filename)
    : filepath_(filepath), file_number_(static_cast<int>(filename.size()))
{
    for (const auto& i : filename) {
        voca_file_.push_back(filepath_ + i);
    }

    std::vector<std::pair<std::string, std::string>> words;
    for (const auto& base : voca_file_) {
        if (!loader_.loadCSV(base, words)) {
            break;
        }
    }

    repo_.set(std::move(words));
    runTest();
}

void TestVoca::runTest()
{
    shuffle_(repo_.size());

    if (!mode_()) {
        voca::VocaResult first_pass;
        testOnce_(repo_.data(), first_pass);
        printScore_(first_pass.score(), static_cast<int>(repo_.size()));

        std::vector<std::pair<std::string, std::string>> wrong_words;
        for (const auto& w : first_pass.wrongList()) {
            wrong_words.emplace_back(w.word, w.correct);
        }

        shuffle_(wrong_words.size());
        voca::VocaResult second_pass;
        testOnce_(wrong_words, second_pass);
        printScore_(second_pass.score(), static_cast<int>(wrong_words.size()));
        printWrongVoca_(second_pass.wrongList());
        saver_.saveWrongCSV(makeBaseName_(), second_pass.wrongList(), 0);
    } else {
        indices_.resize(test_size_);
        voca::VocaResult result;
        testOnce_(repo_.data(), result);
        printScore_(result.score(), static_cast<int>(indices_.size()));
        printWrongVoca_(result.wrongList());
        saver_.saveWrongCSV(makeBaseName_(), result.wrongList(), 1);
    }
}

void TestVoca::testOnce_(const std::vector<std::pair<std::string, std::string>>& words,
                         voca::VocaResult& result)
{
    result.reset();
    for (int i : indices_) {
        std::cout << "What is the meaning of " << words[i].first << "? ";
        std::string answer;
        std::getline(std::cin, answer);

        if (!engine_.isCorrect(answer, words[i].second)) {
            result.markWrong({words[i].first, words[i].second});
            std::cout << "Incorrect. The correct answer is: " << words[i].second << "\n";
        } else {
            result.markCorrect();
        }
    }
}

void TestVoca::printScore_(int score, int total_score)
{
    std::cout << "Score: " << score << " / " << total_score << std::endl;
}

void TestVoca::printWrongVoca_(const std::vector<voca::WrongVoca>& wrong_words)
{
    std::cout << "The following words were answered incorrectly: \n";
    for (const auto& word : wrong_words) {
        std::cout << word.word << ":" << word.correct << "\n";
    }
}

bool TestVoca::mode_()
{
    std::cout << "practice mode is 0" << std::endl;
    std::cout << "test mode is 1" << std::endl;
    std::cout << "which mode do you want to choose? (0 or 1)" << std::endl;

    std::string mode;
    std::getline(std::cin, mode);
    if (mode == "0") {
        return false;
    }
    if (mode == "1") {
        return true;
    }

    std::cout << "please enter 0 or 1" << std::endl;
    return mode_();
}

void TestVoca::shuffle_(std::size_t words_size)
{
    indices_.resize(words_size);
    std::iota(indices_.begin(), indices_.end(), 0);
    std::random_device rd;
    std::default_random_engine eng(rd());
    std::shuffle(indices_.begin(), indices_.end(), eng);
}

std::string TestVoca::makeBaseName_() const
{
    if (voca_file_.empty()) {
        return "";
    }

    if (voca_file_.size() > 1) {
        return voca_file_.front() + "~" + voca_file_.back().back();
    }

    return voca_file_.front();
}

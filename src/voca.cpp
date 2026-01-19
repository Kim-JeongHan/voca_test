#include "voca_test/voca.hpp"

#include <algorithm>
#include <deque>
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

        printWrongVoca_(first_pass.wrongList());
        saver_.saveWrongCSV(makeBaseName_(), first_pass.wrongList(), 0);
    } else {
        if (indices_.size() > static_cast<std::size_t>(test_size_)) {
            indices_.resize(test_size_);
        }
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
    std::deque<int> main_queue(indices_.begin(), indices_.end());
    std::deque<voca::WrongVoca> retry_queue;

    while (!main_queue.empty() || !retry_queue.empty()) {
        bool from_retry = !retry_queue.empty();
        std::string word;
        std::string correct;

        if (from_retry) {
            const auto current = retry_queue.front();
            retry_queue.pop_front();
            word = current.word;
            correct = current.correct;
        } else {
            int idx = main_queue.front();
            main_queue.pop_front();
            word = words[idx].first;
            correct = words[idx].second;
        }

        int wrong_count = result.wrongCount(word, correct);
        int hint_shown = 0;

        while (true) {
            std::cout << "What is the meaning of " << word << "? ";
            std::string answer;
            std::getline(std::cin, answer);

            if (answer == "hint" || answer == "h") {
                ++hint_shown;
                int hint_level = std::min(wrong_count + hint_shown, 4);
                std::cout << makeHint_(correct, hint_level) << "\n";
                continue;
            }

            if (engine_.isCorrect(answer, correct)) {
                if (!from_retry) {
                    result.markCorrect();
                }
                break;
            }

            if (from_retry) {
                result.recordWrongAttempt({word, correct});
            } else {
                result.markWrong({word, correct});
            }

            int next_count = result.wrongCount(word, correct);
            if (next_count >= 4) {
                std::cout << "Incorrect. The correct answer is: "
                          << engine_.stripQuotes(correct) << " (type it again)\n";
            } else {
                std::cout << "Incorrect. (type 'hint' for a hint)\n";
            }

            retry_queue.push_front({word, correct});
            break;
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

std::string TestVoca::makeHint_(const std::string& correct, int wrong_count) const
{
    std::string hint = correct;
    if (hint.size() >= 2 && hint.front() == '"' && hint.back() == '"') {
        hint = hint.substr(1, hint.size() - 2);
    } else if (!hint.empty() && hint.front() == '"') {
        hint = hint.substr(1);
    } else if (!hint.empty() && hint.back() == '"') {
        hint = hint.substr(0, hint.size() - 1);
    }

    std::string compact;
    compact.reserve(hint.size());
    for (char ch : hint) {
        if (ch == ',' || ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r') {
            continue;
        }
        compact.push_back(ch);
    }

    auto splitUtf8 = [](const std::string& s) {
        std::vector<std::string> units;
        for (std::size_t i = 0; i < s.size();) {
            unsigned char c = static_cast<unsigned char>(s[i]);
            std::size_t len = 1;
            if ((c & 0x80) == 0x00) {
                len = 1;
            } else if ((c & 0xE0) == 0xC0) {
                len = 2;
            } else if ((c & 0xF0) == 0xE0) {
                len = 3;
            } else if ((c & 0xF8) == 0xF0) {
                len = 4;
            }

            if (i + len > s.size()) {
                len = 1;
            }
            units.emplace_back(s.substr(i, len));
            i += len;
        }
        return units;
    };

    const auto units = splitUtf8(compact);
    std::size_t len = units.size();
    if (len == 0) {
        return "Hint: (no letters)";
    }

    if (wrong_count == 1) {
        return "Hint: " + std::string(len, '_') + " (" + std::to_string(len) + " 글자)";
    }

    if (wrong_count == 2) {
        return "Hint: " + units[0] + std::string(len - 1, '_');
    }

    if (wrong_count == 3) {
        std::size_t reveal = std::min<std::size_t>(2, len > 0 ? len - 1 : 0);
        std::string prefix;
        for (std::size_t i = 0; i < reveal; ++i) {
            prefix += units[i];
        }
        return "Hint: " + prefix + std::string(len - reveal, '_');
    }

    return "Hint: " + hint + " (type it again)";
}

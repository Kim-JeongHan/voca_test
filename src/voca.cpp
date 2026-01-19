#include "voca_test/voca.hpp"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace fs = std::filesystem;

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

    int selected_mode = mode_();

    if (selected_mode == 0) {
        std::deque<int> remaining_main;
        std::deque<voca::WrongVoca> remaining_retry;

        if (loadSessionState_(remaining_main, remaining_retry)) {
            std::cout << "Resume previous session? (y/n): ";
            std::string choice;
            std::getline(std::cin, choice);
            if (choice == "y" || choice == "Y") {
                voca::VocaResult result;
                auto test_result = testOnce_(repo_.data(), result, remaining_main, remaining_retry);
                if (test_result == TestResult::Completed) {
                    clearSessionState_();
                    printScore_(result.score(), static_cast<int>(repo_.size()));
                    printWrongVoca_(result.wrongList());
                    saver_.saveWrongCSV(makeBaseName_(), result.wrongList(), 0);
                }
                return;
            }
            clearSessionState_();
        }

        std::deque<int> main_queue(indices_.begin(), indices_.end());
        std::deque<voca::WrongVoca> retry_queue;
        voca::VocaResult first_pass;
        auto test_result = testOnce_(repo_.data(), first_pass, main_queue, retry_queue);

        if (test_result == TestResult::Completed) {
            clearSessionState_();
            printScore_(first_pass.score(), static_cast<int>(repo_.size()));
            printWrongVoca_(first_pass.wrongList());
            saver_.saveWrongCSV(makeBaseName_(), first_pass.wrongList(), 0);
        }
    } else if (selected_mode == 1) {
        if (indices_.size() > static_cast<std::size_t>(test_size_)) {
            indices_.resize(test_size_);
        }
        std::deque<int> main_queue(indices_.begin(), indices_.end());
        std::deque<voca::WrongVoca> retry_queue;
        voca::VocaResult result;
        auto test_result = testOnce_(repo_.data(), result, main_queue, retry_queue);
        if (test_result == TestResult::Completed) {
            printScore_(result.score(), static_cast<int>(indices_.size()));
            printWrongVoca_(result.wrongList());
            saver_.saveWrongCSV(makeBaseName_(), result.wrongList(), 1);
        }
    } else if (selected_mode == 2) {
        showWrongDeckMenu_();
    }
}

TestVoca::TestResult TestVoca::testOnce_(
    const std::vector<std::pair<std::string, std::string>>& words,
    voca::VocaResult& result,
    std::deque<int>& main_queue,
    std::deque<voca::WrongVoca>& retry_queue)
{
    result.reset();

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
        int hint_used = 0;
        bool marked_wrong_by_hint = false;

        while (true) {
            std::cout << "What is the meaning of " << word << "? ";
            std::string answer;
            std::getline(std::cin, answer);

            if (answer == "quit" || answer == "q") {
                if (!from_retry) {
                    main_queue.push_front(
                        static_cast<int>(std::find_if(words.begin(), words.end(),
                            [&word](const auto& p) { return p.first == word; }) - words.begin()));
                } else {
                    retry_queue.push_front({word, correct});
                }
                saveSessionState_(main_queue, retry_queue);
                std::cout << "Session saved. You can resume later.\n";
                return TestResult::Interrupted;
            }

            if (answer == "hint" || answer == "h") {
                ++hint_used;
                int hint_level = std::min(wrong_count + hint_used, 4);
                std::cout << makeHint_(correct, hint_level) << "\n";

                if (hint_used >= 2 && !marked_wrong_by_hint) {
                    marked_wrong_by_hint = true;
                    if (from_retry) {
                        result.recordWrongAttempt({word, correct});
                    } else {
                        result.markWrong({word, correct});
                    }
                    std::cout << "(Hint used twice - marked as incorrect)\n";
                }
                continue;
            }

            if (engine_.isCorrect(answer, correct)) {
                if (!from_retry && !marked_wrong_by_hint) {
                    result.markCorrect();
                }
                break;
            }

            if (!marked_wrong_by_hint) {
                if (from_retry) {
                    result.recordWrongAttempt({word, correct});
                } else {
                    result.markWrong({word, correct});
                }
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

    return TestResult::Completed;
}

void TestVoca::printScore_(int score, int total_score)
{
    std::cout << "Score: " << score << " / " << total_score << std::endl;
}

void TestVoca::printWrongVoca_(const std::vector<voca::WrongVoca>& wrong_words)
{
    if (wrong_words.empty()) {
        std::cout << "Perfect! No wrong answers.\n";
        return;
    }
    std::cout << "The following words were answered incorrectly: \n";
    for (const auto& word : wrong_words) {
        std::cout << word.word << ":" << word.correct << "\n";
    }
}

int TestVoca::mode_()
{
    std::cout << "=== Mode Selection ===" << std::endl;
    std::cout << "0: Practice mode" << std::endl;
    std::cout << "1: Test mode" << std::endl;
    std::cout << "2: Wrong deck review" << std::endl;
    std::cout << "Select mode (0/1/2): ";

    std::string mode;
    std::getline(std::cin, mode);
    if (mode == "0") {
        return 0;
    }
    if (mode == "1") {
        return 1;
    }
    if (mode == "2") {
        return 2;
    }

    std::cout << "Please enter 0, 1, or 2" << std::endl;
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

std::vector<WrongDeckInfo> TestVoca::listWrongDecks_() const
{
    std::vector<WrongDeckInfo> decks;

    try {
        for (const auto& entry : fs::directory_iterator(filepath_)) {
            if (!entry.is_regular_file()) {
                continue;
            }
            std::string filename = entry.path().filename().string();
            if (filename.find("_wrong") == std::string::npos) {
                continue;
            }
            if (filename.size() < 4 || filename.substr(filename.size() - 4) != ".csv") {
                continue;
            }

            auto ftime = fs::last_write_time(entry.path());
            auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                ftime - fs::file_time_type::clock::now() + std::chrono::system_clock::now());
            std::time_t cftime = std::chrono::system_clock::to_time_t(sctp);

            std::ostringstream ts;
            ts << std::put_time(std::localtime(&cftime), "%Y-%m-%d %H:%M");

            std::string display = filename.substr(0, filename.size() - 4);
            decks.push_back({filename, display, ts.str()});
        }
    } catch (const fs::filesystem_error&) {
    }

    std::sort(decks.begin(), decks.end(),
              [](const WrongDeckInfo& a, const WrongDeckInfo& b) {
                  return a.timestamp > b.timestamp;
              });

    return decks;
}

void TestVoca::showWrongDeckMenu_()
{
    auto decks = listWrongDecks_();

    if (decks.empty()) {
        std::cout << "No wrong decks available.\n";
        return;
    }

    std::cout << "\n=== Wrong Deck List ===\n";
    for (std::size_t i = 0; i < decks.size(); ++i) {
        std::cout << i + 1 << ". " << decks[i].display_name
                  << " [" << decks[i].timestamp << "]\n";
    }
    std::cout << "d<number>: Delete deck (e.g., d1)\n";
    std::cout << "0: Back to main menu\n";
    std::cout << "Select: ";

    std::string input;
    std::getline(std::cin, input);

    if (input == "0" || input.empty()) {
        return;
    }

    if (!input.empty() && input[0] == 'd') {
        try {
            int idx = std::stoi(input.substr(1)) - 1;
            if (idx >= 0 && static_cast<std::size_t>(idx) < decks.size()) {
                std::cout << "Delete " << decks[idx].display_name << "? (y/n): ";
                std::string confirm;
                std::getline(std::cin, confirm);
                if (confirm == "y" || confirm == "Y") {
                    if (deleteWrongDeck_(decks[idx].filename)) {
                        std::cout << "Deleted.\n";
                    } else {
                        std::cout << "Failed to delete.\n";
                    }
                }
            }
        } catch (...) {
        }
        showWrongDeckMenu_();
        return;
    }

    try {
        int idx = std::stoi(input) - 1;
        if (idx >= 0 && static_cast<std::size_t>(idx) < decks.size()) {
            runWrongDeck_(decks[idx].filename);
        } else {
            std::cout << "Invalid selection.\n";
            showWrongDeckMenu_();
        }
    } catch (...) {
        std::cout << "Invalid input.\n";
        showWrongDeckMenu_();
    }
}

void TestVoca::runWrongDeck_(const std::string& wrong_file)
{
    std::string full_path = filepath_ + wrong_file.substr(0, wrong_file.size() - 4);
    std::vector<std::pair<std::string, std::string>> words;
    if (!loader_.loadCSV(full_path, words) || words.empty()) {
        std::cout << "Failed to load wrong deck or deck is empty.\n";
        return;
    }

    std::cout << "\nStarting wrong deck review: " << wrong_file << "\n";
    std::cout << "Words in deck: " << words.size() << "\n";
    std::cout << "(Type 'quit' to save and exit, correct answers are removed from deck)\n\n";

    std::vector<int> indices(words.size());
    std::iota(indices.begin(), indices.end(), 0);
    std::random_device rd;
    std::default_random_engine eng(rd());
    std::shuffle(indices.begin(), indices.end(), eng);

    std::deque<int> main_queue(indices.begin(), indices.end());
    std::deque<voca::WrongVoca> retry_queue;
    voca::VocaResult result;

    std::vector<voca::WrongVoca> remaining_wrong;

    while (!main_queue.empty() || !retry_queue.empty()) {
        bool from_retry = !retry_queue.empty();
        std::string word;
        std::string correct;
        int word_idx = -1;

        if (from_retry) {
            const auto current = retry_queue.front();
            retry_queue.pop_front();
            word = current.word;
            correct = current.correct;
        } else {
            word_idx = main_queue.front();
            main_queue.pop_front();
            word = words[word_idx].first;
            correct = words[word_idx].second;
        }

        int wrong_count = result.wrongCount(word, correct);
        int hint_used = 0;
        bool marked_wrong_by_hint = false;
        bool answered_correctly = false;

        while (true) {
            std::cout << "What is the meaning of " << word << "? ";
            std::string answer;
            std::getline(std::cin, answer);

            if (answer == "quit" || answer == "q") {
                remaining_wrong.push_back({word, correct});
                for (const auto& idx : main_queue) {
                    remaining_wrong.push_back({words[idx].first, words[idx].second});
                }
                for (const auto& w : retry_queue) {
                    remaining_wrong.push_back(w);
                }
                updateWrongDeck_(wrong_file, remaining_wrong);
                std::cout << "Saved remaining " << remaining_wrong.size() << " words.\n";
                return;
            }

            if (answer == "hint" || answer == "h") {
                ++hint_used;
                int hint_level = std::min(wrong_count + hint_used, 4);
                std::cout << makeHint_(correct, hint_level) << "\n";

                if (hint_used >= 2 && !marked_wrong_by_hint) {
                    marked_wrong_by_hint = true;
                    result.markWrong({word, correct});
                    std::cout << "(Hint used twice - marked as incorrect)\n";
                }
                continue;
            }

            if (engine_.isCorrect(answer, correct)) {
                answered_correctly = true;
                if (!marked_wrong_by_hint) {
                    std::cout << "Correct! (removed from wrong deck)\n";
                } else {
                    std::cout << "Correct! (but keeping in wrong deck due to hint usage)\n";
                    remaining_wrong.push_back({word, correct});
                }
                break;
            }

            if (!marked_wrong_by_hint) {
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

    if (remaining_wrong.empty()) {
        if (deleteWrongDeck_(wrong_file)) {
            std::cout << "\nPerfect! Wrong deck cleared and deleted!\n";
        }
    } else {
        updateWrongDeck_(wrong_file, remaining_wrong);
        std::cout << "\nRemaining words in wrong deck: " << remaining_wrong.size() << "\n";
    }
}

void TestVoca::saveSessionState_(const std::deque<int>& main_queue,
                                  const std::deque<voca::WrongVoca>& retry_queue) const
{
    std::ofstream file(sessionFilePath_());
    if (!file.is_open()) {
        return;
    }

    file << "MAIN\n";
    for (int idx : main_queue) {
        file << idx << "\n";
    }
    file << "RETRY\n";
    for (const auto& w : retry_queue) {
        file << w.word << "," << w.correct << "\n";
    }
}

bool TestVoca::loadSessionState_(std::deque<int>& main_queue,
                                  std::deque<voca::WrongVoca>& retry_queue) const
{
    std::ifstream file(sessionFilePath_());
    if (!file.is_open()) {
        return false;
    }

    main_queue.clear();
    retry_queue.clear();

    std::string line;
    bool reading_main = false;
    bool reading_retry = false;

    while (std::getline(file, line)) {
        if (line == "MAIN") {
            reading_main = true;
            reading_retry = false;
            continue;
        }
        if (line == "RETRY") {
            reading_main = false;
            reading_retry = true;
            continue;
        }

        if (reading_main) {
            try {
                main_queue.push_back(std::stoi(line));
            } catch (...) {
            }
        } else if (reading_retry) {
            auto pos = line.find(',');
            if (pos != std::string::npos) {
                retry_queue.push_back({line.substr(0, pos), line.substr(pos + 1)});
            }
        }
    }

    return !main_queue.empty() || !retry_queue.empty();
}

void TestVoca::clearSessionState_() const
{
    std::remove(sessionFilePath_().c_str());
}

std::string TestVoca::sessionFilePath_() const
{
    return filepath_ + ".session";
}

bool TestVoca::deleteWrongDeck_(const std::string& filename)
{
    try {
        return fs::remove(filepath_ + filename);
    } catch (...) {
        return false;
    }
}

void TestVoca::updateWrongDeck_(const std::string& filename,
                                 const std::vector<voca::WrongVoca>& remaining)
{
    std::string full_path = filepath_ + filename;

    if (remaining.empty()) {
        deleteWrongDeck_(filename);
        return;
    }

    std::ofstream file(full_path, std::ios::trunc);
    if (!file.is_open()) {
        return;
    }

    for (const auto& w : remaining) {
        file << w.word << "," << w.correct << "\n";
    }
}

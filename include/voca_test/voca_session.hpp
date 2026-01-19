#pragma once

#include <deque>
#include <string>
#include <utility>
#include <vector>

#include "voca_test/voca_engine.hpp"
#include "voca_test/voca_result.hpp"

namespace voca {

class VocaSession {
public:
    void setWords(std::vector<std::pair<std::string, std::string>> words);
    void start();
    void start(const std::vector<int>& indices);

    std::string getPromptJson();
    std::string submitAnswer(const std::string& answer);
    std::string summaryJson() const;
    std::string exportWrongCSV() const;
    bool isFinished() const;

private:
    struct CurrentQuestion {
        std::string word;
        std::string correct;
        std::string question_id;
        bool from_retry = false;
    };

    bool ensureCurrent_();
    std::string makeHint_(const std::string& correct, int wrong_count) const;
    static std::string escapeJson_(const std::string& s);

    std::vector<std::pair<std::string, std::string>> words_;
    std::deque<int> main_queue_;
    std::deque<WrongVoca> retry_queue_;
    VocaResult result_;
    VocaTestEngine engine_;
    int total_ = 0;
    bool has_current_ = false;
    CurrentQuestion current_{};
};

} // namespace voca

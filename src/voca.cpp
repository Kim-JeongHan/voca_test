#include "voca_test/voca.hpp"

#include <iostream>
#include <string>
#include <vector>

TestVoca::TestVoca(const std::string& filepath, const int &number)
: TestVoca(filepath, std::vector<std::string>{std::to_string(number)})
{
}

TestVoca::TestVoca(const std::string& filepath, const std::vector<std::string> &filename)
: filepath_(filepath), file_number_(filename.size())
{
    for (auto & i : filename) {
        voca_file_.push_back(filepath_ + i);
    }
    ReadFile_();
    runTest();
}


void TestVoca::runTest()
{
    shuffle_(words_meanings_.size());
    std::vector<std::pair<std::string, std::string>> wrong_words, final_wrong_words;
    if(!mode_())
    {
        Test_(words_meanings_, wrong_words);
        printScore_(words_meanings_.size());
        shuffle_(wrong_words.size());
        Test_(wrong_words, final_wrong_words);
        printScore_(wrong_words.size());
        printWrongVoca_(final_wrong_words);
        save_(final_wrong_words, false);
    }
    else
    {
        if(words_meanings_.size() > test_size_)
        {
            words_meanings_.resize(test_size_);
        }
        Test_(words_meanings_, wrong_words);
        printScore_(words_meanings_.size());
        printWrongVoca_(wrong_words);
        save_(wrong_words, true);
    }

}

void TestVoca::Test_(std::vector<std::pair<std::string, std::string>> & words_meanings,
            std::vector<std::pair<std::string, std::string>> & wrong_words)
{
    score_ = 0;
    for (int i : indices_) {
        std::cout << "What is the meaning of " << words_meanings[i].first << "? ";
        std::string answer;
        std::getline(std::cin, answer);
        // remove all whitespaces
        answer = std::regex_replace(answer, pattern_, "");

        // remove leading and trailing whitespaces
        if (words_meanings[i].second.front() == '\"') {
            words_meanings[i].second.erase(words_meanings[i].second.begin());
        }
        // remove leading and trailing whitespaces
        if (words_meanings[i].second.back() == '\"') {
            words_meanings[i].second.pop_back();
        }
        std::string second_result = std::regex_replace(words_meanings[i].second, pattern_, "");

        if (ContainsComma_(second_result)) {
            std::vector<std::string> answers;
            std::vector<std::string> responses;
            answers = SplitAndSort_(answer);
            responses = SplitAndSort_(second_result);

            if (!AreVectorsEqual_(answers, responses)) {
                wrong_words.push_back(words_meanings[i]);
                std::cout << "Incorrect. The correct answer is: " << words_meanings[i].second << "\n";
                // rewrite_wrong_words_(wrong_words.back());
            }

            else {
                score_++;
            }
        }
        else {
            if (answer != second_result) {
                wrong_words.push_back(words_meanings[i]);
                std::cout << "Incorrect. The correct answer is: " << words_meanings[i].second << "\n";
                // rewrite_wrong_words_(wrong_words.back());
            }
            else {
                score_++;
            }
        }

    }
}

void TestVoca::printScore_(const long int total_score)
{
    std::cout << "Score: " << score_ << " / " << total_score << std::endl;
}

void TestVoca::printWrongVoca_(std::vector<std::pair<std::string, std::string>> & wrong_words)
{
    std::cout << "The following words were answered incorrectly: \n";
    for (const auto& word : wrong_words) {
        std::cout << word.first << ":" << word.second << "\n";
    }
}



void TestVoca::save_(const std::vector<std::pair<std::string, std::string>> &  words,
                    const bool & save_next_file)
{
    
    if(voca_file_.size() > 1)
    {
        voca_file_.front() = voca_file_.front() + "~" + voca_file_.back().back(); 
    }
    if(save_next_file)
    {
        std::ofstream output_file(voca_file_[0] + "_test.csv", std::ios_base::app); 
        for (int i = 0; i < words.size(); ++i) {
            output_file << words[i].first << "," << words[i].second << std::endl;
        }
        output_file.close();
    }
    else
    {
        std::ofstream output_file(voca_file_[0] + "_wrong.csv", std::ios_base::app);
        for (int i = 0; i < words.size(); ++i) {
            output_file << words[i].first << "," << words[i].second << std::endl;
        }
        output_file.close();
    }
}

bool TestVoca::mode_()
{
    std::cout << "practice mode is 0" << std::endl;
    std::cout << "test mode is 1" << std::endl;
    std::cout << "which mode do you want to choose? (0 or 1)" << std::endl;

    std::string mode;
    std::getline(std::cin, mode);
    if(mode == "0")
    {
        return false;
    }
    else if(mode == "1")
    {
        return true;
    }
    else
    {
        std::cout << "please enter 0 or 1" << std::endl;
        mode_();

    }
    return false;
}


void TestVoca::ReadFile_()
{
    for(auto & i : voca_file_)
    {
        std::ifstream file(i+ ".csv");
        if (!file.is_open()) {
            std::cout << i + " not found.\n";
            return;
        }
        std::string line;
        while (std::getline(file, line)) {
            size_t pos = line.find(",");
            if (pos != std::string::npos) {
                words_meanings_.emplace_back(line.substr(0, pos), line.substr(pos + 1));
            }
        }

        file.close();
    }
}

void TestVoca::shuffle_(const long int words_size)
{
    indices_.resize(words_size);
    std::iota(indices_.begin(), indices_.end(), 0);
    std::random_device rd;
    std::default_random_engine eng(rd());
    std::shuffle(indices_.begin(), indices_.end(), eng);
}

bool TestVoca::ContainsComma_(const std::string& str) {
    std::regex pattern(",");
    return std::regex_search(str, pattern);
}

std::vector<std::string> TestVoca::SplitAndSort_(const std::string& input) {
    std::vector<std::string> result;
    std::regex pattern(",");
    std::sregex_token_iterator iter(input.begin(), input.end(), pattern, -1);
    std::sregex_token_iterator end;
    for (; iter != end; ++iter) {
        std::string token = *iter;
        result.push_back(token);
    }
    std::sort(result.begin(), result.end());
    return result;
}

bool TestVoca::AreVectorsEqual_(
    const std::vector<std::string>& vec1,
    const std::vector<std::string>& vec2)
{
    if (vec1.size() != vec2.size()) {
        return false;
    }
    for (std::size_t i = 0; i < vec1.size(); ++i) {
        if (vec1[i] != vec2[i]) {
            return false;
        }
    }
    return true;
}

void TestVoca::rewrite_wrong_words_(std::pair<std::string, std::string> & wrong_words)
{
    std::cout << "---Rewrite the wrong words---" << std::endl;
    std::string answer;
    std::getline(std::cin, answer);
    std::string result = wrong_words.first + " " + wrong_words.second;
    ContainsComma_(answer);
    ContainsComma_(result);
    if (answer != result)
        rewrite_wrong_words_(wrong_words);
}


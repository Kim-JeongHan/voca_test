#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <random>
#include <algorithm>
#include <numeric>
#include <utility>
#include <regex>
bool containsComma(const std::string& str) {
    std::regex pattern(",");
    return std::regex_search(str, pattern);
}
std::vector<std::string> splitAndSort(const std::string& input) {
    std::vector<std::string> result;
    std::regex pattern(",");
    std::sregex_token_iterator iter(input.begin(), input.end(), pattern, -1);
    std::sregex_token_iterator end;
    for (; iter != end; ++iter) {
        std::string token = *iter;
 //       token.erase(std::remove_if(token.begin(), token.end(), ::isspace), token.end());
        result.push_back(token);
    }
    std::sort(result.begin(), result.end());
    return result;
}
bool areVectorsEqual(const std::vector<std::string>& vec1, const std::vector<std::string>& vec2) {
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
int main()
{
    std::ifstream file("C:/Users/kimjh/OneDrive - 한양대학교/토플/2.csv");
    if (!file.is_open()) {
        std::cout << "File not found.\n";
        return 1;
    }
    std::vector<std::pair<std::string, std::string>> words_meanings;
    std::string line;
    std::regex pattern("\\s+");
    while (std::getline(file, line)) {
        size_t pos = line.find(",");
        if (pos != std::string::npos) {
            words_meanings.emplace_back(line.substr(0, pos), line.substr(pos + 1));
        }
    }
    file.close();
    std::vector<int> indices(words_meanings.size());
    std::iota(indices.begin(), indices.end(), 0);
    std::random_device rd;
    std::default_random_engine eng(rd());
    std::shuffle(indices.begin(), indices.end(), eng);
    std::shuffle(indices.begin(), indices.end(), eng);
    std::vector<std::string> wrong_words;
    int score = 0;
    for (int i : indices) {
        std::cout << "What is the meaning of " << words_meanings[i].first << "? ";
        std::string answer;
        std::getline(std::cin, answer);
        if (words_meanings[i].second.front() == '\"') {
            words_meanings[i].second.erase(words_meanings[i].second.begin());
        }
        if (words_meanings[i].second.back() == '\"') {
            words_meanings[i].second.pop_back();
        }
        answer = std::regex_replace(answer, pattern, "");
        std::string second_result = std::regex_replace(words_meanings[i].second, pattern, "");
        if (containsComma(second_result)) {
            std::vector<std::string> answers;
            std::vector<std::string> responses;
            answers = splitAndSort(answer);
            responses = splitAndSort(second_result);
            if (!areVectorsEqual(answers, responses)) {
                wrong_words.push_back(words_meanings[i].first);
                std::cout << "Incorrect. The correct answer is: " << words_meanings[i].second << "\n";
            }
            else {
                score++;
            }
        }
        else {
            if (answer != second_result) {
                wrong_words.push_back(words_meanings[i].first);
                std::cout << "Incorrect. The correct answer is: " << words_meanings[i].second << "\n";
            }
            else {
                score++;
            }
        }
    }
    std::cout << "Score: " << score << " / " << words_meanings.size() << std::endl;
    indices.clear();
    indices.resize(wrong_words.size());
    std::iota(indices.begin(), indices.end(), 0);
    std::shuffle(indices.begin(), indices.end(), eng);
    std::vector<std::string> final_wrong_words;
    for (int i : indices) {
        std::string word = wrong_words[i];
        auto found = std::find_if(words_meanings.begin(), words_meanings.end(), [&word](const auto& wm) {
            return wm.first == word;
            });
        std::cout << "What is the meaning of " << found->first << "? ";
        std::string answer;
        std::getline(std::cin, answer);
        if (found->second.front() == '"') {
            found->second.erase(found->second.begin());
        }
        if (found->second.back() == '"') {
            found->second.pop_back();
        }
        answer = std::regex_replace(answer, pattern, "");
        std::string second_result = std::regex_replace(found->second, pattern, "");
        if (containsComma(second_result)) {
            std::vector<std::string> answers;
            std::vector<std::string> responses;
            answers = splitAndSort(answer);
            responses = splitAndSort(second_result);
            if (!areVectorsEqual(answers, responses)) {
                final_wrong_words.push_back(found->first);
                std::cout << "Incorrect. The correct answer is: " << found->second << "\n";
            }
        }
        else {
            if (answer != second_result) {
                final_wrong_words.push_back(found->first);
                std::cout << "Incorrect. The correct answer is: " << found->second << "\n";
            }
        }
    }
    std::cout << "Final score: " << score << " / " << words_meanings.size() << std::endl;
    std::cout << "The following words were answered incorrectly: \n";
    for (const auto& word : final_wrong_words) {
        std::cout << word << "\n";
    }
    std::ofstream output_file("C:/Users/kimjh/OneDrive - 한양대학교/토플/2_wrong.csv");
    for (const auto& wrong_word : final_wrong_words) {
        auto found = std::find_if(words_meanings.begin(), words_meanings.end(), [&wrong_word](const auto& wm) {
            return wm.first == wrong_word;
            });
        output_file << wrong_word << ", " << found->second << std::endl;
    }
    output_file.close();
    return 0;
}
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <random>
#include <algorithm>
#include <numeric>
#include <utility>
#include <regex>

class TestVoca
{
public:
    TestVoca(const std::string& filepath, const int &number);
    void runTest();
    void Test(std::vector<std::pair<std::string, std::string>> & words_meanings,
              std::vector<std::pair<std::string, std::string>> & wrong_words);
    void printScore(const long int total_score);
    void printWrongVoca(std::vector<std::pair<std::string, std::string>> & wrong_words);

private:
    std::string filepath_,filename_;
    int file_number_;
    std::vector<std::pair<std::string, std::string>> words_meanings_;
    std::vector<int> indices_;
    int score_ = 0;

    std::regex pattern_{ "\\s+" };
    void ReadFile_();
    void shuffle_(const long int words_size);
    void save_(const std::vector<std::pair<std::string, std::string>> &  words);

    void save_(const std::vector<std::pair<std::string, std::string>> &  words,
               const bool & save_next_file);
    bool ContainsComma_(const std::string& str);
    std::vector<std::string> SplitAndSort_(const std::string& input);
    bool AreVectorsEqual_(
        const std::vector<std::string>& vec1,
        const std::vector<std::string>& vec2);
    void rewrite_wrong_words_(std::pair<std::string, std::string> & wrong_words);
    bool mode_();

};

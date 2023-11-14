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
    TestVoca(const std::string& filepath, const std::vector<std::string> &filename);
    void runTest();

protected:
    std::vector<std::pair<std::string, std::string>> words_meanings_;
    
    void Test_(std::vector<std::pair<std::string, std::string>> & words_meanings,
              std::vector<std::pair<std::string, std::string>> & wrong_words);
    void printScore_(const long int total_score);
    void printWrongVoca_(std::vector<std::pair<std::string, std::string>> & wrong_words);

    void save_(const std::vector<std::pair<std::string, std::string>> &  words,
               const bool & save_next_file);
    bool mode_();

private:
    std::string filepath_;
    std::vector<std::string> voca_file_;
    int file_number_;
    std::vector<int> indices_;
    int score_ = 0;
    const int test_size_ = 100;

    std::regex pattern_{ "\\s+" };
    void ReadFile_();
    void shuffle_(const long int words_size);
    bool ContainsComma_(const std::string& str);
    std::vector<std::string> SplitAndSort_(const std::string& input);
    bool AreVectorsEqual_(
        const std::vector<std::string>& vec1,
        const std::vector<std::string>& vec2);
    void rewrite_wrong_words_(std::pair<std::string, std::string> & wrong_words);


};

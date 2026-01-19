#include "voca_test/voca_loader.hpp"

#include <fstream>
#include <iostream>
#include <string>

namespace voca {

bool VocaLoader::loadCSV(const std::string& base_path,
                         std::vector<std::pair<std::string, std::string>>& out) const
{
    std::ifstream file(base_path + ".csv");
    if (!file.is_open()) {
        std::cout << base_path + " not found.\n";
        return false;
    }

    std::string line;
    while (std::getline(file, line)) {
        std::size_t pos = line.find(",");
        if (pos != std::string::npos) {
            std::string word = line.substr(0, pos);
            std::string correct = line.substr(pos + 1);

            word = stripQuotes_(word);
            correct = stripQuotes_(correct);

            out.emplace_back(word, correct);
        }
    }

    return true;
}

std::string VocaLoader::stripQuotes_(const std::string& s) const
{
    if (s.size() >= 2 && s.front() == '"' && s.back() == '"') {
        return s.substr(1, s.size() - 2);
    }
    return s;
}

} // namespace voca

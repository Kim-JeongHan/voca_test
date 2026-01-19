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
            out.emplace_back(line.substr(0, pos), line.substr(pos + 1));
        }
    }

    return true;
}

} // namespace voca

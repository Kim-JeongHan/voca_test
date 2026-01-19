#pragma once

#include <string>
#include <utility>
#include <vector>

namespace voca {

class VocaLoader {
public:
    bool loadCSV(const std::string& base_path,
                 std::vector<std::pair<std::string, std::string>>& out) const;

private:
    std::string stripQuotes_(const std::string& s) const;
};

} // namespace voca

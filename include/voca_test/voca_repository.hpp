#pragma once

#include <cstddef>
#include <string>
#include <utility>
#include <vector>

namespace voca {

class VocaRepository {
public:
    void set(std::vector<std::pair<std::string, std::string>>&& data);
    std::size_t size() const;
    const std::pair<std::string, std::string>& at(std::size_t idx) const;
    const std::vector<std::pair<std::string, std::string>>& data() const;

private:
    std::vector<std::pair<std::string, std::string>> data_;
};

} // namespace voca

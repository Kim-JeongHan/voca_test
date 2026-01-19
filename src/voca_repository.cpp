#include "voca_test/voca_repository.hpp"

namespace voca {

void VocaRepository::set(std::vector<std::pair<std::string, std::string>>&& data)
{
    data_ = std::move(data);
}

std::size_t VocaRepository::size() const
{
    return data_.size();
}

const std::pair<std::string, std::string>& VocaRepository::at(std::size_t idx) const
{
    return data_.at(idx);
}

const std::vector<std::pair<std::string, std::string>>& VocaRepository::data() const
{
    return data_;
}

} // namespace voca

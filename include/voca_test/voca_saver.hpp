#pragma once

#include <string>
#include <vector>

#include "voca_test/voca_result.hpp"

namespace voca {

class VocaSaver {
public:
    bool saveWrongCSV(const std::string& base_name,
                      const std::vector<WrongVoca>& list,
                      int mode) const;
};

} // namespace voca

#include "voca_test/voca_saver.hpp"

#include <fstream>

namespace voca {

bool VocaSaver::saveWrongCSV(const std::string& base_name,
                             const std::vector<WrongVoca>& list,
                             int mode) const
{
    std::string suffix = (mode == 1) ? "_test.csv" : "_wrong.csv";
    std::ofstream output_file(base_name + suffix, std::ios_base::app);
    if (!output_file.is_open()) {
        return false;
    }

    for (const auto& item : list) {
        output_file << item.word << "," << item.correct << std::endl;
    }

    return true;
}

} // namespace voca

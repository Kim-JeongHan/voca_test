#include "voca_test/voca.hpp"

#include <string>
#include <vector>
#include <iostream>

int main(int argc, char* argv[])
{
    std::vector<int> number;
    std::vector<std::string> filename;
    std::string filepath;

    try
    {
        if (argc < 2)
            throw std::runtime_error("Please enter the number of the voca file you want to test.");
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }

    for (int i = 1; i < argc; i++)
    {
        filename.push_back(argv[i]);
    }

    filepath = "../words/";

    TestVoca test(filepath, filename);


    return 0;
}

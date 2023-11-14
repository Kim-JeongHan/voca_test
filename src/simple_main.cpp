#include "voca_test/voca.hpp"
#include <fstream>
#include <string>
#include <vector>


int main(int argc, char* argv[])
{
    std::string fliename, filepath;
    int number;
    fliename = argv[1];
    number = std::stoi(fliename);
    filepath = "../words/";

    TestVoca test(filepath, number);


    return 0;
}

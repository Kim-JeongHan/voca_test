cmake_minimum_required(VERSION 3.10)

project(voca_test_cpp)

set(CMAKE_CXX_STANDARD 17)

add_executable(voca voca.cpp)


install(
    TARGETS voca
    ARCHIVE DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/build/
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/build/
    RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install/
)

install(DIRECTORY ./words
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install
)
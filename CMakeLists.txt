cmake_minimum_required(VERSION 3.10)

project(voca_test)

set(CMAKE_CXX_STANDARD 17)


include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
add_library(
    ${project_name}_lib
    SHARED
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca.cpp
)

add_executable(simple src/simple_main.cpp)
target_link_libraries(simple ${project_name}_lib)

add_executable(multiple src/multiple_main.cpp)
target_link_libraries(multiple ${project_name}_lib)

install(
    TARGETS simple multiple
    ARCHIVE DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/build/
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/build/
    RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install/
)

install(DIRECTORY ./words
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install
)

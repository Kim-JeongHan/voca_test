cmake_minimum_required(VERSION 3.10)

project(voca_test)

set(CMAKE_CXX_STANDARD 17)


include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
add_library(
    ${PROJECT_NAME}_lib
    SHARED
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_loader.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_repository.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_engine.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_result.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_saver.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_session.cpp
)

enable_testing()

add_executable(test_engine tests/test_engine.cpp)
target_link_libraries(test_engine ${PROJECT_NAME}_lib)

add_executable(test_loader tests/test_loader.cpp)
target_link_libraries(test_loader ${PROJECT_NAME}_lib)

add_executable(test_result tests/test_result.cpp)
target_link_libraries(test_result ${PROJECT_NAME}_lib)

add_executable(test_regression tests/test_regression.cpp)
target_link_libraries(test_regression ${PROJECT_NAME}_lib)

add_executable(test_session tests/test_session.cpp)
target_link_libraries(test_session ${PROJECT_NAME}_lib)

add_test(NAME test_engine COMMAND test_engine)
add_test(NAME test_loader COMMAND test_loader)
add_test(NAME test_result COMMAND test_result)
add_test(NAME test_regression COMMAND test_regression)
add_test(NAME test_session COMMAND test_session)

add_executable(simple src/simple_main.cpp)
target_link_libraries(simple ${PROJECT_NAME}_lib)

add_executable(multiple src/multiple_main.cpp)
target_link_libraries(multiple ${PROJECT_NAME}_lib)

install(
    TARGETS simple multiple
    ARCHIVE DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/build/
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/build/
    RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install/
)

install(DIRECTORY ./words
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/install
)

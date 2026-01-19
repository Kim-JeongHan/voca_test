cmake_minimum_required(VERSION 3.10)

project(voca_test)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Core library sources (session API for mobile/WASM)
set(VOCA_CORE_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_loader.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_repository.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_engine.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_result.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_session.cpp
)

# Full library sources (includes CLI facade)
set(VOCA_FULL_SOURCES
    ${VOCA_CORE_SOURCES}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_saver.cpp
)

# voca_core: standalone session API library (for WASM/mobile)
add_library(voca_core STATIC ${VOCA_CORE_SOURCES})
target_include_directories(voca_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# WASM build configuration
if(EMSCRIPTEN)
    add_executable(voca_wasm
        ${CMAKE_CURRENT_SOURCE_DIR}/src/voca_wasm.cpp
    )
    target_link_libraries(voca_wasm voca_core)

    set_target_properties(voca_wasm PROPERTIES
        OUTPUT_NAME "voca_core"
        SUFFIX ".js"
    )

    target_link_options(voca_wasm PRIVATE
        -sEXPORTED_FUNCTIONS=['_voca_session_create','_voca_session_destroy','_voca_session_load_csv','_voca_session_start','_voca_session_start_indices','_voca_session_get_prompt','_voca_session_submit','_voca_session_summary','_voca_session_export_wrong','_voca_session_is_finished','_voca_free_string','_malloc','_free']
        -sEXPORTED_RUNTIME_METHODS=['ccall','cwrap','UTF8ToString','stringToUTF8','lengthBytesUTF8']
        -sMODULARIZE=1
        -sEXPORT_NAME='createVocaCore'
        -sALLOW_MEMORY_GROWTH=1
        -sENVIRONMENT='web'
        --no-entry
    )
endif()

# voca_test_lib: full library with CLI facade (backward compatible)
add_library(${PROJECT_NAME}_lib SHARED ${VOCA_FULL_SOURCES})

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

add_executable(test_golden tests/test_golden.cpp)
target_link_libraries(test_golden ${PROJECT_NAME}_lib)

# WASM API test (only for native builds, not Emscripten)
if(NOT EMSCRIPTEN)
    add_executable(test_wasm_api tests/test_wasm_api.cpp src/voca_wasm.cpp)
    target_link_libraries(test_wasm_api voca_core)
    add_test(NAME test_wasm_api COMMAND test_wasm_api)
endif()

add_test(NAME test_engine COMMAND test_engine)
add_test(NAME test_loader COMMAND test_loader)
add_test(NAME test_result COMMAND test_result)
add_test(NAME test_regression COMMAND test_regression)
add_test(NAME test_session COMMAND test_session)
add_test(NAME test_golden COMMAND test_golden)

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

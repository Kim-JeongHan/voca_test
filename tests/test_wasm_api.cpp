// Test for C API wrapper (WASM interface)
// Ensures the C bindings work correctly before WASM compilation

#include "voca_test/voca_wasm.hpp"

#include <cassert>
#include <cstring>
#include <iostream>
#include <string>

int main()
{
    std::cout << "=== C API (WASM Interface) Tests ===\n";

    // Create session
    VocaSessionHandle session = voca_session_create();
    assert(session != nullptr);

    // Load CSV
    const char* csv = "apple,사과\nbanana,바나나\n";
    int count = voca_session_load_csv(session, csv);
    assert(count == 2);
    std::cout << "Loaded " << count << " words\n";

    // Start session
    voca_session_start(session);
    assert(voca_session_is_finished(session) == 0);

    // Get prompt
    char* prompt = voca_session_get_prompt(session);
    assert(prompt != nullptr);
    std::string prompt_str(prompt);
    assert(prompt_str.find("apple") != std::string::npos);
    std::cout << "Prompt: " << prompt_str << "\n";
    voca_free_string(prompt);

    // Submit wrong answer
    char* feedback1 = voca_session_submit(session, "wrong");
    assert(feedback1 != nullptr);
    std::string fb1_str(feedback1);
    assert(fb1_str.find("\"is_correct\":false") != std::string::npos);
    std::cout << "Wrong feedback: " << fb1_str << "\n";
    voca_free_string(feedback1);

    // Get retry prompt (should show hint)
    char* retry_prompt = voca_session_get_prompt(session);
    std::string retry_str(retry_prompt);
    assert(retry_str.find("Hint") != std::string::npos);
    std::cout << "Retry prompt: " << retry_str << "\n";
    voca_free_string(retry_prompt);

    // Submit correct answer
    char* feedback2 = voca_session_submit(session, "사과");
    std::string fb2_str(feedback2);
    assert(fb2_str.find("\"is_correct\":true") != std::string::npos);
    std::cout << "Correct feedback: " << fb2_str << "\n";
    voca_free_string(feedback2);

    // Continue to next word
    char* prompt2 = voca_session_get_prompt(session);
    std::string p2_str(prompt2);
    assert(p2_str.find("banana") != std::string::npos);
    voca_free_string(prompt2);

    char* feedback3 = voca_session_submit(session, "바나나");
    std::string fb3_str(feedback3);
    assert(fb3_str.find("\"next_action\":\"show_summary\"") != std::string::npos);
    voca_free_string(feedback3);

    // Session should be finished
    assert(voca_session_is_finished(session) == 1);

    // Get summary
    char* summary = voca_session_summary(session);
    std::string sum_str(summary);
    assert(sum_str.find("\"score\":1") != std::string::npos);
    assert(sum_str.find("\"total\":2") != std::string::npos);
    std::cout << "Summary: " << sum_str << "\n";
    voca_free_string(summary);

    // Export wrong
    char* wrong_csv = voca_session_export_wrong(session);
    std::string wrong_str(wrong_csv);
    assert(wrong_str.find("apple,사과") != std::string::npos);
    std::cout << "Wrong CSV:\n" << wrong_str;
    voca_free_string(wrong_csv);

    // Test start with indices
    voca_session_start_indices(session, "1");  // Only banana
    char* idx_prompt = voca_session_get_prompt(session);
    std::string idx_str(idx_prompt);
    assert(idx_str.find("banana") != std::string::npos);
    voca_free_string(idx_prompt);

    // Destroy session
    voca_session_destroy(session);

    std::cout << "=== All C API tests passed ===\n";
    return 0;
}

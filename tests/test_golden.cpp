// Golden tests for session protocol
// Ensures identical JSON output for deterministic inputs
// This guarantees CLI and mobile (WASM) behave identically

#include "voca_test/voca_session.hpp"

#include <cassert>
#include <cstring>
#include <iostream>
#include <string>

namespace {

// Compare JSON strings ignoring whitespace differences
bool jsonEquals(const std::string& a, const std::string& b)
{
    auto strip = [](const std::string& s) {
        std::string result;
        result.reserve(s.size());
        for (char ch : s) {
            if (ch != ' ' && ch != '\n' && ch != '\r' && ch != '\t') {
                result.push_back(ch);
            }
        }
        return result;
    };
    return strip(a) == strip(b);
}

void assertJson(const std::string& actual, const std::string& expected, const char* test_name)
{
    if (!jsonEquals(actual, expected)) {
        std::cerr << "Golden test failed: " << test_name << "\n";
        std::cerr << "Expected: " << expected << "\n";
        std::cerr << "Actual:   " << actual << "\n";
        assert(false);
    }
}

// Test 1: Simple correct answer flow
void test_correct_flow()
{
    voca::VocaSession session;
    session.setWords({{"apple", "사과"}});
    session.start();

    std::string prompt = session.getPromptJson();
    assertJson(prompt,
        R"({"question_id":"0","question_text":"apple","direction":"en_to_kr","hint":"","attempt":1,"progress":{"done":0,"total":1}})",
        "correct_flow_prompt");

    std::string feedback = session.submitAnswer("사과");
    assertJson(feedback,
        R"({"is_correct":true,"correct_answer":"사과","next_action":"show_summary","hint_level":0})",
        "correct_flow_feedback");

    std::string summary = session.summaryJson();
    assertJson(summary,
        R"({"score":1,"total":1,"wrong_count":0})",
        "correct_flow_summary");

    std::cout << "test_correct_flow passed\n";
}

// Test 2: Wrong answer -> retry flow with hint progression
void test_hint_progression()
{
    voca::VocaSession session;
    session.setWords({{"hello", "안녕"}});
    session.start();

    // First attempt
    std::string prompt1 = session.getPromptJson();
    assert(prompt1.find("\"attempt\":1") != std::string::npos);
    assert(prompt1.find("\"hint\":\"\"") != std::string::npos);

    std::string fb1 = session.submitAnswer("wrong");
    assertJson(fb1,
        R"({"is_correct":false,"correct_answer":"안녕","next_action":"retry_same","hint_level":1})",
        "hint_prog_wrong1");

    // Second attempt - hint level 1 (letter count)
    std::string prompt2 = session.getPromptJson();
    assert(prompt2.find("\"attempt\":2") != std::string::npos);
    assert(prompt2.find("Hint:") != std::string::npos);
    assert(prompt2.find("2 글자") != std::string::npos);

    std::string fb2 = session.submitAnswer("wrong");
    assert(fb2.find("\"hint_level\":2") != std::string::npos);

    // Third attempt - hint level 2 (first letter)
    std::string prompt3 = session.getPromptJson();
    assert(prompt3.find("\"attempt\":3") != std::string::npos);

    std::string fb3 = session.submitAnswer("wrong");
    assert(fb3.find("\"hint_level\":3") != std::string::npos);

    // Fourth attempt - hint level 3 (prefix)
    std::string prompt4 = session.getPromptJson();
    assert(prompt4.find("\"attempt\":4") != std::string::npos);

    std::string fb4 = session.submitAnswer("wrong");
    assert(fb4.find("\"hint_level\":4") != std::string::npos);

    // Fifth attempt - hint level 4 (full answer shown)
    std::string prompt5 = session.getPromptJson();
    assert(prompt5.find("type it again") != std::string::npos);

    std::string fb5 = session.submitAnswer("안녕");
    assertJson(fb5,
        R"({"is_correct":true,"correct_answer":"안녕","next_action":"show_summary","hint_level":4})",
        "hint_prog_final_correct");

    std::string summary = session.summaryJson();
    assertJson(summary,
        R"({"score":0,"total":1,"wrong_count":1})",
        "hint_prog_summary");

    std::cout << "test_hint_progression passed\n";
}

// Test 3: Multiple words with mixed results
void test_mixed_results()
{
    voca::VocaSession session;
    session.setWords({{"cat", "고양이"}, {"dog", "강아지"}, {"bird", "새"}});
    session.start();

    // Word 1: correct on first try
    session.getPromptJson();
    std::string fb1 = session.submitAnswer("고양이");
    assert(fb1.find("\"is_correct\":true") != std::string::npos);

    // Word 2: wrong once, then correct
    session.getPromptJson();
    std::string fb2a = session.submitAnswer("wrong");
    assert(fb2a.find("\"is_correct\":false") != std::string::npos);

    session.getPromptJson(); // retry prompt
    std::string fb2b = session.submitAnswer("강아지");
    assert(fb2b.find("\"is_correct\":true") != std::string::npos);

    // Word 3: correct
    session.getPromptJson();
    std::string fb3 = session.submitAnswer("새");
    assert(fb3.find("\"next_action\":\"show_summary\"") != std::string::npos);

    std::string summary = session.summaryJson();
    assertJson(summary,
        R"({"score":2,"total":3,"wrong_count":1})",
        "mixed_results_summary");

    // Verify wrong CSV export
    std::string wrongCSV = session.exportWrongCSV();
    assert(wrongCSV.find("dog,강아지") != std::string::npos);
    assert(wrongCSV.find("cat") == std::string::npos); // cat was correct

    std::cout << "test_mixed_results passed\n";
}

// Test 4: Start with specific indices
void test_start_indices()
{
    voca::VocaSession session;
    session.setWords({{"a", "1"}, {"b", "2"}, {"c", "3"}, {"d", "4"}});
    session.start({1, 3}); // Only "b" and "d"

    std::string prompt1 = session.getPromptJson();
    assert(prompt1.find("\"question_text\":\"b\"") != std::string::npos);

    session.submitAnswer("2");

    std::string prompt2 = session.getPromptJson();
    assert(prompt2.find("\"question_text\":\"d\"") != std::string::npos);

    std::string fb = session.submitAnswer("4");
    assert(fb.find("\"next_action\":\"show_summary\"") != std::string::npos);

    std::string summary = session.summaryJson();
    assertJson(summary,
        R"({"score":2,"total":2,"wrong_count":0})",
        "start_indices_summary");

    std::cout << "test_start_indices passed\n";
}

// Test 5: Empty session handling
void test_empty_session()
{
    voca::VocaSession session;
    session.setWords({});
    session.start();

    assert(session.isFinished());

    std::string summary = session.summaryJson();
    assertJson(summary,
        R"({"score":0,"total":0,"wrong_count":0})",
        "empty_session_summary");

    std::cout << "test_empty_session passed\n";
}

// Test 6: Answer normalization (whitespace, quotes)
void test_answer_normalization()
{
    voca::VocaSession session;
    session.setWords({{"test", "테스트"}});
    session.start();

    session.getPromptJson();

    // Answer with extra whitespace should be accepted
    std::string fb = session.submitAnswer("  테스트  ");
    assert(fb.find("\"is_correct\":true") != std::string::npos);

    std::cout << "test_answer_normalization passed\n";
}

// Test 7: Progress tracking during session
void test_progress_tracking()
{
    voca::VocaSession session;
    session.setWords({{"a", "1"}, {"b", "2"}, {"c", "3"}});
    session.start();

    std::string p1 = session.getPromptJson();
    assert(p1.find("\"done\":0") != std::string::npos);
    assert(p1.find("\"total\":3") != std::string::npos);

    session.submitAnswer("1");

    std::string p2 = session.getPromptJson();
    assert(p2.find("\"done\":1") != std::string::npos);

    session.submitAnswer("2");

    std::string p3 = session.getPromptJson();
    assert(p3.find("\"done\":2") != std::string::npos);

    std::cout << "test_progress_tracking passed\n";
}

} // namespace

int main()
{
    std::cout << "=== Golden Tests for Session Protocol ===\n";

    test_correct_flow();
    test_hint_progression();
    test_mixed_results();
    test_start_indices();
    test_empty_session();
    test_answer_normalization();
    test_progress_tracking();

    std::cout << "=== All golden tests passed ===\n";
    return 0;
}

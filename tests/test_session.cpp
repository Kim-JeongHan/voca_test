#include "voca_test/voca_session.hpp"

#include <cassert>
#include <iostream>

int main()
{
    voca::VocaSession session;
    session.setWords({{"apple", "사과"}, {"banana", "바나나"}});
    session.start();

    std::string prompt1 = session.getPromptJson();
    assert(prompt1.find("\"question_text\":\"apple\"") != std::string::npos);

    std::string feedback1 = session.submitAnswer("wrong");
    assert(feedback1.find("\"is_correct\":false") != std::string::npos);
    assert(feedback1.find("\"next_action\":\"retry_same\"") != std::string::npos);

    std::string prompt_retry = session.getPromptJson();
    assert(prompt_retry.find("\"question_text\":\"apple\"") != std::string::npos);
    assert(prompt_retry.find("\"attempt\":2") != std::string::npos);

    std::string feedback2 = session.submitAnswer("사과");
    assert(feedback2.find("\"is_correct\":true") != std::string::npos);

    std::string prompt2 = session.getPromptJson();
    assert(prompt2.find("\"question_text\":\"banana\"") != std::string::npos);

    std::string feedback3 = session.submitAnswer("바나나");
    assert(feedback3.find("\"next_action\":\"show_summary\"") != std::string::npos);

    std::string summary = session.summaryJson();
    assert(summary.find("\"score\":1") != std::string::npos);
    assert(summary.find("\"total\":2") != std::string::npos);

    std::cout << "test_session passed\n";
    return 0;
}

#include "voca_test/voca_session.hpp"

#include <sstream>

namespace voca {

void VocaSession::setWords(std::vector<std::pair<std::string, std::string>> words)
{
    words_ = std::move(words);
}

void VocaSession::start()
{
    std::vector<int> indices;
    indices.reserve(words_.size());
    for (std::size_t i = 0; i < words_.size(); ++i) {
        indices.push_back(static_cast<int>(i));
    }
    start(indices);
}

void VocaSession::start(const std::vector<int>& indices)
{
    main_queue_.clear();
    retry_queue_.clear();
    result_.reset();
    has_current_ = false;

    for (int idx : indices) {
        if (idx < 0 || static_cast<std::size_t>(idx) >= words_.size()) {
            continue;
        }
        main_queue_.push_back(idx);
    }

    total_ = static_cast<int>(main_queue_.size());
}

std::string VocaSession::getPromptJson()
{
    if (!ensureCurrent_()) {
        return summaryJson();
    }

    int wrong_count = result_.wrongCount(current_.word, current_.correct);
    std::string hint = wrong_count > 0 ? makeHint_(current_.correct, wrong_count) : "";
    int attempt = wrong_count + 1;

    std::ostringstream out;
    out << "{"
        << "\"question_id\":\"" << escapeJson_(current_.question_id) << "\","
        << "\"question_text\":\"" << escapeJson_(current_.word) << "\","
        << "\"direction\":\"en_to_kr\","
        << "\"hint\":\"" << escapeJson_(hint) << "\","
        << "\"attempt\":" << attempt << ","
        << "\"progress\":{\"done\":" << result_.score() << ",\"total\":" << total_ << "}"
        << "}";
    return out.str();
}

std::string VocaSession::submitAnswer(const std::string& answer)
{
    if (!ensureCurrent_()) {
        return "{\"is_correct\":true,\"correct_answer\":\"\",\"next_action\":\"show_summary\",\"hint_level\":0}";
    }

    bool correct = engine_.isCorrect(answer, current_.correct);
    int wrong_count = result_.wrongCount(current_.word, current_.correct);

    if (!correct) {
        if (current_.from_retry) {
            result_.recordWrongAttempt({current_.word, current_.correct});
        } else {
            result_.markWrong({current_.word, current_.correct});
        }

        int next_count = result_.wrongCount(current_.word, current_.correct);
        int hint_level = next_count >= 4 ? 4 : next_count;

        retry_queue_.push_front({current_.word, current_.correct});
        has_current_ = false;

        std::ostringstream out;
        out << "{"
            << "\"is_correct\":false,"
            << "\"correct_answer\":\"" << escapeJson_(current_.correct) << "\","
            << "\"next_action\":\"retry_same\","
            << "\"hint_level\":" << hint_level
            << "}";
        return out.str();
    }

    if (!current_.from_retry) {
        result_.markCorrect();
    }

    has_current_ = false;

    std::string next_action = (main_queue_.empty() && retry_queue_.empty())
        ? "show_summary"
        : "next_question";

    std::ostringstream out;
    out << "{"
        << "\"is_correct\":true,"
        << "\"correct_answer\":\"" << escapeJson_(current_.correct) << "\","
        << "\"next_action\":\"" << next_action << "\","
        << "\"hint_level\":" << wrong_count
        << "}";
    return out.str();
}

std::string VocaSession::summaryJson() const
{
    std::ostringstream out;
    out << "{"
        << "\"score\":" << result_.score() << ","
        << "\"total\":" << total_ << ","
        << "\"wrong_count\":" << static_cast<int>(result_.wrongList().size())
        << "}";
    return out.str();
}

std::string VocaSession::exportWrongCSV() const
{
    std::ostringstream out;
    for (const auto& item : result_.wrongList()) {
        out << item.word << "," << item.correct << "\n";
    }
    return out.str();
}

bool VocaSession::isFinished() const
{
    return !has_current_ && main_queue_.empty() && retry_queue_.empty();
}

bool VocaSession::ensureCurrent_()
{
    if (has_current_) {
        return true;
    }

    if (!retry_queue_.empty()) {
        const auto current = retry_queue_.front();
        retry_queue_.pop_front();
        current_ = {current.word, current.correct, current.word, true};
        has_current_ = true;
        return true;
    }

    if (!main_queue_.empty()) {
        int idx = main_queue_.front();
        main_queue_.pop_front();
        if (idx < 0 || static_cast<std::size_t>(idx) >= words_.size()) {
            return ensureCurrent_();
        }
        current_ = {words_[idx].first, words_[idx].second, std::to_string(idx), false};
        has_current_ = true;
        return true;
    }

    return false;
}

std::string VocaSession::makeHint_(const std::string& correct, int wrong_count) const
{
    std::string hint = correct;
    if (hint.size() >= 2 && hint.front() == '"' && hint.back() == '"') {
        hint = hint.substr(1, hint.size() - 2);
    } else if (!hint.empty() && hint.front() == '"') {
        hint = hint.substr(1);
    } else if (!hint.empty() && hint.back() == '"') {
        hint = hint.substr(0, hint.size() - 1);
    }

    std::string compact;
    compact.reserve(hint.size());
    for (char ch : hint) {
        if (ch == ',' || ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r') {
            continue;
        }
        compact.push_back(ch);
    }

    auto splitUtf8 = [](const std::string& s) {
        std::vector<std::string> units;
        for (std::size_t i = 0; i < s.size();) {
            unsigned char c = static_cast<unsigned char>(s[i]);
            std::size_t len = 1;
            if ((c & 0x80) == 0x00) {
                len = 1;
            } else if ((c & 0xE0) == 0xC0) {
                len = 2;
            } else if ((c & 0xF0) == 0xE0) {
                len = 3;
            } else if ((c & 0xF8) == 0xF0) {
                len = 4;
            }

            if (i + len > s.size()) {
                len = 1;
            }
            units.emplace_back(s.substr(i, len));
            i += len;
        }
        return units;
    };

    const auto units = splitUtf8(compact);
    std::size_t len = units.size();
    if (len == 0) {
        return "Hint: (no letters)";
    }

    if (wrong_count == 1) {
        return "Hint: " + std::string(len, '_') + " (" + std::to_string(len) + " 글자)";
    }

    if (wrong_count == 2) {
        return "Hint: " + units[0] + std::string(len - 1, '_');
    }

    if (wrong_count == 3) {
        std::size_t reveal = std::min<std::size_t>(2, len > 0 ? len - 1 : 0);
        std::string prefix;
        for (std::size_t i = 0; i < reveal; ++i) {
            prefix += units[i];
        }
        return "Hint: " + prefix + std::string(len - reveal, '_');
    }

    return "Hint: " + hint + " (type it again)";
}

std::string VocaSession::escapeJson_(const std::string& s)
{
    std::string out;
    out.reserve(s.size());
    for (char ch : s) {
        switch (ch) {
        case '\\':
            out += "\\\\";
            break;
        case '"':
            out += "\\\"";
            break;
        case '\n':
            out += "\\n";
            break;
        case '\r':
            out += "\\r";
            break;
        case '\t':
            out += "\\t";
            break;
        default:
            out.push_back(ch);
            break;
        }
    }
    return out;
}

} // namespace voca

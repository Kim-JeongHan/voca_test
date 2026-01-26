/**
 * pybind11 bindings for voca_test C++ engine
 *
 * Exposes the core C++ classes to Python for use in FastAPI backend.
 * Build with: cmake -DBUILD_PYTHON=ON
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "voca_test/voca_engine.hpp"
#include "voca_test/voca_repository.hpp"
#include "voca_test/voca_result.hpp"
#include "voca_test/voca_session.hpp"

namespace py = pybind11;

PYBIND11_MODULE(voca_cpp, m) {
    m.doc() = "C++ vocabulary test engine bindings";

    // WrongVoca struct
    py::class_<voca::WrongVoca>(m, "WrongVoca")
        .def(py::init<>())
        .def_readwrite("word", &voca::WrongVoca::word)
        .def_readwrite("correct", &voca::WrongVoca::correct)
        .def_readwrite("wrong_count", &voca::WrongVoca::wrong_count);

    // VocaTestEngine class
    py::class_<voca::VocaTestEngine>(m, "VocaTestEngine")
        .def(py::init<>())
        .def("is_correct", &voca::VocaTestEngine::isCorrect,
             py::arg("answer"), py::arg("correct"),
             "Check if the answer matches the correct answer(s)")
        .def("strip_quotes", &voca::VocaTestEngine::stripQuotes,
             py::arg("text"),
             "Remove surrounding quotes from text");

    // VocaRepository class
    py::class_<voca::VocaRepository>(m, "VocaRepository")
        .def(py::init<>())
        .def("set", [](voca::VocaRepository& self,
                       std::vector<std::pair<std::string, std::string>> data) {
            self.set(std::move(data));
        }, py::arg("data"), "Set word data as list of (word, meaning) pairs")
        .def("size", &voca::VocaRepository::size, "Get number of words")
        .def("at", &voca::VocaRepository::at, py::arg("index"),
             "Get word at index", py::return_value_policy::reference)
        .def("data", &voca::VocaRepository::data,
             "Get all word data", py::return_value_policy::reference);

    // VocaResult class
    py::class_<voca::VocaResult>(m, "VocaResult")
        .def(py::init<>())
        .def("mark_correct", &voca::VocaResult::markCorrect)
        .def("mark_wrong", &voca::VocaResult::markWrong, py::arg("wrong"))
        .def("record_wrong_attempt", &voca::VocaResult::recordWrongAttempt,
             py::arg("wrong"))
        .def("wrong_count", &voca::VocaResult::wrongCount,
             py::arg("word"), py::arg("correct"))
        .def("score", &voca::VocaResult::score, "Get correct answer count")
        .def("total", &voca::VocaResult::total, "Get total question count")
        .def("wrong_list", &voca::VocaResult::wrongList,
             "Get list of wrong answers", py::return_value_policy::reference)
        .def("reset", &voca::VocaResult::reset, "Reset results");

    // VocaSession class - main API for quiz sessions
    py::class_<voca::VocaSession>(m, "VocaSession")
        .def(py::init<>())
        .def("set_words", &voca::VocaSession::setWords, py::arg("words"),
             "Set words as list of (word, meaning) pairs")
        .def("start", py::overload_cast<>(&voca::VocaSession::start),
             "Start quiz with all words in order")
        .def("start_indices", py::overload_cast<const std::vector<int>&>(
                 &voca::VocaSession::start),
             py::arg("indices"),
             "Start quiz with specific word indices")
        .def("get_prompt_json", &voca::VocaSession::getPromptJson,
             "Get current question as JSON string")
        .def("submit_answer", &voca::VocaSession::submitAnswer,
             py::arg("answer"),
             "Submit answer and get result as JSON string")
        .def("summary_json", &voca::VocaSession::summaryJson,
             "Get session summary as JSON string")
        .def("export_wrong_csv", &voca::VocaSession::exportWrongCSV,
             "Export wrong answers as CSV string")
        .def("is_finished", &voca::VocaSession::isFinished,
             "Check if quiz is finished");
}

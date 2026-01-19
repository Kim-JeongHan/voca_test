#pragma once

#ifdef __cplusplus
extern "C" {
#endif

// Session handle type (opaque pointer)
typedef void* VocaSessionHandle;

// Create a new session
VocaSessionHandle voca_session_create();

// Destroy a session
void voca_session_destroy(VocaSessionHandle handle);

// Load words from CSV text (returns number of words loaded)
int voca_session_load_csv(VocaSessionHandle handle, const char* csv_text);

// Start session with all words
void voca_session_start(VocaSessionHandle handle);

// Start session with specific indices (comma-separated, e.g., "0,2,5")
void voca_session_start_indices(VocaSessionHandle handle, const char* indices);

// Get current prompt as JSON (caller must free with voca_free_string)
char* voca_session_get_prompt(VocaSessionHandle handle);

// Submit answer and get feedback as JSON (caller must free with voca_free_string)
char* voca_session_submit(VocaSessionHandle handle, const char* answer);

// Get session summary as JSON (caller must free with voca_free_string)
char* voca_session_summary(VocaSessionHandle handle);

// Export wrong answers as CSV (caller must free with voca_free_string)
char* voca_session_export_wrong(VocaSessionHandle handle);

// Check if session is finished (returns 1 if finished, 0 otherwise)
int voca_session_is_finished(VocaSessionHandle handle);

// Free a string returned by other functions
void voca_free_string(char* str);

#ifdef __cplusplus
}
#endif

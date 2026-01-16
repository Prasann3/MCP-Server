#include <iostream>
#include <string>
#include <vector>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <cstdint>
#include "json.hpp"
#include <poppler/cpp/poppler-document.h>
#include <poppler/cpp/poppler-page.h>
#include "spdlog/spdlog.h"
#include "spdlog/sinks/ansicolor_sink.h"
#include "spdlog/sinks/stdout_color_sinks.h"

using namespace std;
using json = nlohmann::json;

// --- Thread-Safe Queue for Jobs ---
struct Job {
    string id;
    string path;
};

queue<Job> job_queue;
mutex queue_mutex;
condition_variable queue_cv;
bool stop_worker = false;

// --- Mutex for Synchronized Output ---
mutex cout_mutex;

// Helper to read exactly N bytes from stdin (Binary safe)
bool read_exactly(char* buffer, size_t size) {
    size_t bytes_read = 0;
    while (bytes_read < size) {
        cin.read(buffer + bytes_read, size - bytes_read);
        streamsize last_read = cin.gcount();
        if (last_read <= 0) return false; 
        bytes_read += (size_t)last_read;
    }
    return true;
}

// --- Function to send binary-framed JSON to Python ---
void send_to_python(const json& j) {
    string s = j.dump();
    uint32_t len = static_cast<uint32_t>(s.size());

    // Lock the output stream so threads don't mix their bytes
    lock_guard<mutex> lock(cout_mutex);
    
    // 4-byte header + JSON body
    cout.write(reinterpret_cast<const char*>(&len), sizeof(len));
    cout.write(s.data(), len);
    cout.flush();
}

// --- The Worker Thread Logic ---
void worker_thread_func(int thread_id) {
    cerr << "[C++ Thread " << thread_id << "] Started." << endl;

    while (true) {
        Job current_job;

        {
            unique_lock<mutex> lock(queue_mutex);
            queue_cv.wait(lock, [] { return !job_queue.empty() || stop_worker; });

            if (stop_worker && job_queue.empty()) return;

            current_job = job_queue.front();
            job_queue.pop();
        }

        cerr << "[C++ Thread " << thread_id << "] Processing Job: " << current_job.id << endl;
        
        // --- SIMULATE PDF WORK ---
        string extracted_text = "";
        string status = "Success";
        string error = "";
        // 1. Load the document
        poppler::document* doc = poppler::document::load_from_file(current_job.path);
        
        if (!doc) {
            cerr << "[C++ Error] Could not open file: " << current_job.path << endl;
            status = "Failed";
            error = "Could not open file";

        } else {
            // 2. Loop through all pages
            int num_pages = doc->pages();
            for (int i = 0; i < num_pages; ++i) {
                poppler::page* p = doc->create_page(i);
                if (p) {
                    // 3. Extract text from the page
                    // The 'to_utf8()' ensures we handle special characters correctly
                    poppler::ustring u_text = p->text();
                    extracted_text += u_text.to_utf8().data();
                    extracted_text += "\n"; // Add spacing between pages
                    delete p;
                }
            }
            delete doc;
        }        

        json response;
        response["job_id"] = current_job.id;
        response["text"] = extracted_text;
        response["status"] = status;
        if(status == "Failed")response["error"] = error;

        send_to_python(response);
    }
}

int main() {


    // --- Configuring the logger ----//
    auto stderr_sink = make_shared<spdlog::sinks::stderr_color_sink_mt>();
    
    // Create the logger with this specific sink
    auto logger = make_shared<spdlog::logger>("C++", stderr_sink);
    
    // Set as global default logger
    spdlog::set_default_logger(logger);

    spdlog::info("C++ Process started");

    const int num_threads = thread::hardware_concurrency();
    vector<thread> workers;

    for (int i = 0; i < num_threads; ++i) {
        workers.emplace_back(worker_thread_func, i);
    }

    // --- Main Thread: Binary Producer ---
    while (true) {
        uint32_t msg_len = 0;

        // 1. Read 4-byte length header
        if (!read_exactly(reinterpret_cast<char*>(&msg_len), sizeof(msg_len))) {
            break; // Stream closed
        }

        // 2. Read the JSON payload
        string buffer(msg_len, '\0');
        if (!read_exactly(&buffer[0], msg_len)) {
            spdlog::error(" Failed to read complete payload");
            break;
        }

        try {
            json input = json::parse(buffer);
            
            {
                lock_guard<mutex> lock(queue_mutex);
                job_queue.push({input["job_id"], input["file_path"]});
            }
            queue_cv.notify_one();

        } catch (const exception& e) {
            spdlog::error("JSON Parse Failure: " , e.what());
        }
    }

    // Shutdown
    cerr << "[C++ Main] Pipeline closed. Cleaning up..." << endl;
    {
        lock_guard<mutex> lock(queue_mutex);
        stop_worker = true;
    }
    queue_cv.notify_all();

    for (auto& t : workers) {
        if (t.joinable()) t.join();
    }

    return 0;
}
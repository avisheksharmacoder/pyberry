# cython: language_level=3
import sys
from pyberry.config import config

cdef extern from *:
    """
    #include <stddef.h>
    #include <stdatomic.h>
    #include <stdio.h>
    #include <time.h>
    #include <unistd.h>
    #include <pthread.h>

    #define LOG_QUEUE_SIZE 8192

    typedef struct {
        char method[16];
        char path[1024];
        int status;
    } LogEntry;

    typedef struct {
        _Atomic size_t head;
        char pad1[64];
        _Atomic size_t tail;
        char pad2[64];
        LogEntry entries[LOG_QUEUE_SIZE];
    } LogRingBuffer;

    static LogRingBuffer log_buffer = {0};

    static inline int push_log_c(const char* method, const char* path, int status) {
        size_t current_tail = atomic_load_explicit(&log_buffer.tail, memory_order_relaxed);
        size_t next_tail = (current_tail + 1) % LOG_QUEUE_SIZE;
        size_t current_head = atomic_load_explicit(&log_buffer.head, memory_order_acquire);
        
        if (next_tail == current_head) {
            return 0; // Full
        }
        
        size_t i = 0;
        while(i < 15 && method[i] != '\\0') { log_buffer.entries[current_tail].method[i] = method[i]; i++; }
        log_buffer.entries[current_tail].method[i] = '\\0';
        
        i = 0;
        while(i < 1023 && path[i] != '\\0') { log_buffer.entries[current_tail].path[i] = path[i]; i++; }
        log_buffer.entries[current_tail].path[i] = '\\0';
        
        log_buffer.entries[current_tail].status = status;
        
        atomic_store_explicit(&log_buffer.tail, next_tail, memory_order_release);
        return 1; // Success
    }

    static inline int pop_log_c(LogEntry* out_entry) {
        size_t current_head = atomic_load_explicit(&log_buffer.head, memory_order_relaxed);
        size_t current_tail = atomic_load_explicit(&log_buffer.tail, memory_order_acquire);
        
        if (current_head == current_tail) {
            return 0; // Empty
        }
        
        *out_entry = log_buffer.entries[current_head];
        
        size_t next_head = (current_head + 1) % LOG_QUEUE_SIZE;
        atomic_store_explicit(&log_buffer.head, next_head, memory_order_release);
        return 1;
    }

    static void* c_log_worker(void* arg) {
        LogEntry entry;
        char time_buf[64];
        time_t now;
        struct tm* tm_info;
        FILE* log_file = fopen("berrypy.log", "a");
        if (log_file) {
            setvbuf(log_file, NULL, _IOFBF, 65536);
        }
        
        const char* C_GET = "\\033[92m";
        const char* C_POST = "\\033[94m";
        const char* C_PUT = "\\033[93m";
        const char* C_DELETE = "\\033[91m";
        const char* C_STATUS_200 = "\\033[92m";
        const char* C_STATUS_400 = "\\033[93m";
        const char* C_STATUS_500 = "\\033[91m";
        const char* C_RESET = "\\033[0m";

        while (1) {
            if (pop_log_c(&entry)) {
                time(&now);
                tm_info = localtime(&now);
                strftime(time_buf, 64, "%Y-%m-%d %H:%M:%S", tm_info);
                
                const char* method_color = C_RESET;
                if (entry.method[0] == 'G') method_color = C_GET;
                else if (entry.method[0] == 'P' && entry.method[1] == 'O') method_color = C_POST;
                else if (entry.method[0] == 'P' && entry.method[1] == 'U') method_color = C_PUT;
                else if (entry.method[0] == 'D') method_color = C_DELETE;
                
                const char* status_color = C_STATUS_200;
                if (entry.status >= 400 && entry.status < 500) status_color = C_STATUS_400;
                else if (entry.status >= 500) status_color = C_STATUS_500;
                
                fprintf(stdout, "[%s] %s%s%s %s - %s%d%s\\n", 
                    time_buf, method_color, entry.method, C_RESET, entry.path, status_color, entry.status, C_RESET);
                
                if (log_file) {
                    fprintf(log_file, "[%s] %s %s - %d\\n", time_buf, entry.method, entry.path, entry.status);
                    // Let libc buffer the file writes to avoid OS bottlenecks
                }
            } else {
                usleep(1000); // 1ms sleep
            }
        }
        if (log_file) fclose(log_file);
        return NULL;
    }

    static pthread_t log_thread;
    static int thread_started = 0;

    static void start_logger_c() {
        if (!thread_started) {
            pthread_create(&log_thread, NULL, c_log_worker, NULL);
            thread_started = 1;
        }
    }
    """
    void start_logger_c()
    int push_log_c(const char* method, const char* path, int status) nogil

cdef bint c_logging_enabled = True

try:
    c_logging_enabled = bool(config.logging_enabled)
except Exception:
    pass

def start_logger():
    if c_logging_enabled:
        start_logger_c()

cdef void push_log(const char* method, const char* path, int status) noexcept nogil:
    if not c_logging_enabled:
        return
    push_log_c(method, path, status)

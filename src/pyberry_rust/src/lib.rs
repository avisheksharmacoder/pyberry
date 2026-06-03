use pyo3::prelude::*;
use pyo3::ffi::PyObject as RawPyObject;
use tokio::runtime::Runtime;
use once_cell::sync::Lazy;
use libc::{write, c_void};
use std::os::unix::io::RawFd;

// 1. Define the signature of your Cython push_io_c function
type PushIoCFn = unsafe extern "C" fn(*mut RawPyObject, *mut RawPyObject) -> std::os::raw::c_int;

// 2. Global State: The Tokio Runtime, the C-Function Pointer, and the EventFD
static TOKIO_RT: Lazy<Runtime> = Lazy::new(|| {
    Runtime::new().expect("Failed to initialize Tokio runtime")
});

static mut PUSH_IO_C: Option<PushIoCFn> = None;
static mut EVENT_FD: RawFd = -1;

// 3. The Initialization Hook (Called once by Cython on startup)
#[pyfunction]
fn init_rust_engine(push_io_ptr: usize, event_fd: i32) {
    unsafe {
        // Cast the raw memory address from Cython back into a callable Rust function pointer
        PUSH_IO_C = Some(std::mem::transmute(push_io_ptr));
        EVENT_FD = event_fd;
    }
    // Force the runtime to spin up
    let _ = Lazy::force(&TOKIO_RT);
    println!("[PyBerry Rust] Tokio Runtime & FFI Bridge Initialized.");
}

// 4. The Hot Path: Cython submits a Future here
#[pyfunction]
fn submit_io_task(future_ptr: usize, payload: String) {
    TOKIO_RT.spawn(async move {
        // --- REAL I/O HAPPENS HERE OFF THE GIL ---
        // e.g., tokio::time::sleep, reqwest HTTP calls, SurrealDB queries
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
        
        let result_string = format!("Tokio processed: {}", payload);
        
        // --- GIL RE-ACQUISITION BOUNDARY ---
        // We must briefly acquire the GIL to create the Python string and inject it back
        Python::with_gil(|py| {
            // Re-cast the usize back into the raw pointer inside the thread
            let raw_future = future_ptr as *mut RawPyObject;
            // Create the result PyObject
            let py_result = pyo3::types::PyString::new_bound(py, &result_string);
            
            // Convert to raw pointer and INCREF to hand ownership to the C-Queue
            let raw_result = py_result.into_ptr();
            
            unsafe {
                if let Some(push_fn) = PUSH_IO_C {
                    // Push to Cython's lock-free ring buffer
                    let success = push_fn(raw_future, raw_result);
                    
                    if success == 1 {
                        // Wake up uvloop!
                        let val: u64 = 1;
                        write(EVENT_FD, &val as *const u64 as *const c_void, 8);
                    } else {
                        // Queue full! Undo references to prevent leaks
                        pyo3::ffi::Py_DecRef(raw_future);
                        pyo3::ffi::Py_DecRef(raw_result);
                        eprintln!("[PyBerry Rust] FATAL: I/O Queue Full. Dropping result.");
                    }
                }
            }
        });
    });
}

// 5. Expose the module to Python
#[pymodule]
fn pyberry_rust(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(init_rust_engine, m)?)?;
    m.add_function(wrap_pyfunction!(submit_io_task, m)?)?;
    Ok(())
}

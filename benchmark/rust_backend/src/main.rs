// To start the server (in release mode for best performance):
// cargo run --release
use axum::{
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct TestModel {
    id: i32,
    name: String,
    is_active: bool,
}

#[derive(Serialize)]
struct ResponseData {
    status: String,
    received_id: i32,
    received_name: String,
    received_active_status: bool,
}

async fn benchmark_endpoint(Json(payload): Json<TestModel>) -> Json<ResponseData> {
    Json(ResponseData {
        status: "success".to_string(),
        received_id: payload.id,
        received_name: payload.name,
        received_active_status: payload.is_active,
    })
}

#[tokio::main(worker_threads = 1)]
async fn main() {
    let app = Router::new()
        .route("/", get(|| async { "Hello from compiled C-endpoint via Radix Tree!" }))
        .route("/test-benchmark", post(benchmark_endpoint));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:8000").await.unwrap();
    println!("listening on {}", listener.local_addr().unwrap());
    axum::serve(listener, app).await.unwrap();
}

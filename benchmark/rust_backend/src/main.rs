use axum::{
    routing::get,
    Router,
};

#[tokio::main(worker_threads = 1)]
async fn main() {
    // build our application with a single route
    let app = Router::new().route("/", get(|| async { "Hello from compiled C-endpoint via Radix Tree!" }));

    // run our app with hyper, listening globally on port 8000
    let listener = tokio::net::TcpListener::bind("127.0.0.1:8000").await.unwrap();
    println!("listening on {}", listener.local_addr().unwrap());
    axum::serve(listener, app).await.unwrap();
}

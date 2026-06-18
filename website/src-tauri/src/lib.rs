use std::net::{SocketAddr, TcpStream};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct ServerState {
    process: Mutex<Option<CommandChild>>,
}

fn server_addr() -> SocketAddr {
    "127.0.0.1:51441".parse().expect("valid server address")
}

fn is_server_running() -> bool {
    TcpStream::connect_timeout(&server_addr(), Duration::from_millis(500)).is_ok()
}

fn stop_server_process(state: &tauri::State<ServerState>) -> Result<bool, String> {
    let mut process = state.process.lock().map_err(|_| "Failed to lock server state")?;

    if let Some(child) = process.take() {
        let _ = child.kill();
        std::thread::sleep(Duration::from_millis(300));
    }

    Ok(is_server_running())
}

#[tauri::command]
fn server_status() -> bool {
    is_server_running()
}

fn start_server_process(
    app: &tauri::AppHandle,
    state: &tauri::State<ServerState>,
) -> Result<bool, String> {
    if is_server_running() {
        return Ok(true);
    }

    let mut process = state.process.lock().map_err(|_| "Failed to lock server state")?;
    let (mut rx, child) = app
        .shell()
        .sidecar("purifyt-server")
        .map_err(|e| e.to_string())?
        .spawn()
        .map_err(|e| e.to_string())?;

    tauri::async_runtime::spawn(async move {
        while rx.recv().await.is_some() {}
    });

    *process = Some(child);
    std::thread::sleep(Duration::from_millis(800));
    Ok(is_server_running())
}

#[tauri::command]
fn start_server(app: tauri::AppHandle, state: tauri::State<ServerState>) -> Result<bool, String> {
    start_server_process(&app, &state)
}

#[tauri::command]
fn stop_server(state: tauri::State<ServerState>) -> Result<bool, String> {
    stop_server_process(&state)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(ServerState {
            process: Mutex::new(None),
        })
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let handle = app.handle().clone();
            let state = app.state::<ServerState>();

            if let Err(error) = start_server_process(&handle, &state) {
                eprintln!("Failed to auto-start Purifyt server: {error}");
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![server_status, start_server, stop_server])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| match event {
            tauri::RunEvent::ExitRequested { .. }
            | tauri::RunEvent::Exit
            | tauri::RunEvent::WindowEvent {
                event: tauri::WindowEvent::Destroyed,
                ..
            } => {
                let state = app.state::<ServerState>();
                let _ = stop_server_process(&state);
            }
            _ => {}
        });
}

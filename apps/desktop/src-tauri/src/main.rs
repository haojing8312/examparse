#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Serialize;
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader};
use std::thread;

#[derive(Serialize)]
struct EventLine {
    line: String,
}

#[tauri::command]
async fn start_mock(window: tauri::Window) -> Result<(), String> {
    let mut cmd = Command::new("python");
    cmd.arg("-m").arg("sidecar.main").arg("--mock").arg("--input").arg("tmp/a.pdf")
        .stdout(Stdio::piped()).stderr(Stdio::null());

    let mut child = cmd.spawn().map_err(|e| e.to_string())?;
    let stdout = child.stdout.take().ok_or("no stdout")?;
    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(l) = line {
                let _ = window.emit("sidecar-event", l);
            }
        }
    });
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![start_mock])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}



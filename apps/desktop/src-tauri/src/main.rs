#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Serialize;
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader};
use std::thread;
use tauri::Emitter;
use std::path::{Path, PathBuf};
use std::env;

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

fn find_repo_root(start: &Path) -> Option<PathBuf> {
    let mut cur = start.to_path_buf();
    for _ in 0..6 {
        if cur.join("pyproject.toml").exists() || cur.join("sidecar").is_dir() {
            return Some(cur);
        }
        if !cur.pop() {
            break;
        }
    }
    None
}

fn choose_python_exec(repo_root: &Path) -> PathBuf {
    // Prefer project venv python on Windows: .venv\\Scripts\\python.exe
    let candidate = repo_root.join(".venv").join("Scripts").join("python.exe");
    if candidate.exists() {
        return candidate;
    }
    // Fallback to "python" on PATH
    PathBuf::from("python")
}

#[tauri::command]
async fn start_jobs(window: tauri::Window, inputs: Vec<String>, output_dir: Option<String>) -> Result<(), String> {
    if inputs.is_empty() {
        return Err("no inputs provided".to_string());
    }
    let cwd = env::current_dir().map_err(|e| e.to_string())?;
    let repo_root = find_repo_root(&cwd).ok_or_else(|| "cannot locate repo root (pyproject.toml)".to_string())?;

    let python = choose_python_exec(&repo_root);

    let mut cmd = Command::new(python);
    cmd.arg("-m").arg("sidecar.main");
    if inputs.len() == 1 {
        cmd.arg("--input").arg(&inputs[0]);
    } else {
        cmd.arg("--inputs");
        for p in &inputs {
            cmd.arg(p);
        }
    }
    if let Some(out) = output_dir.as_ref() {
        if inputs.len() == 1 {
            cmd.arg("--output").arg(out);
        } else {
            cmd.arg("--output-dir").arg(out);
        }
    }
    // Ensure PYTHONPATH can import sidecar package from repo root
    cmd.env("PYTHONPATH", &repo_root);
    cmd.current_dir(&repo_root);
    cmd.stdout(Stdio::piped()).stderr(Stdio::null());

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
        .invoke_handler(tauri::generate_handler![start_mock, start_jobs])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}



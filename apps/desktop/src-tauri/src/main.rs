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

fn get_sidecar_command(app_handle: &tauri::AppHandle) -> Result<PathBuf, String> {
    // 在开发模式下，使用 Python 解释器运行
    #[cfg(debug_assertions)]
    {
        let cwd = env::current_dir().map_err(|e| e.to_string())?;
        let repo_root = find_repo_root(&cwd).ok_or_else(|| "cannot locate repo root (pyproject.toml)".to_string())?;
        let python = choose_python_exec(&repo_root);
        return Ok(python);
    }

    // 在发布模式下，使用打包的 sidecar 可执行文件
    #[cfg(not(debug_assertions))]
    {
        let sidecar_name = if cfg!(target_os = "windows") {
            "examparse-sidecar.exe"
        } else {
            "examparse-sidecar"
        };
        
        // 尝试多个可能的路径
        let possible_paths = [
            app_handle.path().resource_dir().map(|p| p.join("sidecar-dist").join(sidecar_name)),
            app_handle.path().app_data_dir().map(|p| p.join("sidecar-dist").join(sidecar_name)),
            Some(PathBuf::from("sidecar-dist").join(sidecar_name)),
        ];

        for path_opt in possible_paths.iter() {
            if let Some(path) = path_opt {
                if path.exists() {
                    return Ok(path.clone());
                }
            }
        }

        return Err(format!("Sidecar executable not found: {}", sidecar_name));
    }
}

fn create_sidecar_command(app_handle: &tauri::AppHandle, is_mock: bool, inputs: Vec<String>, output_dir: Option<String>) -> Result<Command, String> {
    let sidecar_path = get_sidecar_command(app_handle)?;
    
    #[cfg(debug_assertions)]
    {
        // 开发模式：使用 Python 解释器
        let mut cmd = Command::new(sidecar_path);
        cmd.arg("-m").arg("sidecar.main");
        
        if is_mock {
            cmd.arg("--mock");
        }
        
        if inputs.len() == 1 {
            cmd.arg("--input").arg(&inputs[0]);
        } else if inputs.len() > 1 {
            cmd.arg("--inputs");
            for input in &inputs {
                cmd.arg(input);
            }
        }
        
        if let Some(out) = output_dir.as_ref() {
            if inputs.len() == 1 {
                cmd.arg("--output").arg(out);
            } else {
                cmd.arg("--output-dir").arg(out);
            }
        }
        
        // 设置工作目录和环境变量
        let cwd = env::current_dir().map_err(|e| e.to_string())?;
        let repo_root = find_repo_root(&cwd).ok_or_else(|| "cannot locate repo root".to_string())?;
        cmd.env("PYTHONPATH", &repo_root);
        cmd.current_dir(&repo_root);
        
        return Ok(cmd);
    }
    
    #[cfg(not(debug_assertions))]
    {
        // 发布模式：直接使用可执行文件
        let mut cmd = Command::new(sidecar_path);
        
        if is_mock {
            cmd.arg("--mock");
        }
        
        if inputs.len() == 1 {
            cmd.arg("--input").arg(&inputs[0]);
        } else if inputs.len() > 1 {
            cmd.arg("--inputs");
            for input in &inputs {
                cmd.arg(input);
            }
        }
        
        if let Some(out) = output_dir.as_ref() {
            if inputs.len() == 1 {
                cmd.arg("--output").arg(out);
            } else {
                cmd.arg("--output-dir").arg(out);
            }
        }
        
        return Ok(cmd);
    }
}

#[tauri::command]
async fn start_mock(app_handle: tauri::AppHandle, window: tauri::Window) -> Result<(), String> {
    let inputs = vec!["tmp/a.pdf".to_string()];
    let mut cmd = create_sidecar_command(&app_handle, true, inputs, None)?;
    cmd.stdout(Stdio::piped()).stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to start sidecar: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to get stdout")?;
    
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
    
    // Try Unix-like venv path: .venv/bin/python
    let candidate = repo_root.join(".venv").join("bin").join("python");
    if candidate.exists() {
        return candidate;
    }
    
    // Fallback to "python" on PATH
    PathBuf::from("python")
}

#[tauri::command]
async fn start_jobs(app_handle: tauri::AppHandle, window: tauri::Window, inputs: Vec<String>, output_dir: Option<String>) -> Result<(), String> {
    if inputs.is_empty() {
        return Err("No inputs provided".to_string());
    }
    
    let mut cmd = create_sidecar_command(&app_handle, false, inputs, output_dir)?;
    cmd.stdout(Stdio::piped()).stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to start sidecar: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to get stdout")?;
    
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



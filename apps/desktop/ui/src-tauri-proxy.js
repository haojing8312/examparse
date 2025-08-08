// 开发模式下，vite 通过此代理转发 /tauri/* 到 tauri 后端（可按需拓展）
export default function tauriProxy() {
  return {
    name: 'tauri-proxy',
    configureServer(server) {
      server.middlewares.use('/tauri', (req, res, next) => {
        // 这里可根据需要实现 HTTP → Tauri 命令桥。当前占位，实际事件通过 window.emit 发送。
        res.statusCode = 404
        res.end('tauri proxy not implemented')
      })
    },
  }
}



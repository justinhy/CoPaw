# T14 工作机 CoPaw 配置记录

> 本文档记录 CoPaw 在 T14 工作机上的安装配置信息，便于问题排查和版本追踪。

## 环境信息

| 项目 | 值 |
|------|-----|
| 操作系统 | Windows 11 |
| Python | 3.13.12 |
| Node.js | v24.14.0 |
| npm | 11.11.0 |

## 安装位置

| 项目 | 路径 |
|------|------|
| 项目目录 | `D:\代码\thirdpart\copaw` |
| CoPaw 工作目录 | `C:\Users\huang\.copaw` |
| CoPaw CLI | `C:\Users\huang\AppData\Roaming\Python\Python313\Scripts\copaw.exe` |
| Python site-packages | `C:\Users\huang\AppData\Roaming\Python\Python313\site-packages` |
| 配置文件 | `C:\Users\huang\.copaw\config.json` |

## 当前版本

| 组件 | 版本 | 更新日期 |
|------|------|----------|
| CoPaw | 0.0.6.post1 | 2026-03-10 |
| Playwright MCP | 0.0.68 | 2026-03-10 |

## 服务配置

| 配置项 | 值 |
|--------|-----|
| 服务端口 | 1012 |
| 访问地址 | http://127.0.0.1:1012/ |
| Desktop Channel | 启用 |
| Console Channel | 启用 |

## 已启用的 MCP

| 名称 | 包 | 功能 |
|------|-----|------|
| playwright | `@playwright/mcp@latest` | 浏览器自动化 |

## 已启用的 Skills

- browser_visible
- cron
- dingtalk_channel
- docx
- file_reader
- himalaya
- news
- pdf
- pptx
- xlsx

## 开发脚本

项目 `scripts/` 目录下的开发脚本：

```powershell
# 在项目根目录运行
.\scripts\dev.ps1              # 完整流程：重装 + 重启
.\scripts\dev.ps1 -NoReinstall # 仅重启
.\scripts\restart.ps1          # 重启服务
.\scripts\stop.ps1             # 停止服务
.\scripts\reinstall.ps1        # 重新安装（含前端构建）
```

## 快速命令

```powershell
# 启动服务（后台）
powershell -Command "Start-Process -FilePath 'C:\Users\huang\AppData\Roaming\Python\Python313\Scripts\copaw.exe' -ArgumentList 'app','--port','1012' -WindowStyle Hidden"

# 停止服务
powershell -Command "Get-Process -Name copaw -ErrorAction SilentlyContinue | Stop-Process -Force"

# 检查服务状态
netstat -ano | findstr :1012

# 测试服务
curl http://127.0.0.1:1012/
```

---

## 升级记录

### 2026-03-10

**操作**：初始化安装

**变更内容**：
- 从源码安装 CoPaw 0.0.6.post1 (`pip install -e .`)
- 配置服务端口为 1012
- 添加 Playwright MCP (`@playwright/mcp@latest`)
- 创建开发脚本 (`scripts/dev.ps1`, `restart.ps1`, `stop.ps1`, `reinstall.ps1`)
- 合并 upstream/main（45 个新提交）
- 构建前端并复制到 `src/copaw/console/`

**注意事项**：
- 从源码安装需要手动构建前端：
  ```powershell
  cd console && npm ci && npm run build
  cp -r console/dist/* src/copaw/console/
  ```
- `src/copaw/console/` 目录被 `.gitignore` 忽略，是正常的

---

<!-- 模板：后续升级记录格式
### YYYY-MM-DD

**操作**：[描述操作，如：升级版本 / 添加功能 / 修复问题]

**变更内容**：
- 变更1
- 变更2

**注意事项**：
- 注意事项1
-->
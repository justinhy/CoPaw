# Scripts

Run from **repo root**.

## Build wheel (with latest console)

```bash
bash scripts/wheel_build.sh
```

- Builds the console frontend (`console/`), copies `console/dist` to `src/copaw/console/dist`, then builds the wheel. Output: `dist/*.whl`.

## Build website

```bash
bash scripts/website_build.sh
```

- Installs dependencies (pnpm or npm) and runs the Vite build. Output: `website/dist/`.

## Build Docker image

```bash
bash scripts/docker_build.sh [IMAGE_TAG] [EXTRA_ARGS...]
```

- Default tag: `copaw:latest`. Uses `deploy/Dockerfile` (multi-stage: builds console then Python app).
- Example: `bash scripts/docker_build.sh myreg/copaw:v1 --no-cache`.

## Development Scripts (Windows)

快速开发脚本，用于本地开发调试：

```powershell
# 完整流程：重装 + 重启
.\scripts\dev.ps1

# 仅重启（不重装）
.\scripts\dev.ps1 -NoReinstall

# 仅停止服务
.\scripts\stop.ps1

# 使用其他端口
.\scripts\dev.ps1 -Port 8080
```

| 脚本 | 功能 |
|------|------|
| `dev.ps1` | 完整开发流程 (重装+重启) |
| `reinstall.ps1` | 仅重新安装 `pip install -e .` |
| `restart.ps1` | 仅重启服务 |
| `stop.ps1` | 仅停止服务 |
| `copaw-dev.ps1` | 全局命令（复制到 PATH 使用） |

**参数**：`-Port`（默认1012）、`-NoReinstall`、`-Background`

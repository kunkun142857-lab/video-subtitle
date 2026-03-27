# Video Subtitle Remover macOS Packager

这个目录不是上游项目源码本体，而是一个专门给 [video-subtitle-remover](https://github.com/YaoFANGUK/video-subtitle-remover) 做 macOS `.app/.dmg` 安装包的构建器。

它解决了上游仓库目前缺的几件事：

- 自动拉取上游源码
- 在打包前预合并被切片的大模型，避免应用首次启动时再修改自己的包内容
- 用 `PyInstaller` 生成 macOS `.app`
- 用 `dmgbuild` 生成可分发的 `.dmg`
- 在 GitHub Actions 上一键出包
- 可选接入 Apple Developer 证书做签名/公证

## 你现在最该怎么用

如果你只是想尽快拿到一个能装到 Mac 上的包，优先走 GitHub Actions。
具体步骤我单独整理在 [GITHUB_SETUP.md](GITHUB_SETUP.md)。
如果你想看“网页上点哪里”的超细步骤，直接看 [PUSH_TO_GITHUB.md](PUSH_TO_GITHUB.md)。
如果你准备配置签名和公证，直接看 [SECRETS_CHECKLIST.md](SECRETS_CHECKLIST.md)。

## 产物形式

- `Video Subtitle Remover.app`
- `vsr-v<version>-macos-<arch>.dmg`

默认 GitHub Actions 使用 `macos-latest`，通常产出的是 `arm64` 包。
如果你是 Intel Mac，建议改成自有 Intel Mac 机器本地构建，或改成自托管 x86_64 runner。

## 最省事的用法

### 方案 A：GitHub Actions 出包

1. 把这个目录单独放进一个 GitHub 仓库。
2. 打开仓库的 `Actions`。
3. 手动运行 `Build macOS DMG`。
4. 去 `Artifacts` 或 `Release` 下载 `.dmg`。

不配置苹果开发者证书也能出包，但第一次打开大概率会遇到 Gatekeeper 安全提示。

### 方案 B：在你自己的 Mac 上本地出包

```bash
cd /path/to/video-subtitle-remover-macos-packager
chmod +x scripts/build_macos.sh
PYTHON_BIN=python3.12 ./scripts/build_macos.sh --ref main
```

构建完成后，产物会在 `release/` 目录里。

## 真正做到“更像傻瓜式安装”

如果你希望用户下载后尽量接近“双击就开”，需要补苹果签名和公证。

GitHub Actions 里预留了这些 secrets：

- `APPLE_CERTIFICATE_P12_BASE64`
- `APPLE_CERTIFICATE_PASSWORD`
- `APPLE_SIGNING_IDENTITY`
- `APPLE_ID`
- `APPLE_APP_SPECIFIC_PASSWORD`
- `APPLE_TEAM_ID`

说明：

- 只有证书，没有公证账号：可以做签名，但仍可能有安全提示。
- 证书和公证都齐全：最接近真正的一键安装体验。

## 文件说明

- `requirements-macos.txt`: macOS 运行时依赖
- `requirements-build.txt`: 打包工具依赖
- `scripts/build_macos.sh`: 本地一键构建入口
- `scripts/build_macos.py`: 拉取上游、预处理模型、打包 `.app/.dmg`
- `build/macos/VideoSubtitleRemover.spec`: PyInstaller 规格文件
- `build/macos/dmg_settings.py`: DMG 布局配置
- `.github/workflows/build-macos.yml`: GitHub Actions 流水线
- `GITHUB_SETUP.md`: GitHub 仓库和 Secrets 配置说明
- `PUSH_TO_GITHUB.md`: 网页上传版和 Git 命令版发布步骤
- `SECRETS_CHECKLIST.md`: GitHub Actions secrets 填写清单

## 已知限制

- 上游项目当前没有官方 macOS 发布包，这套方案属于补全交付链路，不是上游原生提供。
- 上游依赖比较重，首次打包时间会比较长。
- 我这里没有真实 macOS 机器做实机运行验证，所以这套链路已经尽量规避已知坑，但第一次在你的 Mac 上跑时仍建议先试一轮。

# GitHub Actions 配置说明

如果你只想尽快拿到一个 macOS 安装包，最简单就是把这个目录推到 GitHub，然后直接跑 Actions。

## 最简流程

1. 新建一个 GitHub 仓库。
2. 把这个目录里的文件全部推上去。
3. 进入 `Actions`。
4. 运行 `Build macOS DMG`。
5. 在 `Artifacts` 或 `Releases` 下载 `.dmg`。

## 不配置任何 Secrets 会怎样

可以正常构建出：

- `.app`
- `.dmg`

但这是“未签名/未公证”的安装包。
在 macOS 上第一次打开时，系统大概率会拦一下，需要手动放行。

## 想更接近真正的双击安装，需要哪些 Secrets

### 只做签名

需要：

- `APPLE_CERTIFICATE_P12_BASE64`
- `APPLE_CERTIFICATE_PASSWORD`
- `APPLE_SIGNING_IDENTITY`

效果：

- 应用会被签名
- 比完全未签名更好
- 但如果没有公证，仍可能被 Gatekeeper 提示

### 签名 + 公证

再额外加上：

- `APPLE_ID`
- `APPLE_APP_SPECIFIC_PASSWORD`
- `APPLE_TEAM_ID`

效果：

- 这是最接近“普通用户双击就装”的方式
- GitHub Actions 会在构建后自动提交 notarization，并给 DMG staple

## Secrets 含义

- `APPLE_CERTIFICATE_P12_BASE64`
  把你的开发者证书 `.p12` 文件做 base64 编码后的内容

- `APPLE_CERTIFICATE_PASSWORD`
  导出 `.p12` 时设置的密码

- `APPLE_SIGNING_IDENTITY`
  一般类似：
  `Developer ID Application: Your Name (TEAMID)`

- `APPLE_ID`
  你的 Apple 开发者账号邮箱

- `APPLE_APP_SPECIFIC_PASSWORD`
  Apple ID 的 app-specific password

- `APPLE_TEAM_ID`
  Apple Developer Team ID

## `.p12` 转 Base64 的常用方式

在 Mac 里执行：

```bash
base64 -i your-cert.p12 | pbcopy
```

然后把剪贴板内容填到 `APPLE_CERTIFICATE_P12_BASE64`。

## 一句话建议

- 只是自己用：不配 secrets 也能出包
- 想发给别人：至少做签名
- 想尽量傻瓜式：签名 + 公证

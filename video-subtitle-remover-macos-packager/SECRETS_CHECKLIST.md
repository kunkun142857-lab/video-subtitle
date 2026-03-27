# GitHub Secrets 填写清单

如果你准备做“更像正常安装包”的版本，就按这张表填。

## 先说结论

- 自己先测试：可以一个 secret 都不填
- 想减少安全提示：至少填签名相关
- 想尽量傻瓜式双击安装：把签名和公证都填全

## 进入位置

在 GitHub 仓库里打开：

`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

## 第一组：签名必填

### `APPLE_CERTIFICATE_P12_BASE64`

内容：

- 你的 Apple Developer 证书 `.p12` 文件转成 base64 之后的文本

### `APPLE_CERTIFICATE_PASSWORD`

内容：

- 导出 `.p12` 证书时设置的密码

### `APPLE_SIGNING_IDENTITY`

内容示例：

```text
Developer ID Application: Your Name (TEAMID)
```

## 第二组：公证必填

### `APPLE_ID`

内容：

- 你的 Apple 开发者账号邮箱

### `APPLE_APP_SPECIFIC_PASSWORD`

内容：

- Apple ID 专用的 app-specific password

### `APPLE_TEAM_ID`

内容：

- Apple Developer Team ID

## `.p12` 怎么转 base64

在 Mac 终端执行：

```bash
base64 -i your-cert.p12 | pbcopy
```

执行后，剪贴板里的内容就是 `APPLE_CERTIFICATE_P12_BASE64` 要填的值。

## 不确定有没有填对时怎么看

如果 secrets 配好了，工作流运行时通常会出现这些行为：

- 先导入证书
- 然后 `codesign`
- 最后如果公证信息完整，会跑 `notarytool`

如果没有这些步骤，通常就是 secrets 没配全，或者名字写错了。

## 最常见错误

- `.p12` 不是 base64 文本，直接把文件内容乱贴进去
- `APPLE_SIGNING_IDENTITY` 名字和证书真实 identity 不一致
- `APPLE_APP_SPECIFIC_PASSWORD` 填成 Apple 登录密码
- `APPLE_TEAM_ID` 写错

## 一句话版本

- 能出包不等于能顺利双击安装
- 真正想让别人装得省心，签名和公证最好都做

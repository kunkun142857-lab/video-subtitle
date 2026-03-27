# 推到 GitHub 的最短步骤

这份说明按“最省脑子”的方式写。
你可以直接照着做，不需要懂太多 Git。

## 方案 1：完全不用 Git 命令，网页上传

这是最适合第一次操作 GitHub 的方式。

### 第一步：新建仓库

1. 打开 GitHub。
2. 点击右上角 `+`。
3. 选择 `New repository`。
4. Repository name 建议填：
   `video-subtitle-remover-macos-packager`
5. 选择 `Public` 或 `Private` 都可以。
6. 不要勾选：
   - `Add a README file`
   - `Add .gitignore`
   - `Choose a license`
7. 点击 `Create repository`。

### 第二步：上传文件

1. 进入你刚创建的空仓库页面。
2. 点击 `uploading an existing file`。
3. 把这个目录里的全部文件拖进去：
   [video-subtitle-remover-macos-packager](/C:/Users/Administrator/Desktop/demo/video-subtitle-remover-macos-packager)
4. 页面下方 commit message 可以填：
   `Initial macOS packager`
5. 点击 `Commit changes`。

### 第三步：跑构建

1. 进入仓库上方的 `Actions`。
2. 找到 `Build macOS DMG`。
3. 点击 `Run workflow`。
4. `upstream_ref` 默认填 `main` 就行。
5. 点击绿色按钮运行。

### 第四步：下载成品

构建成功后有两个常见下载位置：

- `Actions` 页面里的 `Artifacts`
- 仓库右侧的 `Releases`

你最终要拿的是 `.dmg` 文件。

## 方案 2：用 Git 命令推上去

如果你电脑里已经装了 Git，也可以用命令。

```powershell
cd C:\Users\Administrator\Desktop\demo\video-subtitle-remover-macos-packager
git init
git add .
git commit -m "Initial macOS packager"
git branch -M main
git remote add origin https://github.com/<你的用户名>/video-subtitle-remover-macos-packager.git
git push -u origin main
```

然后再去 GitHub 的 `Actions` 页面运行 `Build macOS DMG`。

## 不想配签名也能用吗

可以。

如果你只是自己在 Mac 上用，或者先想验证能不能打出包，不配 Apple secrets 也能正常产出 `.dmg`。

区别只是：

- 不签名不公证：第一次打开时更容易被 macOS 拦截
- 签名但不公证：体验会更好一点
- 签名并公证：最接近正常双击安装

## 我建议你现在怎么做

最顺的路线就是：

1. 用网页上传法把仓库先建起来
2. 先不配 secrets，先跑一次构建
3. 确认能出 `.dmg`
4. 如果你要发给别人，再补签名和公证

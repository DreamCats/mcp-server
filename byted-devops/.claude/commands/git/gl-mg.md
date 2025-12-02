---
description: 先同步当前分支远端更新并推送本地提交，再拉取并合并主分支（main/master），冲突时立即暂停等待用户解决
description-hint: 无参数
---

# gl-mg

在本地当前分支上，一键完成“双向同步”后再合并主分支：
1. 拉取并合并当前分支对应的远端分支，确保获取他人最新提交；
2. 若本地有未推送提交，自动 push 回远端；
3. 拉取远端主分支（自动识别 main 或 master）并合并到当前分支。

**一旦检测到冲突，命令立即暂停，提示用户手动选择保留的代码，解决后继续。**

## 使用方法:

`/gl-mg`

## 执行流程:

1. 获取当前分支名 `<current>`
2. 若存在远端分支 `origin/<current>`，则：
   - `git fetch origin <current>`
   - `git merge origin/<current> --no-edit`
   **若合并产生冲突 → 中止并提示用户手动解决，待解决后用户重新运行命令**
3. 若本地存在未推送的提交，则：
   - `git push origin <current>`
4. 获取远端默认仓库名（通常为 origin）
5. 查询远端引用列表，判断存在 `origin/main` 还是 `origin/master`
6. 若两者都不存在，报错并终止
7. 若存在唯一主分支，则执行：
   - `git fetch origin <主分支名>`
   - `git merge origin/<主分支名> --no-edit`
   **若合并产生冲突 → 中止并提示用户手动解决，待解决后用户重新运行命令**
8. 输出最终状态摘要

## 示例:

- 日常同步共享开发分支与主分支
  `/git:gl-mg`
  输出示例（无冲突）：
📥 拉取远端分支 origin/fix-header... ✅
🚀 检测到 2 个本地提交未推送，正在 push... ✅
🔍 检测到远端主分支：origin/main
📥 拉取并合并 origin/main 到当前分支... ✅
🎉 双向同步 + 主分支合并完成，当前分支已是最新。


输出示例（冲突）：

📥 拉取远端分支 origin/fix-header...
⚠️ 合并冲突！请手动解决以下冲突文件： src/header.js src/utils.js 解决后执行：git add . && git commit -m "resolve conflict"
然后重新运行 /git:gl-mg


## 注意事项:

- 当前分支若未关联远端分支，步骤 2 会跳过并提示
- 若本地存在未提交更改，请先 stash 或 commit，避免合并冲突
- **冲突发生时，命令会立即中止，必须用户手动选择冲突内容、完成合并提交后，再次运行本命令继续后续流程**
- 本命令默认使用 `merge` 策略；如需 rebase，请改用相应命令
- 自动 push 前会先做快进检测，非快进推送需加 `--force` 时请手动处理

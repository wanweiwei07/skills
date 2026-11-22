# Claude Skills

A collection of [Claude Code](https://claude.com/claude-code) skills for our lab.
本仓库收集实验室使用的 Claude Code skill。

| Skill | 说明 / Description |
|---|---|
| [doc-maker](doc-maker/) | 制作 PPT、论文等文档：用 [one](https://github.com/wanweiwei07/one) 渲染图片和视频，自动建文件夹，在 VS Code 里随时查看。 Make slides / papers with figures and videos rendered by `one`. |

## 安装 / Install

把整个仓库 clone 成你的个人 skills 文件夹（Windows PowerShell）：

```powershell
git clone https://github.com/wanweiwei07/skills "$env:USERPROFILE\.claude\skills"
```

如果 `%USERPROFILE%\.claude\skills` 已经存在、里面有你自己的 skill，就 clone 到别处，再把需要的子文件夹（如 `doc-maker`）复制进 `%USERPROFILE%\.claude\skills\`。

If `~/.claude/skills` already exists, clone elsewhere and copy the skill folders you want into it.

更新 / Update:

```powershell
git -C "$env:USERPROFILE\.claude\skills" pull
```

安装后重新打开 Claude Code，在任意文件夹下直接提要求即可，例如：

- 「帮我做一个关于 bunny 抓取规划的 PPT」
- 「用 one 录一段机械臂运动的视频，做成组会幻灯片」
- 「写一篇关于这个实验的论文初稿」

## doc-maker 需要的环境 / Requirements

- Python ≥ 3.12，并安装 `one`
- VS Code（推荐扩展：LaTeX Workshop、vscode-pdf）
- Microsoft PowerPoint（导出 PDF 用）
- 写论文时需要 LaTeX（MiKTeX 或 TeX Live）

缺什么 Claude 会先检查并提示，征得你同意后帮你安装（PowerPoint 需自行安装）。

<div align="center">

# Claude Skills

[English](README.md) · [日本語](README.ja.md) · **中文**

</div>

本仓库收集实验室使用的 [Claude Code](https://claude.com/claude-code) skill。skill 是一个
装有说明和脚本的文件夹，用来教 Claude 按固定流程工作；安装后，只要你的要求和它对得上，
Claude 就会自动使用。

| Skill | 功能 |
|---|---|
| [doc-maker](doc-maker/) | 制作幻灯片（PowerPoint + PDF）和论文（LaTeX）。图片和视频用机器人库 [one](https://github.com/wanweiwei07/one) 渲染，所有东西放进一个带日期的文件夹，在 VS Code 里随时查看结果。 |

## 1. 安装

Claude Code 会从你的 **用户主文件夹**（属于你这个用户账号的文件夹）里的
`.claude/skills` 文件夹读取个人 skill：

| 系统 | 用户主文件夹 | skills 文件夹 |
|---|---|---|
| Windows | `C:\Users\<你的用户名>` | `C:\Users\<你的用户名>\.claude\skills` |
| Linux（Ubuntu） | `/home/<你的用户名>`（简写为 `~`） | `/home/<你的用户名>/.claude/skills` |
| macOS | `/Users/<你的用户名>`（简写为 `~`） | `/Users/<你的用户名>/.claude/skills` |

`.claude` 和 `skills` 文件夹可能还不存在，没关系，下面的命令会自动建好。

### Windows

1. 打开 **PowerShell**（开始菜单里输入 `PowerShell`）。
2. 粘贴并运行：

   ```powershell
   git clone https://github.com/wanweiwei07/skills "$env:USERPROFILE\.claude\skills"
   ```

   `$env:USERPROFILE` 是 Windows 自带的变量，每台电脑都有，永远指向你的用户主文件夹，
   例如 `C:\Users\taro`。运行 `echo $env:USERPROFILE` 可以看到你自己的。
3. 检查：运行 `dir "$env:USERPROFILE\.claude\skills\doc-maker"`，能看到 `SKILL.md` 就装好了。
   （也可以在资源管理器的地址栏输入 `%USERPROFILE%\.claude\skills` 打开。）

### Linux（Ubuntu）/ macOS

1. 打开 **终端**（Ubuntu：`Ctrl+Alt+T`）。
2. 粘贴并运行：

   ```bash
   git clone https://github.com/wanweiwei07/skills ~/.claude/skills
   ```

   `~` 就是你的用户主文件夹，例如 `/home/taro`。运行 `echo ~` 可以看到你自己的。
3. 检查：运行 `ls ~/.claude/skills/doc-maker`，能看到 `SKILL.md` 就装好了。
   `.claude` 以点开头，是 **隐藏文件夹**：用 `ls -a ~` 查看，或在 Ubuntu 文件管理器里按
   `Ctrl+H` 显示。

没有 `git`？Windows：`winget install Git.Git`；Ubuntu：`sudo apt install git`。
也可以在 GitHub 页面点 **Code → Download ZIP**，解压后把 `doc-maker` 文件夹复制到上表的
skills 文件夹里（文件夹不存在就自己建）。

**已经有 `skills` 文件夹**、里面有你自己的 skill？那 `git clone` 会失败。请 clone 到别处，
再只把 `doc-maker` 文件夹复制进你的 skills 文件夹。

**更新**：

```powershell
git -C "$env:USERPROFILE\.claude\skills" pull      # Windows
```

```bash
git -C ~/.claude/skills pull                       # Linux / macOS
```

安装或更新后请重启 Claude Code。

## 2. 使用

在想放文档的文件夹里打开终端（或者用 VS Code 打开这个文件夹，再启动 Claude Code），
直接提要求即可，例如：

- 「做一份关于 bunny 抓取规划的 PPT，加一段机器人的视频」
- 「从正面和顶部各渲染一张机器人的图，放在同一页幻灯片里」
- 「写一篇这个实验的论文初稿，图用 one 来做」

Claude 会在当前文件夹下建 `YYYYMMDD_<名字>/`（没给名字就是 `YYYYMMDD_document`）：

```
20261122_grasp_planning/
├── scripts/   生成每张图、每段视频的 one 程序（重新运行即可重新生成）
├── imgs/      截图（不弹窗口渲染，自动取景，让目标物体尽量大）
├── videos/    动画（.mp4）以及每段视频的封面图
├── slides/    <名字>.pptx 和导出的 <名字>.pdf
└── tex/       main.tex（论文源文件）和 main.pdf
```

PDF 可以一直在 VS Code 里开着：幻灯片每次修改后会重新导出，LaTeX 的 PDF 在每次保存
`main.tex` 时自动重新编译。

### 统一样式

所有文档都遵守同一套规则，实验室的幻灯片看起来风格一致：

- 幻灯片文字：封面大标题 **44 pt**，每页标题 **32 pt**，正文 **24 pt**，次要文字（子项、图下标注、图注）**20 pt**
- 图里的文字（曲线图、示意图）：**18 pt**
- 线宽统一 **1.5 pt**（曲线、坐标轴、箭头）
- 实验室 logo 只放在封面，标题上方；想换成自己的，替换 `doc-maker/assets/logo.png`（透明背景 PNG）
- 公式一律用 **LaTeX** 排版，幻灯片里也一样（不用 PowerPoint 自带的公式编辑器）
- 图按 16:9 幻灯片的 **半页** 尺寸做，半页放不下就按 **整页** 尺寸做
- 视频默认 **1280×720（720p，16:9）**；不合适时 Claude 会先问你

## 3. 环境要求

开始时 Claude 会先运行检查脚本（`doc-maker/scripts/check_env.py`）。缺什么它会给出安装命令，
并且 **安装前一定先征求你的同意**。你也可以自己装：

| 用途 | Windows | Linux（Ubuntu） | macOS |
|---|---|---|---|
| Python ≥ 3.12 | python.org 或 `winget install Python.Python.3.12` | `sudo apt install python3.12 python3.12-venv` | `brew install python@3.12` |
| one | 见下文 | 见下文 | 见下文 |
| VS Code | `winget install Microsoft.VisualStudioCode` | `sudo snap install code --classic` | `brew install --cask visual-studio-code` |
| Python 包 | `pip install python-pptx pillow imageio imageio-ffmpeg pymupdf matplotlib pywin32` | `pip install python-pptx pillow imageio imageio-ffmpeg pymupdf matplotlib` | 同 Linux |
| 幻灯片 → PDF | **Microsoft PowerPoint**（需自行安装），或 LibreOffice：`winget install TheDocumentFoundation.LibreOffice` | **LibreOffice**：`sudo apt install libreoffice-impress` | LibreOffice：`brew install --cask libreoffice` |
| LaTeX（论文和幻灯片公式） | MiKTeX `winget install MiKTeX.MiKTeX` 或 TeX Live | `sudo apt install texlive-xetex texlive-lang-cjk latexmk` | `brew install --cask mactex-no-gui` |
| VS Code 扩展 | `code --install-extension james-yu.latex-workshop` 和 `code --install-extension tomoki1207.pdf` | 同左 | 同左 |

说明：

- **Linux 上的 Office**：请用 LibreOffice。WPS 虽然能打开 .pptx，但不能被脚本调用，
  没法自动导出 PDF。
- **没有桌面的 Linux（SSH、服务器）**：渲染需要 OpenGL 显示环境。装上 `xvfb`
  （`sudo apt install xvfb`）后，Claude 会用 `xvfb-run` 运行出图脚本。
- PowerPoint 只能你自己装，其他的东西经你同意后 Claude 都可以帮你装。

### 手动安装 one

```bash
git clone https://github.com/wanweiwei07/one.git
cd one
python -m venv venv                # 可选，推荐
venv\Scripts\activate              # Windows（Linux/macOS：source venv/bin/activate）
pip install -e .
```

和 Claude 一起工作时请使用同一个 Python（或 venv），保证 `import one` 能成功。
检查方法：`python -c "import one; print(one.__file__)"`。

## 4. 常见问题

| 问题 | 解决办法 |
|---|---|
| Claude 没有用这个 skill | 确认 `SKILL.md` 在 `<skills 文件夹>/doc-maker/SKILL.md`（没有多套一层文件夹），然后重启 Claude Code。也可以直接说“用 doc-maker skill”。 |
| `import one` 失败 | 激活装了 one 的 venv，或告诉 Claude 该用哪个 Python。 |
| 导出 PDF 失败 | 先关掉在 PowerPoint / LibreOffice 里打开的这份幻灯片，再让 Claude 重试。 |
| Linux 上图片是黑的或空白 | 更新显卡驱动，或用 `xvfb-run` 运行。 |

## 添加新的 skill（维护者）

在 `doc-maker/` 旁边新建一个文件夹并放入 `SKILL.md`，在三份 README 开头的表格里加上它，
然后 commit、push。学生 `git pull` 就能拿到。

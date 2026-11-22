<div align="center">

# Claude Skills

[English](README.md) · **日本語** · [中文](README.zh.md)

</div>

研究室で使う [Claude Code](https://claude.com/claude-code) 用のスキル集です。スキルとは、
Claude に作業手順を教える説明書とスクリプトのフォルダです。インストールしておくと、
依頼内容に合うときに Claude が自動で使います。

| スキル | 内容 |
|---|---|
| [doc-maker](doc-maker/) | スライド（PowerPoint + PDF）と論文（LaTeX）を作成します。図と動画はロボットライブラリ [one](https://github.com/wanweiwei07/one) でレンダリングし、すべてを日付付きの 1 つのフォルダにまとめ、VS Code で結果を随時確認できます。 |

## 1. インストール

Claude Code は、**ホームフォルダ**（自分のユーザーアカウントのフォルダ）の中にある
`.claude/skills` フォルダから個人スキルを読み込みます：

| OS | ホームフォルダ | スキルフォルダ |
|---|---|---|
| Windows | `C:\Users\<ユーザー名>` | `C:\Users\<ユーザー名>\.claude\skills` |
| Linux（Ubuntu） | `/home/<ユーザー名>`（`~` と書く） | `/home/<ユーザー名>/.claude/skills` |
| macOS | `/Users/<ユーザー名>`（`~` と書く） | `/Users/<ユーザー名>/.claude/skills` |

`.claude` や `skills` フォルダはまだ無いかもしれませんが、問題ありません。下のコマンドで自動的に作られます。

### Windows

1. **PowerShell** を開く（スタートメニューで `PowerShell` と入力）。
2. 次を貼り付けて実行：

   ```powershell
   git clone https://github.com/wanweiwei07/skills "$env:USERPROFILE\.claude\skills"
   ```

   `$env:USERPROFILE` は Windows に最初からある変数で、常に自分のホームフォルダ
   （例：`C:\Users\taro`）を指します。`echo $env:USERPROFILE` で確認できます。
3. 確認：`dir "$env:USERPROFILE\.claude\skills\doc-maker"` で `SKILL.md` が表示されれば OK。
   （エクスプローラーならアドレスバーに `%USERPROFILE%\.claude\skills` と入力。）

### Linux（Ubuntu）/ macOS

1. **端末（ターミナル）** を開く（Ubuntu：`Ctrl+Alt+T`）。
2. 次を貼り付けて実行：

   ```bash
   git clone https://github.com/wanweiwei07/skills ~/.claude/skills
   ```

   `~` はホームフォルダ（例：`/home/taro`）のことです。`echo ~` で確認できます。
3. 確認：`ls ~/.claude/skills/doc-maker` で `SKILL.md` が表示されれば OK。
   `.claude` はドットで始まるため **隠しフォルダ** です。`ls -a ~` を使うか、
   Ubuntu のファイルマネージャーで `Ctrl+H` を押すと表示されます。

`git` がない場合：Windows は `winget install Git.Git`、Ubuntu は `sudo apt install git`。
または GitHub の **Code → Download ZIP** でダウンロード・解凍し、`doc-maker` フォルダを
上の表のスキルフォルダにコピーします（フォルダがなければ作成）。

**すでに `skills` フォルダがあり**、自分のスキルが入っている場合は `git clone` が失敗します。
別の場所に clone して、`doc-maker` フォルダだけをスキルフォルダにコピーしてください。

**更新**：

```powershell
git -C "$env:USERPROFILE\.claude\skills" pull      # Windows
```

```bash
git -C ~/.claude/skills pull                       # Linux / macOS
```

インストール・更新後は Claude Code を再起動してください。

## 2. 使い方

文書を作りたいフォルダでターミナルを開く（または VS Code でそのフォルダを開いて
Claude Code を起動する）だけで、あとは普通に依頼します。例：

- 「bunny の把持計画についてのスライドを作って。ロボットの動画も入れて」
- 「ロボットを正面と真上から描画して、1 枚のスライドに並べて」
- 「この実験の論文の下書きを書いて。図は one で作って」

Claude はカレントフォルダに `YYYYMMDD_<名前>/` を作ります（名前がなければ `YYYYMMDD_document`）：

```
20261122_grasp_planning/
├── scripts/   各図・動画を生成する one のプログラム（再実行で作り直せる）
├── imgs/      スクリーンショット（ウィンドウを出さずに描画し、対象が大きく写るよう自動フレーミング）
├── videos/    アニメーション（.mp4）と各動画のポスター画像
├── slides/    <名前>.pptx と書き出した <名前>.pdf
└── tex/       main.tex（論文ソース）と main.pdf
```

PDF は VS Code で開いたままにしておけます。スライドは変更のたびに書き出し直され、
LaTeX の PDF は `main.tex` を保存するたびに再ビルドされます。

## 3. 必要な環境

最初に Claude がチェック（`doc-maker/scripts/check_env.py`）を実行します。足りないものが
あればインストールコマンドを示し、**インストールする前に必ず確認します**。自分でインストールしても構いません：

| 用途 | Windows | Linux（Ubuntu） | macOS |
|---|---|---|---|
| Python ≥ 3.12 | python.org または `winget install Python.Python.3.12` | `sudo apt install python3.12 python3.12-venv` | `brew install python@3.12` |
| one | 下記参照 | 下記参照 | 下記参照 |
| VS Code | `winget install Microsoft.VisualStudioCode` | `sudo snap install code --classic` | `brew install --cask visual-studio-code` |
| Python パッケージ | `pip install python-pptx pillow imageio imageio-ffmpeg pywin32` | `pip install python-pptx pillow imageio imageio-ffmpeg` | Linux と同じ |
| スライド → PDF | **Microsoft PowerPoint**（各自でインストール）または LibreOffice：`winget install TheDocumentFoundation.LibreOffice` | **LibreOffice**：`sudo apt install libreoffice-impress` | LibreOffice：`brew install --cask libreoffice` |
| 論文（LaTeX） | MiKTeX `winget install MiKTeX.MiKTeX` または TeX Live | `sudo apt install texlive-xetex texlive-lang-cjk latexmk` | `brew install --cask mactex-no-gui` |
| VS Code 拡張機能 | `code --install-extension james-yu.latex-workshop` と `code --install-extension tomoki1207.pdf` | 同じ | 同じ |

補足：

- **Linux の Office**：LibreOffice を使ってください。WPS でも .pptx は開けますが、
  スクリプトから操作できないため、PDF を自動で書き出せません。
- **デスクトップのない Linux（SSH・サーバー）**：描画には OpenGL のディスプレイが必要です。
  `xvfb` をインストール（`sudo apt install xvfb`）すると、Claude が `xvfb-run` で図のスクリプトを実行します。
- PowerPoint は Claude がインストールできません。それ以外はあなたの許可があればインストールできます。

### one を手動でインストールする

```bash
git clone https://github.com/wanweiwei07/one.git
cd one
python -m venv venv                # 任意（推奨）
venv\Scripts\activate              # Windows（Linux/macOS：source venv/bin/activate）
pip install -e .
```

Claude と作業するときも同じ Python（または venv）を使い、`import one` が通るようにしてください。
確認：`python -c "import one; print(one.__file__)"`。

## 4. トラブルシューティング

| 問題 | 対処 |
|---|---|
| Claude がスキルを使わない | `SKILL.md` が `<スキルフォルダ>/doc-maker/SKILL.md` にあるか（1 階層深くなっていないか）確認し、Claude Code を再起動。「doc-maker スキルを使って」と頼んでも OK。 |
| `import one` が失敗する | one をインストールした venv を有効化するか、使う Python を Claude に伝える。 |
| PDF の書き出しに失敗する | PowerPoint / LibreOffice で開いているスライドを閉じて、もう一度依頼する。 |
| Linux で画像が黒い・空になる | GPU ドライバを更新するか、`xvfb-run` で実行する。 |

## 新しいスキルの追加（管理者向け）

`doc-maker/` と同じ階層に新しいフォルダを作って `SKILL.md` を置き、3 つの README の
先頭の表に追加して commit・push します。学生は `git pull` で入手できます。

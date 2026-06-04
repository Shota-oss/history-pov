# history-pov

歴史系の縦型ショート動画（TikTok / Instagram Reels / YouTube Shorts、9:16）を
**自動生成**するパイプラインです。台本 → ナレーション音声 → 歴史画像 → 字幕 → 動画
までを一気通貫で書き出します。

無料・APIキー不要のスタックを既定にしています：

| 工程 | 既定の手段 | キー |
|------|-----------|------|
| ナレーション音声 | Edge TTS（高品質な日本語音声） | 不要 |
| 画像 | Wikimedia Commons（自由ライセンスの歴史画像） | 不要 |
| 音声・字幕タイミング | Edge TTS の WordBoundary で自動同期 | 不要 |
| 動画合成 | MoviePy + 同梱 ffmpeg（Ken Burns ＋ 字幕焼き込み） | 不要 |
| 台本生成（任意） | Anthropic / OpenAI | 任意 |

## セットアップ

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp config.example.yaml config.yaml   # 必要なら編集
```

日本語字幕には日本語フォントが必要です。多くの環境では自動検出されますが、
無ければ `config.yaml` の `font` にフォントパスを指定してください
（例：Noto Sans CJK JP）。

## 使い方

### 1. 用意した台本から作る（キー不要・推奨の入口）

```bash
python make_video.py --script scripts/sample_sengoku.json
# -> output/本能寺の変・天下統一の夢.mp4
```

台本は JSON です（`scripts/sample_sengoku.json` を参照）：

```json
{
  "title": "タイトル",
  "topic": "テーマ",
  "scenes": [
    {
      "narration": "読み上げる文",
      "caption": "画面に出す短い文（省略時は narration）",
      "image_query": "English search term for Wikimedia Commons",
      "image": "（任意）ローカル画像パス。指定すると検索より優先"
    }
  ]
}
```

### 2. テーマ一行から自動生成する（LLM が必要）

`config.yaml` で `llm_provider` を `anthropic` か `openai` にし、
対応するキーを環境変数（または `.env`）に設定：

```bash
export ANTHROPIC_API_KEY=...     # または OPENAI_API_KEY=...
python make_video.py --topic "本能寺の変" --scenes 6
```

生成された台本は `output/<title>.json` に保存されるので、手直しして再利用できます。

### 3. オフライン・デモ（ネットもキーも不要）

合成エンジンの動作確認用。生成グラデーション背景＋合成音で実際に mp4 を書き出します
（ネットワーク制限のある CI / クラウド環境でも動きます）。

```bash
python make_demo.py --script scripts/sample_sengoku.json
# -> output/demo.mp4
```

## 声を変える

```bash
python make_video.py --script scripts/sample_sengoku.json --voice ja-JP-KeitaNeural
edge-tts --list-voices | grep ja-JP   # 利用可能な日本語音声一覧
```

## 構成

```
make_video.py        CLI（--script / --topic）
make_demo.py         オフライン・デモ
pipeline/
  config.py          設定（config.yaml / .env を読み込み）
  models.py          Script / Scene データモデル
  script_gen.py      LLM で台本生成（Anthropic / OpenAI）
  tts.py             Edge TTS で音声＋字幕タイミング
  images.py          Wikimedia Commons 画像取得（失敗時はグラデーション）
  render.py          MoviePy で 9:16 合成（Ken Burns＋字幕）
  runner.py          全工程のオーケストレーション
scripts/             サンプル台本
docs/                公開用ページ（TikTok/YouTube 連携ランディング）
```

## ネットワークについて

`make_video.py` は実行時に Edge TTS サーバと Wikimedia Commons へアクセスします。
外向き通信が制限された環境では、画像は自動でグラデーションにフォールバックし、
音声は取得できません。完成動画はネットワークの開いた環境（ローカル等）で実行してください。

## 画像の権利について

Wikimedia Commons の素材はファイルごとにライセンスが異なります。公開・収益化の前に、
各素材のライセンスと帰属表示（クレジット）要件を必ず確認してください。

## 補足

- 動画は `output/` に書き出されます（`.gitignore` 済み）。
- `config.yaml` と各種トークンも `.gitignore` 済みです。コミットしないでください。

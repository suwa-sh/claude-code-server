# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリでコードを作業する際のガイダンスを提供します。

## ルール

- 日本語で会話してください。
- 新しい施策を試す前に、思考プロセスをユーザーに説明してください。

### テストコードのルール

テストコードは以下のルールに従って作成してください：

#### 1. テストメソッド命名規則
テストメソッド名は以下の形式で命名してください：
```
test_{対象機能}_{テスト条件}_と_期待結果であること
```

**例：**
```python
def test_models_endpoint_GETリクエストを送信した場合_claude_sonnet_4だけが返されること(self, server_process):
def test_chat_completion_正常なチャットリクエストを送信した場合_回答が得られること(self, server_process, client):
def test_chat_completion_チャットリクエストで無効なAPIキーでリクエストを送信した場合_例外が発生すること(self, server_process):
```

#### 2. AAAパターンの実装
すべてのテストメソッドは以下の3つのセクションに明確に分割してください：

```python
def test_example_テスト条件_期待結果であること(self, fixtures):
    #------------------------------
    # 準備 (Arrange)
    #------------------------------
    # テストデータの設定、モックの準備など
    
    #------------------------------
    # 実行 (Act)
    #------------------------------
    # テスト対象の機能を実行
    
    #------------------------------
    # 検証 (Assert)
    #------------------------------
    # 結果の検証とアサーション
```

#### 3. テストメソッドの構造化
- **準備 (Arrange)**: テストに必要なデータ、オブジェクト、モックを設定
- **実行 (Act)**: テスト対象の機能を実行（1つの操作に集中）
- **検証 (Assert)**: 期待される結果と実際の結果を比較・検証

#### 4. テストケースの焦点化
- 各テストメソッドは1つの具体的なシナリオに集中する
- 複雑な並行処理や複数の条件を組み合わせたテストは避ける
- 基本的な動作確認を重視し、エッジケースは別のテストで扱う

#### 5. BDDスタイルの採用
テスト名と内容は「〜の場合、〜であること」という形式で、ビジネス要件を明確に表現してください。

## プロジェクト概要

これは、claude-code CLIをラップしてClaude AIの機能を標準APIインターフェース経由で提供する、OpenAI API互換サーバーです。LiteLLMをプロキシサーバーとして使用してOpenAI互換のリクエストを処理し、claude-code CLIに転送します。

## アーキテクチャ

システムは2つの主要コンポーネントで構成されています：

1. **LiteLLM Proxy** (`litellm_config.yaml`): ポート4000でOpenAI互換APIリクエストを処理
2. **Custom Provider** (`claude_code_server/provider.py`): claude-code CLIコマンドを実行するCustomLLMクラス

フロー: OpenAI APIリクエスト → LiteLLM → ClaudeCodeProvider → claude-code CLI → レスポンス

### 主要な実装詳細
- **CustomLLM継承**: `ClaudeCodeProvider`はLiteLLMの`CustomLLM`基底クラスを拡張
- **非同期サポート**: `completion()`と`acompletion()`メソッドの両方を実装
- **プロバイダー登録**: `litellm_config.yaml`の`custom_provider_map`で登録
- **モデルマッピング**: `claude-sonnet-4` → `claude-code-server/claude-code`

## 一般的な開発コマンド

### 環境セットアップ
```bash
# Ryeでプロジェクトを初期化
make init

# 依存関係をインストール/同期
make sync
```

### サーバー起動
```bash
# LiteLLMプロキシサーバーを起動（推奨）
make run

# または直接実行
rye run litellm --config litellm_config.yaml --port 4001
```

### テスト
```bash
# プロバイダーユニットテストを実行（高速）
make test

# 統合テストを含む全テストを実行（低速）
make test-all

# 統合テストのみ実行（時間がかかります）
make test-integration

# カバレッジレポートを生成
make coverage
```

### コード品質
```bash
# リンティングを実行（flake8 + mypy）
make lint

# コードをフォーマット（black + isort）
make format
```

### Docker
```bash
# Dockerイメージをビルド
make docker-build

# Dockerコンテナを実行
make docker-run
```

## 主要な設定

### LiteLLM設定 (`litellm_config.yaml`)
```yaml
model_list:
  - model_name: claude-sonnet-4            # クライアント向けモデル名
    litellm_params:
      model: claude-code-server/claude-code  # 内部プロバイダーモデル

litellm_settings:
  custom_provider_map:
    - provider: "claude-code-server"
      custom_handler: "claude_code_server.provider.claude_code_provider_instance"
```

### 依存関係 (`pyproject.toml`)
- **コア**: `litellm[proxy]>=1.72.1` (プロキシ機能付きLiteLLM)
- **開発**: pytest、カバレッジ、リンティングツールはRyeで管理

### 環境変数
- `PORT`: APIサーバーポート (デフォルト: 4000)
- `LITELLM_MASTER_KEY`: API認証キー (デフォルト: sk-1234)

## テストアプローチ

プロジェクトは階層化されたテスト戦略を使用しています：

### ユニットテスト (`tests/test_provider.py`)
- **対象**: `ClaudeCodeProvider`クラスのロジックのみ
- **速度**: 高速 (約1.7秒)
- **モック**: claude-code CLIへの`subprocess.run`呼び出し
- **カバレッジ**: プロバイダーロジックの94%
- **実行方法**: `make test`

### 統合テスト (`tests/test_integration.py`)
- **対象**: 完全なエンドツーエンドフロー (LiteLLM + Provider + claude-code CLI)
- **速度**: 低速 (約90秒)
- **実コンポーネント**: ポート4001の実際のLiteLLMサーバー、実際のclaude-code CLI呼び出し
- **テスト内容**: モデルエンドポイント、チャット完了、認証、並行リクエスト
- **実行方法**: `make test-integration`

### テスト構造
```
tests/
├── conftest.py           # 共有フィクスチャとモック
├── test_provider.py      # ユニットテスト (6テスト、claude-codeモック)
└── test_integration.py   # 統合テスト (4テスト、実claude-code)
```

### 重要なテストノート
- 統合テストは独自のLiteLLMサーバーを自動的に開始/停止します
- ユニットテストは速度のためにモックされたサブプロセス呼び出しを使用
- 統合テストはclaude-code CLIのインストールと認証が必要
- 日常開発には`make test`、リリース検証には`make test-integration`を使用

## プロジェクト構造

### 最小コア構造
```
claude_code_server/
├── __init__.py          # パッケージ初期化
└── provider.py          # CustomLLMプロバイダー実装 (コアロジック)

litellm_config.yaml      # LiteLLMプロキシ設定
```

### 完全なプロジェクト構造
```
├── claude_code_server/   # コアパッケージ
├── tests/               # テストスイート
├── Makefile            # 開発コマンド
├── pyproject.toml      # 依存関係とプロジェクト設定
├── litellm_config.yaml # LiteLLM設定
└── run_local.sh        # ローカル開発スクリプト
```

## 重要な注意事項

- **依存関係**: claude-code CLIのインストールと認証が必要
- **非同期サポート**: 同期 (`completion`) と非同期 (`acompletion`) メソッドの両方を実装
- **モデルレスポンス**: レスポンスでは常に `claude-code-server/claude-code` をモデル名として返す
- **メッセージ処理**: 最後のユーザーメッセージを抽出し、`-p` フラグ経由でclaude-codeに渡す
- **ログ**: claude-codeへのすべてのサブプロセス呼び出しはデバッグ用にログ出力される
- **ストリーミング非対応**: claude-code CLIはストリーミングをサポートしないため、レスポンスは完全なチャンクとして返される
- **ポート分離**: 統合テストはポート4000の開発サーバーとの競合を避けるためポート4001を使用
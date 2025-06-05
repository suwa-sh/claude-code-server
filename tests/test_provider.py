import subprocess

import pytest
from litellm import ModelResponse

from claude_code_server.provider import ClaudeCodeProvider


class TestClaudeCodeProvider:
    """ClaudeCodeProviderクラスのユニットテスト"""

    @pytest.fixture
    def provider(self):
        return ClaudeCodeProvider()

    def test_completion_正常なメッセージでcompletionを実行した場合_正しいレスポンスが返されること(self, provider, sample_messages, mock_subprocess_run):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = sample_messages

        #------------------------------
        # 実行 (Act)
        #------------------------------
        response = provider.completion(model=model, messages=messages)

        #------------------------------
        # 検証 (Assert)
        #------------------------------
        assert isinstance(response, ModelResponse)
        assert response.choices[0].message.content == "Hello from claude-code!"
        assert response.choices[0].finish_reason == "stop"
        assert response.model == "claude-code-server/claude-code"

        # Verify subprocess was called correctly
        mock_subprocess_run.assert_called_once()
        args, kwargs = mock_subprocess_run.call_args
        assert args[0] == ["/usr/local/bin/claude", "-p", "Hello, Claude!"]
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is True

    @pytest.mark.asyncio
    async def test_acompletion_正常なメッセージで非同期completionを実行した場合_正しいレスポンスが返されること(self, provider, sample_messages, mock_subprocess_run):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = sample_messages

        #------------------------------
        # 実行 (Act)
        #------------------------------
        response = await provider.acompletion(model=model, messages=messages)

        #------------------------------
        # 検証 (Assert)
        #------------------------------
        assert isinstance(response, ModelResponse)
        assert response.choices[0].message.content == "Hello from claude-code!"
        assert response.choices[0].finish_reason == "stop"
        assert response.model == "claude-code-server/claude-code"

        # Verify subprocess was called correctly
        mock_subprocess_run.assert_called_once()

    def test_completion_ユーザーメッセージがない場合_ValueErrorが発生すること(self, provider):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = [{"role": "system", "content": "System prompt"}]

        #------------------------------
        # 実行 & 検証 (Act & Assert)
        #------------------------------
        with pytest.raises(ValueError, match="No user messages found"):
            provider.completion(model=model, messages=messages)

    @pytest.mark.asyncio
    async def test_acompletion_ユーザーメッセージがない場合_ValueErrorが発生すること(self, provider):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = [{"role": "system", "content": "System prompt"}]

        #------------------------------
        # 実行 & 検証 (Act & Assert)
        #------------------------------
        with pytest.raises(ValueError, match="No user messages found"):
            await provider.acompletion(model=model, messages=messages)

    def test_completion_claude_code_コマンドが失敗した場合_RuntimeErrorが発生すること(self, provider, sample_messages, mocker):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = sample_messages
        
        # Mock shutil.which to return a valid path
        mocker.patch("shutil.which", return_value="/usr/local/bin/claude")
        
        # Mock subprocess to return error
        mock_subprocess = mocker.patch("subprocess.run")
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["claude", "-p", "Hello, Claude!"], stderr="Error: Authentication failed"
        )

        #------------------------------
        # 実行 & 検証 (Act & Assert)
        #------------------------------
        with pytest.raises(RuntimeError, match="claude-code failed"):
            provider.completion(model=model, messages=messages)

    @pytest.mark.asyncio
    async def test_astreaming_正常なメッセージで非同期streamingを実行した場合_正しいストリーミングレスポンスが返されること(self, provider, sample_messages, mock_subprocess_run):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = sample_messages

        #------------------------------
        # 実行 (Act)
        #------------------------------
        chunks = []
        async for chunk in provider.astreaming(model=model, messages=messages):
            chunks.append(chunk)
        
        #------------------------------
        # 検証 (Assert)
        #------------------------------
        # Verify we got one chunk (since claude-code doesn't support real streaming)
        assert len(chunks) == 1
        chunk = chunks[0]
        
        # Verify chunk format
        assert isinstance(chunk, dict)
        assert chunk["text"] == "Hello from claude-code!"
        assert chunk["is_finished"] is True
        assert chunk["finish_reason"] == "stop"
        assert "usage" in chunk
        assert chunk["usage"]["prompt_tokens"] == 2  # "Hello, Claude!" = 2 tokens
        assert chunk["usage"]["completion_tokens"] == 3  # "Hello from claude-code!" = 3 tokens
        assert chunk["usage"]["total_tokens"] == 5
        
        # Verify subprocess was called correctly
        mock_subprocess_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_astreaming_ユーザーメッセージがない場合_ValueErrorが発生すること(self, provider):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = [{"role": "system", "content": "System prompt"}]
        
        #------------------------------
        # 実行 & 検証 (Act & Assert)
        #------------------------------
        with pytest.raises(ValueError, match="No user messages found"):
            async for _ in provider.astreaming(model=model, messages=messages):
                pass
    
    def test_completion_APIキーが無効な場合_認証エラーが発生すること(self, provider, sample_messages, mocker):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = sample_messages
        
        # Mock shutil.which to return a valid path
        mocker.patch("shutil.which", return_value="/usr/local/bin/claude")
        
        # Mock subprocess to return authentication error
        mock_subprocess = mocker.patch("subprocess.run")
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["claude", "-p", "Hello, Claude!"], stderr="Invalid API key"
        )
        
        #------------------------------
        # 実行 & 検証 (Act & Assert)
        #------------------------------
        with pytest.raises(RuntimeError, match="claude-code authentication failed"):
            provider.completion(model=model, messages=messages)
    
    def test_completion_ログインが必要な場合_認証エラーが発生すること(self, provider, sample_messages, mocker):
        #------------------------------
        # 準備 (Arrange)
        #------------------------------
        model = "claude-code-server/claude-code"
        messages = sample_messages
        
        # Mock shutil.which to return a valid path
        mocker.patch("shutil.which", return_value="/usr/local/bin/claude")
        
        # Mock subprocess to return login prompt error
        mock_subprocess = mocker.patch("subprocess.run")
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["claude", "-p", "Hello, Claude!"], stderr="Please run /login to authenticate"
        )
        
        #------------------------------
        # 実行 & 検証 (Act & Assert)
        #------------------------------
        with pytest.raises(RuntimeError, match="claude-code authentication failed"):
            provider.completion(model=model, messages=messages)

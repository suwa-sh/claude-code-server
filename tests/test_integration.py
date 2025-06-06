import asyncio
import os
import subprocess
import time
from unittest.mock import MagicMock

import httpx
import pytest
from openai import OpenAI


@pytest.mark.integration
class TestIntegration:
    """litellmを起動して、OpenAPIクライアントからのアクセスを検証 前提: claude-codeがローカルで実行できること"""

    @pytest.fixture(scope="class")
    def server_process(self):
        """Start the server for integration tests"""
        env = os.environ.copy()
        env["PORT"] = "4001"  # Use different port to avoid conflicts

        # Start server using LiteLLM directly
        process = subprocess.Popen(
            ["rye", "run", "litellm", "--config", "litellm_config.yaml", "--port", "4001"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to be ready by checking health endpoint
        max_retries = 30  # 30 seconds
        for i in range(max_retries):
            try:
                response = httpx.get("http://localhost:4001", timeout=1.0)
                if response.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            process.terminate()
            raise RuntimeError("Server failed to start within 30 seconds")

        yield process

        # Cleanup
        process.terminate()
        process.wait(timeout=5)

    @pytest.fixture
    def client(self):
        """OpenAI client for integration tests"""
        return OpenAI(
            api_key="sk-1234",
            base_url="http://localhost:4001/v1",
        )

    @pytest.fixture
    def mock_claude_code(self, mocker):
        """Mock claude-code command for integration tests"""
        mock = mocker.patch("subprocess.run")
        result_mock = MagicMock()
        result_mock.stdout = "Integration test response from Claude"
        result_mock.stderr = ""
        result_mock.returncode = 0
        mock.return_value = result_mock
        return mock

    def test_models_endpoint_GETリクエストを送信した場合_claude_sonnet_4だけが返されること(self, server_process):
        #------------------------------
        # 準備
        #------------------------------
        url = "http://localhost:4001/v1/models"
        headers = {"Authorization": "Bearer sk-1234"}

        #------------------------------
        # 実行
        #------------------------------
        response = httpx.get(
            url,
            headers=headers
        )

        #------------------------------
        # 検証
        #------------------------------
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        assert data["data"][0]["id"] == "claude-sonnet-4"

    def test_chat_completion_正常なチャットリクエストを送信した場合_回答が得られること(self, server_process, client):
        #------------------------------
        # 準備
        #------------------------------
        model = "claude-sonnet-4"
        message = {"role": "user", "content": "Hello, Claude!"}

        #------------------------------
        # 実行
        #------------------------------
        response = client.chat.completions.create(
            model=model,
            messages=[message],
        )

        #------------------------------
        # 検証
        #------------------------------
        # Just verify we got a response with expected structure
        assert response.choices[0].message.content is not None
        assert len(response.choices[0].message.content) > 0
        assert response.choices[0].finish_reason == "stop"
        assert response.model == "claude-code-server/claude-code"

    def test_chat_completion_チャットリクエストで無効なAPIキーでリクエストを送信した場合_例外が発生すること(self, server_process):
        #------------------------------
        # 準備
        #------------------------------
        client = OpenAI(api_key="invalid-key", base_url="http://localhost:4001/v1")

        #------------------------------
        # 実行 & 検証
        #------------------------------
        with pytest.raises(Exception):  # Should raise authentication error
            client.chat.completions.create(
                model="claude-sonnet-4", messages=[{"role": "user", "content": "Test"}]
            )

    def test_chat_completion_streamチャットリクエストを送信した場合_回答が得られること(self, server_process, client):
        #------------------------------
        # 準備
        #------------------------------
        model = "claude-sonnet-4"
        message = {"role": "user", "content": "Hello, Claude!"}

        #------------------------------
        # 実行
        #------------------------------
        stream = client.chat.completions.create(
            model=model,
            messages=[message],
            stream=True
        )
        
        #------------------------------
        # 検証
        #------------------------------
        # Collect chunks
        chunks = []
        for chunk in stream:
            chunks.append(chunk)
        
        # Verify we got at least one chunk
        assert len(chunks) > 0
        
        # Verify first chunk has role or content
        first_chunk = chunks[0]
        assert hasattr(first_chunk.choices[0].delta, 'role') or hasattr(first_chunk.choices[0].delta, 'content')
        
        # Verify last chunk has finish_reason
        last_chunk = chunks[-1]
        assert last_chunk.choices[0].finish_reason == "stop"

    def test_chat_completion_streamチャットリクエストで無効なmodelでリクエストを送信した場合__例外が発生すること(self, server_process, client):
        #------------------------------
        # 準備
        #------------------------------
        model = "not-exists"
        message = {"role": "user", "content": "Hello, Claude!"}

        #------------------------------
        # 実行 & 検証
        #------------------------------
        with pytest.raises(Exception):  # Should raise authentication error
            client.chat.completions.create(
                model=model,
                messages=[message],
                stream=True
            )

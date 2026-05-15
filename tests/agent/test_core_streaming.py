from unittest.mock import Mock, patch
from app.agent.core import agent_loop

def test_agent_loop_without_callback():
    """测试无回调时保持原有同步行为"""
    messages = [{"role": "user", "content": "test"}]
    
    with patch("app.agent.core.client.messages.create") as mock_create:
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Hello")]
        mock_response.stop_reason = "end_turn"
        mock_create.return_value = mock_response
        
        agent_loop(messages)
        
        assert len(messages) == 2
        assert messages[1]["role"] == "assistant"

def test_agent_loop_with_stream_callback():
    """测试有回调时触发流式输出"""
    messages = [{"role": "user", "content": "test"}]
    collected = []
    
    def callback(text: str):
        collected.append(text)
    
    with patch("app.agent.core.client.messages.create") as mock_create:
        # 模拟完整的流式响应（包含 content_block_start/delta/stop）
        mock_start = Mock()
        mock_start.type = "content_block_start"
        mock_start.index = 0
        mock_start.content_block = Mock(type="text")
        
        mock_delta1 = Mock()
        mock_delta1.type = "content_block_delta"
        mock_delta1.delta = Mock(text="Hel")
        
        mock_delta2 = Mock()
        mock_delta2.type = "content_block_delta"
        mock_delta2.delta = Mock(text="lo")
        
        mock_stop = Mock()
        mock_stop.type = "content_block_stop"
        
        mock_msg_delta = Mock()
        mock_msg_delta.type = "message_delta"
        mock_msg_delta.delta = Mock(stop_reason="end_turn")
        
        mock_create.return_value = [mock_start, mock_delta1, mock_delta2, mock_stop, mock_msg_delta]
        
        agent_loop(messages, stream_callback=callback)
        
        assert collected == ["Hel", "lo"]
        assert len(messages) == 2

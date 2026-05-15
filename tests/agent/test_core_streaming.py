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
        # 模拟流式响应
        mock_event1 = Mock()
        mock_event1.type = "content_block_delta"
        mock_event1.delta = Mock(text="Hel")
        
        mock_event2 = Mock()
        mock_event2.type = "content_block_delta"
        mock_event2.delta = Mock(text="lo")
        
        # stream=True 返回迭代器
        mock_create.return_value = [mock_event1, mock_event2]
        
        agent_loop(messages, stream_callback=callback)
        
        assert collected == ["Hel", "lo"]
        assert len(messages) == 2

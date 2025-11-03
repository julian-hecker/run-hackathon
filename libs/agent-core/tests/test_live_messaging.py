"""Tests for live_messaging module."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai.types import Content, Blob

from agent_core.runtime.live_messaging import (
    text_to_content,
    start_agent_session,
    agent_to_client_messaging,
    send_pcm_to_agent,
    AgentInterruptedEvent,
    AgentTurnCompleteEvent,
    AgentDataEvent,
    AgentEvent,
    APP_NAME,
)


class TestTextToContent:
    """Tests for text_to_content helper function."""

    def test_text_to_content_user_role(self):
        """Test creating content with default user role."""
        content = text_to_content("Hello, world!")
        assert isinstance(content, Content)
        assert content.role == "user"
        assert len(content.parts) == 1
        assert content.parts[0].text == "Hello, world!"

    def test_text_to_content_model_role(self):
        """Test creating content with model role."""
        content = text_to_content("Hello, world!", role="model")
        assert isinstance(content, Content)
        assert content.role == "model"
        assert content.parts[0].text == "Hello, world!"


class TestEventModels:
    """Tests for event model classes."""

    def test_agent_interrupted_event(self):
        """Test AgentInterruptedEvent model."""
        event = AgentInterruptedEvent(timestamp=1234.56)
        assert event.type == "interrupted"
        assert event.timestamp == 1234.56

    def test_agent_turn_complete_event(self):
        """Test AgentTurnCompleteEvent model."""
        event = AgentTurnCompleteEvent(timestamp=5678.90)
        assert event.type == "complete"
        assert event.timestamp == 5678.90

    def test_agent_data_event(self):
        """Test AgentDataEvent model."""
        payload = b"audio_data_bytes"
        event = AgentDataEvent(payload=payload)
        assert event.type == "data"
        assert event.payload == payload

    def test_agent_event_union(self):
        """Test that AgentEvent union type works correctly."""
        # Should accept any of the event types
        events: list[AgentEvent] = [
            AgentInterruptedEvent(timestamp=1.0),
            AgentTurnCompleteEvent(timestamp=2.0),
            AgentDataEvent(payload=b"data"),
        ]
        assert len(events) == 3
        assert events[0].type == "interrupted"
        assert events[1].type == "complete"
        assert events[2].type == "data"


@pytest.mark.asyncio
class TestStartAgentSession:
    """Tests for start_agent_session function."""

    @patch("agent_core.runtime.live_messaging.InMemoryRunner")
    @patch("agent_core.runtime.live_messaging.LiveRequestQueue")
    async def test_start_agent_session_creates_runner(
        self, mock_queue_class, mock_runner_class
    ):
        """Test that start_agent_session creates a runner with correct config."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner

        mock_session = MagicMock()
        mock_runner.session_service.create_session = AsyncMock(
            return_value=mock_session
        )

        mock_live_events = AsyncMock(spec=AsyncGenerator)
        mock_runner.run_live.return_value = mock_live_events

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        # Call function
        live_events, live_request_queue = await start_agent_session(
            agent=mock_agent, user_id="user123", session_id="session456"
        )

        # Verify runner was created correctly
        mock_runner_class.assert_called_once_with(
            mock_agent,
            app_name=APP_NAME,
        )

        # Verify session was created
        mock_runner.session_service.create_session.assert_awaited_once_with(
            app_name=APP_NAME,
            user_id="user123",
            session_id="session456",
        )

        # Verify run_live was called with correct config
        mock_runner.run_live.assert_called_once()
        call_kwargs = mock_runner.run_live.call_args[1]
        assert call_kwargs["live_request_queue"] == mock_queue
        assert call_kwargs["session"] == mock_session
        assert call_kwargs["run_config"] is not None
        assert call_kwargs["run_config"].streaming_mode.value == "bidi"

        # Verify return values
        assert live_events == mock_live_events
        assert live_request_queue == mock_queue

    @patch("agent_core.runtime.live_messaging.InMemoryRunner")
    @patch("agent_core.runtime.live_messaging.LiveRequestQueue")
    async def test_start_agent_session_config(
        self, mock_queue_class, mock_runner_class
    ):
        """Test that start_agent_session creates correct run config."""
        mock_agent = MagicMock()
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner

        mock_session = MagicMock()
        mock_runner.session_service.create_session = AsyncMock(
            return_value=mock_session
        )
        mock_runner.run_live.return_value = AsyncMock()
        mock_queue_class.return_value = MagicMock()

        await start_agent_session(
            agent=mock_agent, user_id="user123", session_id="session456"
        )

        # Verify run_config structure
        call_kwargs = mock_runner.run_live.call_args[1]
        run_config = call_kwargs["run_config"]

        assert run_config.speech_config is not None
        assert run_config.speech_config.language_code == "en-US"
        assert run_config.streaming_mode.value == "bidi"
        assert run_config.realtime_input_config is not None


@pytest.mark.asyncio
class TestAgentToClientMessaging:
    """Tests for agent_to_client_messaging function."""

    async def test_turn_complete_event(self):
        """Test handling of turn_complete events."""
        # Create a mock event with turn_complete
        mock_event = MagicMock()
        mock_event.turn_complete = True
        mock_event.timestamp = 123.45
        mock_event.interrupted = False
        mock_event.content = None

        # Create async generator that yields the event
        async def event_generator():
            yield mock_event

        # Track callbacks
        callback_events = []

        async def on_event(event: AgentEvent):
            callback_events.append(event)

        # Run the messaging function
        await agent_to_client_messaging(on_event, event_generator())

        # Verify callback was called with correct event
        assert len(callback_events) == 1
        assert isinstance(callback_events[0], AgentTurnCompleteEvent)
        assert callback_events[0].type == "complete"
        assert callback_events[0].timestamp == 123.45

    async def test_interrupted_event(self):
        """Test handling of interrupted events."""
        mock_event = MagicMock()
        mock_event.turn_complete = False
        mock_event.interrupted = True
        mock_event.timestamp = 678.90
        mock_event.content = None

        async def event_generator():
            yield mock_event

        callback_events = []

        async def on_event(event: AgentEvent):
            callback_events.append(event)

        await agent_to_client_messaging(on_event, event_generator())

        assert len(callback_events) == 1
        assert isinstance(callback_events[0], AgentInterruptedEvent)
        assert callback_events[0].type == "interrupted"
        assert callback_events[0].timestamp == 678.90

    async def test_audio_data_event(self):
        """Test handling of audio data events."""
        audio_bytes = b"fake_audio_data_12345"

        # Create mock inline_data
        mock_inline_data = MagicMock()
        mock_inline_data.mime_type = "audio/pcm;rate=24000"
        mock_inline_data.data = audio_bytes

        # Create mock part
        mock_part = MagicMock()
        mock_part.inline_data = mock_inline_data
        mock_part.text = None
        # Make hasattr return True for inline_data check
        type(mock_part).inline_data = mock_inline_data

        # Create mock content
        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        mock_event = MagicMock()
        mock_event.turn_complete = False
        mock_event.interrupted = False
        mock_event.content = mock_content
        mock_event.timestamp = 999.99

        async def event_generator():
            yield mock_event

        callback_events = []

        async def on_event(event: AgentEvent):
            callback_events.append(event)

        await agent_to_client_messaging(on_event, event_generator())

        assert len(callback_events) == 1
        assert isinstance(callback_events[0], AgentDataEvent)
        assert callback_events[0].type == "data"
        assert callback_events[0].payload == audio_bytes

    async def test_text_event_ignored(self):
        """Test that text events are ignored."""
        mock_part = MagicMock()
        mock_part.text = "Hello, world!"
        # Make hasattr return True for text check
        type(mock_part).text = "Hello, world!"
        mock_part.inline_data = None

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        mock_event = MagicMock()
        mock_event.turn_complete = False
        mock_event.interrupted = False
        mock_event.content = mock_content

        async def event_generator():
            yield mock_event

        callback_events = []

        async def on_event(event: AgentEvent):
            callback_events.append(event)

        await agent_to_client_messaging(on_event, event_generator())

        # Text events should be ignored, no callback
        assert len(callback_events) == 0

    async def test_empty_content_skipped(self):
        """Test that events with empty content are skipped."""
        mock_event = MagicMock()
        mock_event.turn_complete = False
        mock_event.interrupted = False
        mock_event.content = None

        async def event_generator():
            yield mock_event

        callback_events = []

        async def on_event(event: AgentEvent):
            callback_events.append(event)

        await agent_to_client_messaging(on_event, event_generator())

        assert len(callback_events) == 0

    async def test_empty_parts_skipped(self):
        """Test that events with empty parts are skipped."""
        mock_content = MagicMock()
        mock_content.parts = []

        mock_event = MagicMock()
        mock_event.turn_complete = False
        mock_event.interrupted = False
        mock_event.content = mock_content

        async def event_generator():
            yield mock_event

        callback_events = []

        async def on_event(event: AgentEvent):
            callback_events.append(event)

        await agent_to_client_messaging(on_event, event_generator())

        assert len(callback_events) == 0

    async def test_audio_without_data_skipped(self):
        """Test that audio parts without data are skipped."""
        mock_inline_data = MagicMock()
        mock_inline_data.mime_type = "audio/pcm;rate=24000"
        mock_inline_data.data = None

        mock_part = MagicMock()
        mock_part.inline_data = mock_inline_data
        mock_part.text = None
        type(mock_part).inline_data = mock_inline_data

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        mock_event = MagicMock()
        mock_event.turn_complete = False
        mock_event.interrupted = False
        mock_event.content = mock_content

        async def event_generator():
            yield mock_event

        callback_events = []

        async def on_event(event: AgentEvent):
            callback_events.append(event)

        await agent_to_client_messaging(on_event, event_generator())

        assert len(callback_events) == 0

    async def test_multiple_events_processed(self):
        """Test that multiple events are processed in sequence."""
        events = [
            MagicMock(
                turn_complete=True, interrupted=False, timestamp=1.0, content=None
            ),
            MagicMock(
                turn_complete=False, interrupted=True, timestamp=2.0, content=None
            ),
            MagicMock(
                turn_complete=False, interrupted=False, timestamp=3.0, content=None
            ),
        ]

        async def event_generator():
            for event in events:
                yield event

        callback_events = []

        async def on_event(event: AgentEvent):
            callback_events.append(event)

        await agent_to_client_messaging(on_event, event_generator())

        assert len(callback_events) == 2  # Only turn_complete and interrupted
        assert isinstance(callback_events[0], AgentTurnCompleteEvent)
        assert isinstance(callback_events[1], AgentInterruptedEvent)


class TestSendPcmToAgent:
    """Tests for send_pcm_to_agent function."""

    def test_send_pcm_to_agent_calls_send_realtime(self):
        """Test that send_pcm_to_agent calls send_realtime with correct format."""
        mock_queue = MagicMock()
        pcm_audio = b"fake_pcm_audio_bytes"

        send_pcm_to_agent(pcm_audio, mock_queue)

        # Verify send_realtime was called
        mock_queue.send_realtime.assert_called_once()
        call_arg = mock_queue.send_realtime.call_args[0][0]

        # Verify it's a Blob with correct format
        assert isinstance(call_arg, Blob)
        assert call_arg.data == pcm_audio
        assert call_arg.mime_type == "audio/pcm;rate=16000"

    def test_send_pcm_to_agent_with_empty_bytes(self):
        """Test sending empty audio bytes."""
        mock_queue = MagicMock()
        empty_audio = b""

        send_pcm_to_agent(empty_audio, mock_queue)

        mock_queue.send_realtime.assert_called_once()
        call_arg = mock_queue.send_realtime.call_args[0][0]
        assert call_arg.data == empty_audio

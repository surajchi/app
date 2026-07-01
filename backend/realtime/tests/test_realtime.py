import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser

from realtime.auth import get_user_from_token
from realtime.consumers import MarketConsumer


@pytest.mark.django_db
def test_get_user_from_token_valid_and_invalid():
    from rest_framework_simplejwt.tokens import AccessToken

    from apps.users.tests.factories import UserFactory

    user = UserFactory()
    token = str(AccessToken.for_user(user))
    assert get_user_from_token(token).id == user.id
    assert isinstance(get_user_from_token("not-a-token"), AnonymousUser)
    assert isinstance(get_user_from_token(None), AnonymousUser)


async def test_connect_and_ping():
    communicator = WebsocketCommunicator(MarketConsumer.as_asgi(), "/ws/")
    connected, _ = await communicator.connect()
    assert connected
    assert (await communicator.receive_json_from())["type"] == "connected"

    await communicator.send_json_to({"action": "ping"})
    assert (await communicator.receive_json_from())["type"] == "pong"
    await communicator.disconnect()


async def test_subscribe_and_receive_quote():
    communicator = WebsocketCommunicator(MarketConsumer.as_asgi(), "/ws/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.receive_json_from()  # "connected"

    await communicator.send_json_to({"action": "subscribe", "channels": ["quotes.AAPL"]})
    ack = await communicator.receive_json_from()
    assert ack["type"] == "subscribed"
    assert "quotes.AAPL" in ack["channels"]

    layer = get_channel_layer()
    await layer.group_send(
        "quotes.AAPL",
        {
            "type": "quote.message",
            "group": "quotes.AAPL",
            "data": {"symbol": "AAPL", "price": 123.45},
        },
    )
    frame = await communicator.receive_json_from()
    assert frame["type"] == "quote"
    assert frame["channel"] == "quotes.AAPL"
    assert frame["data"]["price"] == 123.45
    await communicator.disconnect()


async def test_news_channel_receives_breaking_news():
    communicator = WebsocketCommunicator(MarketConsumer.as_asgi(), "/ws/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.receive_json_from()  # "connected"

    await communicator.send_json_to({"action": "subscribe", "channels": ["news"]})
    ack = await communicator.receive_json_from()
    assert ack["type"] == "subscribed"
    assert "news" in ack["channels"]

    layer = get_channel_layer()
    await layer.group_send(
        "news",
        {"type": "news.message", "group": "news", "data": {"title": "Breaking headline"}},
    )
    frame = await communicator.receive_json_from()
    assert frame["type"] == "news"
    assert frame["data"]["title"] == "Breaking headline"
    await communicator.disconnect()


async def test_unknown_action_returns_error():
    communicator = WebsocketCommunicator(MarketConsumer.as_asgi(), "/ws/")
    await communicator.connect()
    await communicator.receive_json_from()  # "connected"
    await communicator.send_json_to({"action": "nope"})
    assert (await communicator.receive_json_from())["type"] == "error"
    await communicator.disconnect()

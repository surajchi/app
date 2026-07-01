from django.urls import path

from apps.notifications.views import (
    DeviceRegisterView,
    MarkReadView,
    NotificationListView,
    PreferenceView,
    TestNotificationView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("read/", MarkReadView.as_view(), name="read"),
    path("preferences/", PreferenceView.as_view(), name="preferences"),
    path("devices/register/", DeviceRegisterView.as_view(), name="device-register"),
    path("test/", TestNotificationView.as_view(), name="test"),
]

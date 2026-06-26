from django.urls import path

from apps.accounts.views import ActivityView, DeviceDeleteView, DeviceListView
from apps.profiles.views import ProfileView

app_name = "profiles"

urlpatterns = [
    path("", ProfileView.as_view(), name="profile"),
    path("devices/", DeviceListView.as_view(), name="devices"),
    path("devices/<uuid:id>/", DeviceDeleteView.as_view(), name="device-delete"),
    path("activity/", ActivityView.as_view(), name="activity"),
]

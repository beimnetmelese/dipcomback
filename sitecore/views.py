from rest_framework import permissions, viewsets
from rest_framework.response import Response

from accounts.permissions import IsAdminOnly

from .models import PlatformSettings
from .serializers import PlatformSettingsSerializer


class PlatformSettingsViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action in {'update', 'partial_update'}:
            return [permissions.IsAuthenticated(), IsAdminOnly()]
        return [permissions.AllowAny()]

    def list(self, request):
        settings = PlatformSettings.get_solo()
        return Response(PlatformSettingsSerializer(settings).data)

    def retrieve(self, request, pk=None):
        settings = PlatformSettings.get_solo()
        return Response(PlatformSettingsSerializer(settings).data)

    def update(self, request, pk=None):
        settings = PlatformSettings.get_solo()
        serializer = PlatformSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    partial_update = update

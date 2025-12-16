from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser

from . import services
from .models import File
from filehub.core.fga.relations import FGARelation
from .serializers import FileSerializer, FileShareSerializer


class FileListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/files/      -> list files
    POST /api/files/      -> upload new file
    """

    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        allowed_file_ids = services.fga_list_viewable_file_ids(user)
        return File.objects.filter(uuid__in=allowed_file_ids)

    def perform_create(self, serializer):
        file_instance = serializer.save()
        services.fga_write_owner(
            user=self.request.user,
            file=file_instance,
        )

class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/files/<uuid>/      -> retrieve (requires OpenFGA check)
    PUT    /api/files/<uuid>/      -> update file (requires OpenFGA check)
    PATCH  /api/files/<uuid>/      -> partially update (requires OpenFGA check)
    DELETE /api/files/<uuid>/      -> delete (requires OpenFGA check)
    """

    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "uuid"

    def get_queryset(self):
        if self.request.method == "GET":
            user = self.request.user
            allowed_file_ids = services.fga_list_viewable_file_ids(user)
            return File.objects.filter(uuid__in=allowed_file_ids)

        return File.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        method = self.request.method

        if method in ("GET", "HEAD", "OPTIONS"):
            allowed = services.fga_check(user=user, relation=FGARelation.CAN_VIEW.value, file=obj)
        elif method in ("PUT", "PATCH"):
            allowed = services.fga_check(user=user, relation=FGARelation.CAN_EDIT.value, file=obj)
        elif method == "DELETE":
            allowed = services.fga_check(user=user, relation=FGARelation.OWNER.value, file=obj)
        else:
            allowed = False

        if not allowed:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access this file.")

        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        services.update_file(
            file_instance=instance,
            file_obj=serializer.validated_data.get("file"),
        )

        # Re-serialize the updated instance for response
        output_serializer = self.get_serializer(instance)
        return Response(output_serializer.data)

    def perform_destroy(self, instance):
        services.delete_file( file_instance=instance)


class FileShareView(APIView):
    """
    POST /api/files/<uuid>/share/
    body:
    {
        "permissions": [
            { "user_id": "1", "relation": "can_edit" },
            { "user_id": "2", "relation": "can_view" }
        ]
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, uuid):
        try:
            file_instance = File.objects.get(uuid=uuid)
        except File.DoesNotExist:
            return Response(
                {"detail": "File not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Ensure caller is allowed to share (e.g. must be 'owner')
        if not services.fga_check(user=request.user, relation=FGARelation.OWNER.value, file=file_instance):
            return Response(
                {"detail": "You do not have permission to share this file."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = FileShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            services.fga_grant_relation(
                file=file_instance,
                assignments=serializer.validated_data["permissions"],
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        return Response({"detail": "File shared successfully."}, status=status.HTTP_200_OK)


class FilePermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, uuid):
        try:
            file_instance = File.objects.get(uuid=uuid)
        except File.DoesNotExist:
            return Response({"detail": "File not found."}, status=404)

        owners = services.fga_list_file_users(
            file=file_instance,
            relation=FGARelation.OWNER.value
        )
        viewers = services.fga_list_file_users(
            file=file_instance,
            relation=FGARelation.VIEWER.value
        )
        editors = services.fga_list_file_users(
            file=file_instance,
            relation=FGARelation.EDITOR.value
        )

        return Response({
            "file": str(uuid),
            "permissions": {
                "owners": owners,
                "viewers": viewers,
                "editors": editors
            }
        })


class FileRelations(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, uuid):
        try:
            file_instance = File.objects.get(uuid=uuid)
        except File.DoesNotExist:
            return Response({"detail": "File not found."}, status=404)
        
        data  = services.fga_file_relation_users(user=self.request.user, file=file_instance )

        return Response(data)
        

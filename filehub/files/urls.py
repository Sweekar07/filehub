from django.urls import path
from .views import (
    FileListCreateView, 
    FileDetailView, 
    FileShareView, 
    FilePermissionsView, 
    FileRelations
)

urlpatterns = [
    path("files/", FileListCreateView.as_view(), name="file-list-create"),
    path("files/<uuid:uuid>/", FileDetailView.as_view(), name="file-detail"),
    path("files/<uuid:uuid>/share/", FileShareView.as_view(), name="file-share"),
    path("files/<uuid:uuid>/permissions/", FilePermissionsView.as_view(), name="file-permissions"),
    path("files/<uuid:uuid>/relations/", FileRelations.as_view(), name="file-relastions")
]

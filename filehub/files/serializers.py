from rest_framework import serializers
from .models import File
from filehub.core.fga.relations import FGARelation

class FileSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = File
        fields = [
            "uuid",
            "file",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "created_at", "updated_at"]


class FileShareItemSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    relation = serializers.ChoiceField(choices=[r.value for r in FGARelation])

class FileShareSerializer(serializers.Serializer):
    permissions = FileShareItemSerializer(many=True)

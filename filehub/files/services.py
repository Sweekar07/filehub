import logging
from asgiref.sync import async_to_sync
from rest_framework.exceptions import APIException
from openfga_sdk import UserTypeFilter
from openfga_sdk.rest import ApiException
from openfga_sdk.client.models import (
    ClientListObjectsRequest, 
    ClientTuple, 
    ClientWriteRequest, 
    ClientCheckRequest, 
    ClientListRelationsRequest
)
from openfga_sdk.models.fga_object import FgaObject
from openfga_sdk.client.models.list_users_request import ClientListUsersRequest
from django.contrib.auth import get_user_model

from .models import File
from filehub.core.fga.client import get_fga_client 
from filehub.core.fga.relations import FGARelation


User = get_user_model()

logger = logging.getLogger(__name__)


# -----------------------
# Helpers
# -----------------------
def _fga_user_id(user) -> str:
    """
    Map Django user -> OpenFGA user identifier.
    """
    return f"user:{user.id}"


def _fga_file_id(file: File) -> str:
    """
    Map File model -> OpenFGA object identifier.
    """
    return f"file:{file.uuid}"


def _handle_api_exception(exc: ApiException, context_msg: str = ""):
    """
    Wrap OpenFGA ApiException into a DRF APIException so views return proper HTTP 500 responses.
    Add log entries for easier debugging.
    """
    logger.exception("%s: OpenFGA ApiException: %s", context_msg, exc)
    raise APIException(detail=f"OpenFGA error: {getattr(exc, 'body', str(exc))}")


# ---- File persistence helpers ----


def create_file(*, file_obj) -> File:
    return File.objects.create(file=file_obj)


def update_file(*, file_instance: File, file_obj=None) -> File:
    if file_obj is not None:
        file_instance.file = file_obj
        file_instance.save()
    return file_instance

async def fga_delete_file_tuple_async(*, file: File):
    client = get_fga_client()
    body = ClientWriteRequest(
        deletes=[
            ClientTuple(
            user="user:*",
            relation=FGARelation.OWNER.value,
            object=_fga_file_id(file)
        ),
        ClientTuple(user="*", relation=FGARelation.VIEWER.value, object=_fga_file_id(file)),
        ]
    )
    await client.write(body)

def delete_file(*, file_instance: File) -> None:
    async_to_sync(fga_delete_file_tuple_async)(file=file_instance)
    file_instance.delete()



# -----------------------
# Basic permission checks
# -----------------------
async def _fga_check_async(user, relation: str, file: File) -> bool:
    client = get_fga_client()
    body = ClientCheckRequest(
        user=_fga_user_id(user),
        relation=relation,
        object=_fga_file_id(file)
    )
    try:
        resp = await client.check(body)
    except ApiException as exc:
        _handle_api_exception(exc, "fga_check")
    return bool(resp.allowed)


def fga_check(*, user, relation: str, file: File) -> bool:
    """
    Sync wrapper used in views; Django views are sync by default.
    Raises APIException on OpenFGA error.
    """
    return async_to_sync(_fga_check_async)(user=user, relation=relation, file=file)


# -----------------------
# List objects user can access
# -----------------------
async def _fga_list_objects_async(user, relation: str, obj_type: str) -> list[str]:
    client = get_fga_client()
    body = ClientListObjectsRequest(
        user=_fga_user_id(user),
        relation=relation,
        type=obj_type
    )  
    try:
        resp = await client.list_objects(body)
    except ApiException as exc:
        _handle_api_exception(exc, "fga_list_objects")
    objects = getattr(resp, "objects", []) or []
    return [obj.split(":", 1)[1] for obj in objects]


def fga_list_viewable_file_ids(user) -> list[str]:
    """Return list of file UUIDs the user can view (sync wrapper)."""
    return async_to_sync(_fga_list_objects_async)(user=user, relation=FGARelation.CAN_VIEW.value, obj_type="file")



# -----------------------
# Write owner tuple when creating file
# -----------------------
async def _fga_write_owner_async(*, user, file: File) -> None:
    client = get_fga_client()
    body = ClientWriteRequest(
        writes=[
            ClientTuple(
            user=_fga_user_id(user),
            relation=FGARelation.OWNER.value,
            object=_fga_file_id(file),
        )
        ]
    )
    try:
        await client.write(body)
    except ApiException as exc:
        _handle_api_exception(exc, "fga_write_owner")


def fga_write_owner(*, user, file: File) -> None:
    return async_to_sync(_fga_write_owner_async)(user=user, file=file)



# -----------------------
# Grant / Revoke relations
# -----------------------
async def _fga_apply_write_tuples_async(*, writes: list[ClientTuple]) -> None:
    client = get_fga_client()
    body = ClientWriteRequest(writes=writes)
    try:
        await client.write(body)
    except ApiException as exc:
        _handle_api_exception(exc, "fga_write_tuples")

def fga_grant_relation(*, file: File, assignments: list[dict]) -> None:
    writes = []
    for perm in assignments:
        try:
            user = User.objects.get(id=perm["user_id"])
        except User.DoesNotExist:
            raise ValueError(f"User with uuid {perm['id']} does not exist")
        
        writes.append(
            ClientTuple(
                user=_fga_user_id(user),
                relation=perm["relation"],
                object=_fga_file_id(file),
            )
        )
    return async_to_sync(_fga_apply_write_tuples_async)(writes=writes)




# -----------------------
# List users for a file & relation
# -----------------------
async def _fga_list_users_for_file_async(file: File, relation: str) -> list:
    client = get_fga_client()
    request = ClientListUsersRequest(
        object=FgaObject(type="file", id=str(file.uuid)),
        relation=relation,
        user_filters=[
            UserTypeFilter(type="user")
        ],
        context={}
    )
    try:
        resp = await client.list_users(request)
    except ApiException as exc:
        _handle_api_exception(exc, "fga_list_users_for_file")
    
    users = []
    for entry in getattr(resp, "users", []) or []:
        obj = getattr(entry, "object", None)
        if obj:
            users.append(f"user:{obj.id}")
    return users


def fga_list_file_users(file: File, relation: str) -> list[str]:
    return async_to_sync(_fga_list_users_for_file_async)(file=file, relation=relation)



# -----------------------
# List relations the user has on an object
# -----------------------
async def _fga_list_relations_for_user_file_async(user, file: File):
    client = get_fga_client()
    body = ClientListRelationsRequest(
        user=_fga_user_id(user),
        object=_fga_file_id(file),
        relations=[
            FGARelation.OWNER.value, FGARelation.VIEWER.value, FGARelation.EDITOR.value
        ]
    )
    try:
        relations_list  = await client.list_relations(body)
    except ApiException as exc:
        _handle_api_exception(exc, "fga_list_relations_for_user_file")

    return {
            "user": _fga_user_id(user),
            "object": _fga_file_id(file),
            "relations": relations_list,
        }

def fga_file_relation_users(user, file: File):
    return async_to_sync(_fga_list_relations_for_user_file_async)(user=user, file=file)

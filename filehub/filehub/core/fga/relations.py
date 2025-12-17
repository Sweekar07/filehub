from enum import Enum

class FGARelation(str, Enum):
    OWNER = "owner"
    VIEWER = "viewer"
    EDITOR = "editor"
    CAN_VIEW = "can_view"
    CAN_EDIT = "can_edit"

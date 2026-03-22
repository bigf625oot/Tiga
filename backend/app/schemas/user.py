from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, field_validator
import json
from datetime import datetime

# --- Role Schemas ---
class RoleBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    is_system: bool = False
    permissions: List[str] = []

    @field_validator("permissions", mode="before")
    @classmethod
    def parse_permissions(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    name: Optional[str] = None
    code: Optional[str] = None
    is_system: Optional[bool] = None
    permissions: Optional[List[str]] = None

class RoleInDBBase(RoleBase):
    id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Role(RoleInDBBase):
    userCount: int = 0

# --- Department Schemas ---
class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    leader: Optional[str] = None
    phone: Optional[str] = None
    parent_id: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(DepartmentBase):
    name: Optional[str] = None
    code: Optional[str] = None

class DepartmentInDBBase(DepartmentBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Department(DepartmentInDBBase):
    userCount: int = 0

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role_id: str
    department_id: Optional[str] = None
    status: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role_id: Optional[str] = None
    department_id: Optional[str] = None
    status: Optional[bool] = None
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: str
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class User(UserInDBBase):
    role: Optional[Role] = None
    department: Optional[Department] = None

class UserInDB(UserInDBBase):
    hashed_password: str

# Pagination Response
class UserPage(BaseModel):
    items: List[User]
    total: int
    page: int
    page_size: int

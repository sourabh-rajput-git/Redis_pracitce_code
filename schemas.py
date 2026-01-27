from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str

class UserUpdate(UserCreate):
    name: str

class UserResponse(BaseModel):
    id: int
    name: str
    

class UserUpload(BaseModel):
    file_path: str

# from_attributes (formerly orm_mode) is used for arbitrary objects (unpredictable objects)
class Config:
        from_attributes = True

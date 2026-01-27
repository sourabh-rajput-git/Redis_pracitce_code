from fastapi import APIRouter, Depends,HTTPException, File, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Annotated
from models import User
import schemas
from database import get_db
import uuid
from redis_client import r,q

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/hello")
def hello_func():
    return {
        "message" : "Hello_world"
            }


# Function that a background worker will execute
def process_image_task(image_id: str, file_path: str):
    # In a real application, this is where you'd perform 
    # intensive tasks like resizing, storing in S3/permanent storage, etc.
    print(f"Processing image {image_id} from {file_path}")
    
    # Example: update Redis status key
    r.set(f"image_status:{image_id}", "processed")
    # Clean up the temporary file after processing if necessary

@router.post("/create-users", response_model=schemas.UserResponse , status_code = 201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Docstring for create_user
    
    :param user: Creating the name object to store in db
    :type user: schemas.UserCreate
    :param db: Dependency injection for handling session
    :type db: Session
    """
    db_user = User(name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/get-all-users", response_model=list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    """
    Docstring for get_users
    
    :param db: Dependency injection for handling session
    :type db: Session
    """
    return db.query(User).all()


@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(
                user_id: int,
                user: schemas.UserUpdate,
                db: Session = Depends(get_db)
    ):
    """
    Docstring for update_user
    
    :param user_id: Id is used to find the user that needs to be updated
    :type user_id: int
    :param user: This is the new data that is being commited
    :type user: schemas.UserUpdate
    :param db: Dependency injection for handling session
    :type db: Session
    """
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = user.name

    db.commit()
    db.refresh(db_user)

    return db_user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Docstring for delete_user
    
    :param user_id: Used to find the user that needs to be deleted
    :type user_id: int
    :param db: Dependency injection for handling session
    :type db: Session
    """
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return {"deleted": user_id}

@router.post("/files/")
async def create_file(file: Annotated[bytes,File(description="This is a file")]):
    return {"file_size": len(file)}


@router.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}

@router.post("/upload/{user_id}", response_model=schemas.UserUpload)
async def uploadfile(file: UploadFile, user_id: int, db: Session = Depends(get_db)):
    """
    Docstring for uploadfile
    
    :param file: Description
    :type file: UploadFile
    :param user_id: Descriptiondef override_get_db():  
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override dependency
app.dependency_overrides[get_db] = override_get_db
    :type user_id: int
    :param db: Description
    :type db: Session
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    try:

        print("This is try")
        file_extension= (file.filename) [1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"./uploads/{unique_filename}"

        with open(file_path, "wb") as f:
            f.write(file.file.read())
            db_user.file_path=file_path
            db.commit()

        r.set(f"user_file:{user_id}", db_user.file_path)
        # Enqueue the background processing task
        # This is a non-blocking operation for the API endpoint
        q.enqueue(process_image_task, unique_filename, file_path)
        return db_user
    except Exception as e:
        return {"message": e.args}
    

@router.get("/find-file/{user_id}", response_model=schemas.UserUpload)
async def find_file(user_id: int, db: Session = Depends(get_db)):
    
    # Try Redis first
    cached_file_path = r.get(f"user_file:{user_id}")

    if cached_file_path:
        print("Found in Cache")
        return {
            "id": user_id,
            "file_path": cached_file_path,
            "Found in" : "cache"
        }
    #Fall back to db
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user :
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store in Redis for next time
    print("Found in DB")
    r.set(f"user_file:{user_id}", db_user.file_path)
    return db_user





@router.post("/upload-image-redis/")
async def upload_image(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image type")

    image_id = str(uuid.uuid4())
    
    # Define a temporary file path
    temp_file_path = f"/tmp/{image_id}_{file.filename}"

    # Save the file temporarily to disk
    try:
        with open(temp_file_path, "wb") as buffer:
            while content := await file.read(1024):
                buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

    # Store initial status in Redis
    r.set(f"image_status:{image_id}", "uploaded")

    # Enqueue the background processing task
    # This is a non-blocking operation for the API endpoint
    q.enqueue(process_image_task, image_id, temp_file_path)

    return {"image_id": image_id, "status": "processing_queued", "filename": file.filename}

# Endpoint to check the status (optional but useful)
@router.get("/status/{image_id}")
def get_status(image_id: str):
    status = r.get(f"image_status:{image_id}")
    if status is None:
        return {"image_id": image_id, "status": "not_found"}
    return {"image_id": image_id, "status": status.decode('utf-8')}
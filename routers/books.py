from fastapi import HTTPException, status, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import schemas
import models
from database import get_db


router = APIRouter(
    prefix="/books",
    tags=["books"]
)

# Step 3a: GET ALL - Query database for all books
@router.get("/", response_model=List[schemas.BookRead])
async def get_all_books(db: AsyncSession = Depends(get_db)):
    # Execute SELECT query to fetch all books from database
    result = await db.execute(select(models.Book))
    books = result.scalars().all()
    if not books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No books found")
    return books


# Step 3b: GET ONE - Query database by UUID
@router.get("/{book_uid}", response_model=schemas.BookRead)
async def get_book_by_id(book_uid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Execute SELECT query with WHERE clause to find specific book
    result = await db.execute(select(models.Book).where(models.Book.uid == book_uid))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book

# Step 3c: CREATE - Insert new book into database
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.BookRead)
async def create_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    # Create new Book model instance from request data
    new_book = models.Book(**book.model_dump())
    # Add to database session
    db.add(new_book)
    # Commit transaction to save to database
    await db.commit()
    # Refresh to get auto-generated fields (uid, timestamps)
    await db.refresh(new_book)
    return new_book

# Step 3d: UPDATE - Modify existing book in database
@router.patch("/{book_uid}", response_model=schemas.BookRead)
async def patch_book(book_uid: uuid.UUID, book: schemas.BookUpdate, db: AsyncSession = Depends(get_db)):
    # Find the book in database
    result = await db.execute(select(models.Book).where(models.Book.uid == book_uid))
    stored_book = result.scalar_one_or_none()
    
    if not stored_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Get only fields that were provided in the request
    update_data = book.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )
    
    # Update each field on the database model
    for field, value in update_data.items():
        setattr(stored_book, field, value)
    
    # Commit changes to database
    await db.commit()
    # Refresh to get updated timestamp
    await db.refresh(stored_book)
    return stored_book

# Step 3e: DELETE - Remove book from database
@router.delete("/{book_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_uid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Find the book in database
    result = await db.execute(select(models.Book).where(models.Book.uid == book_uid))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    # Delete from database
    await db.delete(book)
    # Commit the deletion
    await db.commit()
    return None


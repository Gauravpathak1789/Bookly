from fastapi import HTTPException, status, APIRouter, Depends
from typing import List
import schemas
import book_data
from database import get_db


router = APIRouter(
    prefix="/books",
    tags=["books"]
)


books=book_data.books

@router.get("/",response_model=List[schemas.BookRead])
async def get_all_books():
    if not books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No books found")
    return books

@router.get("/{book_id}",response_model=schemas.BookRead)
async def get_book_by_id(book_id: int):
    for book in books:
        if book["id"] == book_id:
            return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")


@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_book(book: schemas.BookCreate):
    for b in books:
        if b["id"] == book.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book with this ID already exists")
    new_book = book.dict()
    books.append(new_book)
    return new_book


@router.patch("/{book_id}",response_model=schemas.BookRead)
async def patch_book(book_id: int, book:schemas.BookUpdate):
    for stored_book in books:
        if stored_book["id"] == book_id:
            update_data = book.dict(exclude_unset=True)

            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields provided for update"
                )

            stored_book.update(update_data)
            return stored_book

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Book not found"
    )

@router.delete("/{book_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int):
    for index, book in enumerate(books):
        if book["id"] == book_id:
            del books[index]
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")


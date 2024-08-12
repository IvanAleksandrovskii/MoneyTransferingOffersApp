from typing import List
from uuid import UUID

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core import logger
from core.models import db_helper, Currency, Country, Document
from core.schemas import CurrencyResponse, CountryResponse, DocumentResponse

router = APIRouter()


@router.get("/currency/{currency_id}", response_model=CurrencyResponse, tags=["Global Objects"])
async def get_currency(
        currency_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    query = Currency.active().where(Currency.id == currency_id)
    try:
        result = await session.execute(query)
        currency = result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_currency: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return CurrencyResponse.model_validate(currency)


@router.get("/currencies", response_model=List[CurrencyResponse], tags=["Global Objects"])
async def get_all_currencies(session: AsyncSession = Depends(db_helper.session_getter)):
    query = Currency.active()
    try:
        result = await session.execute(query)
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_all_currencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    currencies = result.scalars().all()
    return [CurrencyResponse.model_validate(currency) for currency in currencies]


@router.get("/country/{country_id}", response_model=CountryResponse, tags=["Global Objects"])
async def get_country(
        country_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    query = (
        Country.active()
        .options(joinedload(Country.local_currency))
        .where(Country.id == country_id)
    )
    try:
        result = await session.execute(query)
        country = result.unique().scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_country: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    return CountryResponse.model_validate(country)


@router.get("/countries", response_model=List[CountryResponse], tags=["Global Objects"])
async def get_all_countries(session: AsyncSession = Depends(db_helper.session_getter)):
    query = (
        Country.active()
        .options(joinedload(Country.local_currency))
    )
    try:
        result = await session.execute(query)
        countries = result.unique().scalars().all()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_all_countries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [CountryResponse.model_validate(country) for country in countries]


@router.get("/document/{document_id}", response_model=DocumentResponse, tags=["Global Objects"])
async def get_document(
        document_id: UUID,
        session: AsyncSession = Depends(db_helper.session_getter)
):
    query = Document.active().where(Document.id == document_id)

    try:
        result = await session.execute(query)
        document = result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(id=document.id, name=document.name)


@router.get("/documents", response_model=List[DocumentResponse], tags=["Global Objects"])
async def get_all_documents(session: AsyncSession = Depends(db_helper.session_getter)):
    query = Document.active()
    try:
        result = await session.execute(query)
        documents = result.scalars().all()
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error occurred in get_all_documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [DocumentResponse(id=doc.id, name=doc.name) for doc in documents]

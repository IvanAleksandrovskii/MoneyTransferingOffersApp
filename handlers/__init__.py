from aiogram import Router


router = Router()


from .on_start import router as on_start_router
router.include_router(on_start_router)

from aiogram import Router


router = Router()


from .on_start import router as on_start_router
router.include_router(on_start_router)

from .universal_page import router as universal_page_router
router.include_router(universal_page_router)

from .admin import router as admin_router 
router.include_router(admin_router)

from .reader import router as reader_router
router.include_router(reader_router)

from .direct_broadcast import router as direct_broadcast_router
router.include_router(direct_broadcast_router)

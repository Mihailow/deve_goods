from aiogram.dispatcher.filters.state import StatesGroup, State

class MyStates(StatesGroup):
    increaseBalance = State()
    adminChangeNameProduct = State()
    adminChangeDescProduct = State()
    adminChangePriceProduct = State()

    adminAddProductDataUniqueP = State()
    adminAddProductDataNonuniqueP = State()
    adminAddProductDataUniqueF = State()
    adminAddProductDataNonuniqueF = State()
    adminAddProductDataService = State()
    adminAddProductDataUniqueGift = State()
    adminAddProductDataNonuniqueGift = State()

    adminDeleteProductData = State()

    activateCoupon = State()

    CreateNewProductSelectName = State()
    CreateNewProductSelectDesc = State()
    CreateNewProductSelectPrice = State()
    CreateNewProductSelectImage = State()

    searchByID = State()
    searchByName = State()

    new_mailing_state = State()
    add_text = State()
    add_media_state = State()
    change_media_state = State()

    find_order = State()

    new_mailing_state = State()
    add_text_state = State()
    add_media_state = State()
    change_text_state = State()

    refund_order_state = State()

    find_user_by_ID_state = State()
    find_user_by_USERNAME_state = State()
    find_user_by_TELEGRAM_ID_state = State()
    send_message_from_admin_state = State()

    promo_code_during_purchase_state = State()

    product_count_state = State()
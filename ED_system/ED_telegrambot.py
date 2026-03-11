RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m'

# Import aiogram library
try:
    from aiogram import Bot, types, Router, exceptions
    from aiogram.fsm.context import FSMContext
    from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
except ModuleNotFoundError:
    print(f"{RED}Please, install aiogram!{RESET}")
    exit()

# Import asyncio for running bot and keeping track of the time.
try:
    import asyncio
except ModuleNotFoundError:
    print(f"{RED}Please, install asyncio!{RESET}")
    exit()

try:
    import random
except ModuleNotFoundError:
    print(f"{RED}Please, install random!{RESET}")
    exit()

try:
    import aiohttp
except ModuleNotFoundError:
    print(f"{RED}Please, install aiohttp!{RESET}")
    exit()

try:
    from ED_Maintools import *
    userstable = Users_Table()
    homeworktable = Homework_Table()
except ModuleNotFoundError:
    print(f"{RED}Please, install full ED system! [ED_Maintools]{RESET}")
    exit()

cancel_button = [types.InlineKeyboardButton(text=texts_dict["cancel_text"], callback_data="cancel")] # list
support_button = [types.InlineKeyboardButton(text=texts_dict["support_text"], callback_data="support")] # list

bot = Bot(token=TOKEN)
router = Router()

def update_texts_dict_tgbot():
    global texts_dict
    texts_dict = get_texts()

async def errors_handler(error: types.ErrorEvent, state: FSMContext):
    if error.update.message:
        user_id = error.update.message.from_user.id
        event = False
    elif error.update.callback_query:
        user_id = error.update.callback_query.from_user.id
        event = error.update.callback_query.data
    else: user_id = "Error while getting user id"

    bot_state = await state.get_data()
    try: bot_state = str(bot_state["bot_state"])
    except KeyError:
        bot_state = None
        await state.update_data(bot_state = None)

    print(f"{RED}Error ({current_time()}): {error.exception}; user id = {user_id}, bot_state = {bot_state}{(', callback = ' + str(event)) * (event != False)}{RESET}")
    
    for dev_id in get_developers_id(userstable.users_table, user_id, remove_self = False):
        if int(get_userconfig(dev_id, "notify_err")) == 0: continue
        try: await bot.send_message(
            chat_id=dev_id,
            text=f"{texts_dict['error_found']}\n<b>Time</b>: {current_time()}\n<b>Error</b>: {error.exception}\n" + \
                f"<b>User id</b>: {user_id}\n<b>Bot state</b>: {bot_state}\n{'<b>Callback</b>: ' + str(event)}",
            parse_mode="HTML"
            )
        except exceptions.TelegramForbiddenError:
            userstable.delete_user(dev_id, notify=False)
        except: pass

    try: await bot.send_message(chat_id=user_id, text=texts_dict["sth_gone_wrong"], parse_mode="HTML")
    except exceptions.TelegramForbiddenError:
        userstable.delete_user(user_id, notify=False)
    except: pass

router.errors.register(errors_handler)

# Message handler
@router.message()
async def message_handler(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    tgusername = message.from_user.username

    data = await state.get_data()
    if "bot_state" not in data: await state.update_data(bot_state = None)

    data = await state.get_data()
    bot_state = str(data["bot_state"])
    usercategory = get_usercategory(user_id, userstable, message.from_user.full_name)

    bt = Buttons(user_id)
    
    if "&&&&" in bot_state: # after '&&&&' follows message id to delete
        try: await bot.delete_message(chat_id=user_id, message_id=int(bot_state.split("&&&&")[-1]))
        except: pass
        bot_state = bot_state.split("&&&&")[0]

    try: userstable.set_time(user_id, notify=False)
    except: pass
    
    await asyncio.sleep(delay_time())

    if message.text or message.pinned_message: pass
    else:
        if bot_state != "addingdocnotify" and bot_state[:13] != "adding_doc_hw" and bot_state != "None":
            await message.reply(texts_dict["plz_send_me_a_text_text"], parse_mode="HTML")
            return 0

        if message.document: file_id = message.document.file_id
        elif message.photo: file_id = message.photo[-1].file_id
        elif message.video: file_id = message.video.file_id
        elif message.voice: file_id = message.voice.file_id
        else: return 0

        file_info = await bot.get_file(file_id)
        file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}'

        if bot_state[:13] == "adding_doc_hw":
            subject = bot_state.split("!")[-2]
            date = bot_state.split("!")[-1]
            filename = f'{get_homework_docs_dirpath()}/{subject}_{date}'

            homework = homeworktable.get_homework(subject, date)
            if homework[1] == False: homework[1] = []
            
            if "." in file_info.file_path:
                filename = f"{filename}_{len(homework[1]) + 1}.{file_info.file_path.split('.')[-1]}"
            else:
                filename = f"{filename}_{len(homework[1]) + 1}"

            if len(homework[1]) <= int(get_config("system", "docs_hw_limit")):

                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as response:
                        fdata = await response.read()
                            
                        with open(filename, 'wb') as f:
                            f.write(fdata)
                
                if len(homework[1]) != 0: old_files = '&&&'.join(homework[1]) + "&&&"
                else: old_files = ""

                homeworktable.add_homework(subject, homework[0], 
                    filepath=f"{old_files}{filename}", notify=False)
                
                await state.update_data(bot_state = None)
                last_photo_button = [
                    [types.InlineKeyboardButton(text=texts_dict["add_more_docs"], callback_data=f"add_doc_hw!{subject}!{date}")]
                ]
                last_photo_keyboard = types.InlineKeyboardMarkup(inline_keyboard=last_photo_button)
                await message.reply(texts_dict["document_added_text"] + " " + texts_dict["can_add_more"], reply_markup=last_photo_keyboard)

            else: await message.reply(texts_dict["doc_limit_reached"])

        elif bot_state == "addingdocnotify":
            filename = f"{get_system_docs_dirpath()}/notify_document.{file_info.file_path.split('.')[-1]}"

            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    fdata = await response.read()
                        
                    with open(filename, 'wb') as f:
                        f.write(fdata)
            
            await state.update_data(bot_state = None)

            cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
            msg = await message.reply(f"{texts_dict['document_added_text']}\n{texts_dict['enter_message_text']}",
                    reply_markup=cancel_keyboard)
            await state.update_data(bot_state = f"notifying_all_users_entering_msg&&&&{msg.message_id}")
        
        return 0

    message_text = str(message.text)

    if usercategory == "Ban": await message.answer(texts_dict["ur_banned_text"])

    elif len(message_text) > int(get_config("system", "input_text_limit")):
        await message.answer(texts_dict["too_huge_text"])

    elif message_text == None: pass

    elif message_text == bt.start_button:
        await state.update_data(bot_state = None)
        username = get_username(userstable, user_id, message.from_user.full_name)

        # Create buttons for the main keyboard
        bt.__init__(user_id)

        button_row_1 = [
            KeyboardButton(text=bt.homework_button)
        ]
        button_row_3 = [
            KeyboardButton(text=bt.start_button),
            KeyboardButton(text=bt.settings_button)
        ]
            
        if usercategory in ["Dev", "MAdm"]:
            button_row_2 = [
                KeyboardButton(text=bt.lessonshedule_button),
                KeyboardButton(text=bt.management_button)
            ]
        else:
            button_row_2 = [
                KeyboardButton(text=bt.lessonshedule_button)
            ]
        main_keyboard = ReplyKeyboardMarkup(
            keyboard=[button_row_1, button_row_2, button_row_3],
            resize_keyboard=True
        )
        try: await message.answer(greetings(username), reply_markup=main_keyboard, parse_mode="HTML")
        except: await message.answer(greetings(username), reply_markup=main_keyboard)
    
    elif message_text == bt.homework_button:
        await state.update_data(bot_state = None)
        homeworktable.__init__()
        hw_msg = homework_message(homeworktable.operat_table)
        try: homewrk_list_limit = int(get_config("system", "homewrk_list_limit"))
        except: homewrk_list_limit = 40

        homework_buttons = []
        for subj in hw_msg[1]:
            homework_buttons += [
                [types.InlineKeyboardButton(text=hw_msg[1][subj]["text"],
                callback_data=hw_msg[1][subj]["callback"])]
            ]
        if len(homework_buttons) > homewrk_list_limit:
            homework_buttons = homework_buttons[:homewrk_list_limit]
            homework_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data="next_hwpage-1")]
            ]
        update_hw_button = [types.InlineKeyboardButton(text=texts_dict["update_text"], callback_data="update_homework_list")]
        homework_buttons += [update_hw_button]
        homework_keyboard = types.InlineKeyboardMarkup(inline_keyboard=homework_buttons)

        await message.answer(hw_msg[0], reply_markup=homework_keyboard, parse_mode="HTML")
    
    elif message_text == bt.lessonshedule_button:
        await state.update_data(bot_state = None)

        lessonshedule_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["monday"], callback_data="get_ls!monday")],
            [types.InlineKeyboardButton(text=texts_dict["tuesday"], callback_data="get_ls!tuesday")],
            [types.InlineKeyboardButton(text=texts_dict["wednesday"], callback_data="get_ls!wednesday")],
            [types.InlineKeyboardButton(text=texts_dict["thursday"], callback_data="get_ls!thursday")],
            [types.InlineKeyboardButton(text=texts_dict["friday"], callback_data="get_ls!friday")],
            [types.InlineKeyboardButton(text=texts_dict["all_days_ls"], callback_data="all_days_ls")]
        ]
        lessonshedule_keyboard = types.InlineKeyboardMarkup(inline_keyboard=lessonshedule_buttons)

        await message.answer(texts_dict["choose_day_text"], reply_markup=lessonshedule_keyboard)

    elif message_text == bt.settings_button:
        await state.update_data(bot_state = None)
        username = get_username(userstable, user_id, message.from_user.full_name)

        settings_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["change_username_text"], callback_data="change_name")],
            [types.InlineKeyboardButton(text=texts_dict["change_usercategory_text"], callback_data="change_category")],
            [types.InlineKeyboardButton(text=texts_dict["change_mainkeyboard_text"], callback_data="edit_main_keyboard")],
            [types.InlineKeyboardButton(text=texts_dict["notifications_text"], callback_data="config_notify!f!f")]
        ]
        if usercategory != "Dev": settings_buttons += [support_button]
        settings_keyboard = types.InlineKeyboardMarkup(inline_keyboard=settings_buttons)

        try: await message.answer(settings_message(user_id, username, usercategory, tgusername), \
                parse_mode="HTML", reply_markup=settings_keyboard)
        except: await message.answer(settings_message(user_id, username, usercategory, tgusername), \
                reply_markup=settings_keyboard)
    
    elif message_text == bt.management_button and usercategory in ["Dev", "MAdm"]:
        await state.update_data(bot_state = None)

        management_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["statistics"], callback_data="statistics")],
            [types.InlineKeyboardButton(text=texts_dict["all_users_notify"], callback_data="notify_all_users")],
            [types.InlineKeyboardButton(text=texts_dict["userdata"], callback_data="usersdata")]
        ]
        if usercategory in ["Dev"]:
            management_buttons += [[types.InlineKeyboardButton(text=texts_dict["system_text"], callback_data="system_contol_enter_password")]]
        
        management_keyboard = types.InlineKeyboardMarkup(inline_keyboard=management_buttons)

        await message.answer(texts_dict["management_func_text"], reply_markup=management_keyboard, parse_mode="HTML")

    else:
        if bot_state == "changing_username":
            new_username = message_text
            userstable.edit_value(user_id, "username", new_username, _abc_ascii = True, notify=False)
            await state.update_data(bot_state = None)
            await message.reply(texts_dict["username_changed_text"])
        
        elif bot_state == "editing_hw_b":
            bt.change_button_text("homework_button", message_text)
            await state.update_data(bot_state = None)
            await message.reply(texts_dict["button_text_updated"])

        elif bot_state == "editing_ls_b":
            bt.change_button_text("lessonshedule_button", message_text)
            await state.update_data(bot_state = None)
            await message.reply(texts_dict["button_text_updated"])

        elif bot_state == "editing_set_b":
            bt.change_button_text("settings_button", message_text)
            await state.update_data(bot_state = None)
            await message.reply(texts_dict["button_text_updated"])

        elif bot_state == "editing_mt_b":
            bt.change_button_text("management_button", message_text)
            await state.update_data(bot_state = None)
            await message.reply(texts_dict["button_text_updated"])

        elif "entering_password_edit_category" in bot_state:
            try: await message.delete()
            except:pass
            
            password1 = get_config("system", "password1")

            if message_text == password1:
                select_category_buttons = [
                    [types.InlineKeyboardButton(text=texts_dict["short_descriptiondev"], callback_data="edit_category_passw!Dev")],
                    [types.InlineKeyboardButton(text=texts_dict["short_descriptionmadm"], callback_data="edit_category_passw!MAdm")],
                    [types.InlineKeyboardButton(text=texts_dict["short_descriptionadm"], callback_data="edit_category_passw!Adm")],
                    [types.InlineKeyboardButton(text=texts_dict["short_descriptionaver"], callback_data="edit_category_passw!Aver")],
                    [types.InlineKeyboardButton(text=texts_dict["short_descriptionban"], callback_data="edit_category_passw!Ban")]
                ]
                select_category_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_category_buttons)

                await message.answer(texts_dict["which_category_u_want"], reply_markup=select_category_keyboard)
            else:
                await message.answer(texts_dict["wrong_password"])

        elif "entering_password_system_contol" in bot_state:
            try: await message.delete()
            except:pass
            
            password1 = get_config("system", "password1")

            if message_text == password1:
                select_category_buttons = [
                    [types.InlineKeyboardButton(text=texts_dict["edit_mainconfigs"], callback_data="edit_mainconfigs")],
                    [types.InlineKeyboardButton(text=texts_dict["check_system"], callback_data="check_system")],
                    [types.InlineKeyboardButton(text=texts_dict["sql_query"], callback_data="sql_query")],
                    [types.InlineKeyboardButton(text=texts_dict["exit_system"], callback_data="exit_system")],
                    ]
                select_category_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_category_buttons)
                
                username = get_username(userstable, user_id, message.from_user.full_name)
                await message.answer(system_greetings(username), reply_markup=select_category_keyboard, parse_mode="HTML")
                await state.update_data(bot_state = f"working_with_system")
            else:
                await message.answer(texts_dict["wrong_password"])

        elif bot_state == "asking_support_entering_question":
            await state.update_data(bot_state = None)

            support_request_buttons = [
                [types.InlineKeyboardButton(text=texts_dict["answer_text"], callback_data=f"answer_request!{user_id}"),
                types.InlineKeyboardButton(text=texts_dict["ignore_text"], callback_data="ignore_request")]
            ]
            support_request_keyboard = types.InlineKeyboardMarkup(inline_keyboard=support_request_buttons)

            username = get_username(userstable, user_id, message.from_user.full_name)
            dev_list = []
            for devid in get_developers_id(userstable.users_table, user_id):
                if get_userconfig(devid, "notify_sup") != "0": dev_list.append(int(devid))
            try: devid = random.choice(dev_list)
            except: devid = get_config("system", "developer_id")
            try: await bot.send_message(chat_id=devid, \
                    text = asking_support_message(user_id, username,  tgusername, message_text), \
                    parse_mode="HTML", reply_markup=support_request_keyboard)
            except exceptions.TelegramForbiddenError:
                userstable.delete_user(devid, notify=False)
            except: await bot.send_message(chat_id=devid, \
                        text = asking_support_message(user_id, username,  tgusername, message_text), \
                        reply_markup=support_request_keyboard)
                
            await message.answer(texts_dict["request_will_be_reviewed"])

        elif bot_state[:21] == "answering_sup_request":
            await state.update_data(bot_state = None)
            username = get_username(userstable, user_id, message.from_user.full_name)
            chatid = bot_state.split("!")[-1]
            try:await bot.send_message(chat_id=chatid, \
                text=support_answer(message_text, username), parse_mode="HTML")
            except exceptions.TelegramForbiddenError:
                userstable.delete_user(chatid, notify=False)
            await message.answer(texts_dict["ur_answer_sent_text"])

        elif bot_state[:19] == "editing_userconfigs":
            await state.update_data(bot_state = None)
            userid = bot_state.split("!")[-1]
            parameter = bot_state.split("!")[-2]
            old_config = get_userconfig(userid, parameter)

            await message.answer(edit_userparameter_value(userid, parameter, message_text), parse_mode="HTML")

            username = get_username(userstable, user_id, message.from_user.full_name)
            msg_text = userconfigs_edited_message(username, userid, parameter, message_text, old_config)

            try:
                await bot.send_message(
                    userid, text=f"{texts_dict['sets_edited_by_creator']} ({parameter}).\n{texts_dict['press_start_to_update'] * int(not 'notify' in parameter)}",
                    parse_mode="HTML")
            except exceptions.TelegramForbiddenError:
                userstable.delete_user(creatorid, notify=False)
            except: pass    

            for creatorid in get_developers_id(userstable.users_table, user_id).union(get_main_admins_id(userstable.users_table, user_id)):
                if int(get_userconfig(creatorid, "notify_ude")) == 0: continue
                try:
                    await bot.send_message(creatorid, msg_text, parse_mode="HTML")
                except exceptions.TelegramForbiddenError:
                    userstable.delete_user(creatorid, notify=False)
                except: pass

        elif bot_state[:16] == "editing_username":
            userid = bot_state.split("!")[-1]
            username = get_username(userstable, user_id, message.from_user.full_name)

            userstable.edit_value(userid, "username", message_text, _abc_ascii = True, notify=False)
            await state.update_data(bot_state = None)
            try: await bot.send_message(userid, text=f"{texts_dict['name_edited_by_creator']}\n{texts_dict['press_start_to_update']}")
            except exceptions.TelegramForbiddenError:
                userstable.delete_user(userid, notify=False)
            await message.reply(texts_dict["username_changed_text"])

            for creatorid in get_developers_id(userstable.users_table, user_id).union(get_main_admins_id(userstable.users_table, user_id)):
                if int(get_userconfig(creatorid, "notify_ude")) == 0: continue
                try:
                    await bot.send_message(creatorid, userdata_edited_message(
                        username, userid, "username", message_text, username), parse_mode="HTML")
                except exceptions.TelegramForbiddenError:
                    userstable.delete_user(creatorid, notify=False)
                except: pass

        elif bot_state == "userdata_entering_id":
            userid = message_text

            if userid in list(userstable.users_table.index):
                    userinfo_buttons = [
                        [types.InlineKeyboardButton(text=texts_dict["category_parpadezsh"], callback_data=f"edit_usercategory!{userid}"),
                        types.InlineKeyboardButton(text=texts_dict["name_parpadezsh"], callback_data=f"edit_username!{userid}")],
                        [types.InlineKeyboardButton(text=texts_dict["edit_userconfigs"], callback_data=f"edit_userconfigs!{userid}")],
                        [types.InlineKeyboardButton(text=texts_dict["notify_user"], callback_data=f"notify_user!{userid}")],
                        [types.InlineKeyboardButton(text=texts_dict["delete_user"], callback_data=f"deleteuser!{userid}")],
                        cancel_button
                    ]
                    userinfo_keyboard = types.InlineKeyboardMarkup(inline_keyboard=userinfo_buttons)

                    try:await message.answer(user_info(userid, userstable.users_table), parse_mode="HTML", \
                            reply_markup=userinfo_keyboard)
                    except:await message.answer(user_info(userid, userstable.users_table), \
                            reply_markup=userinfo_keyboard)
            else: 
                await message.answer(texts_dict["user_not_found"], parse_mode="HTML")

        elif bot_state[:28] == "entering_message_notify_user":
            await state.update_data(bot_state = None)
            username = get_username(userstable, user_id, message.from_user.full_name)
            try:
                chatid = bot_state.split("!")[-1]
                await bot.send_message(chat_id=chatid, text=message_for_user(message_text, username), \
                    parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[support_button]))
                await message.answer(texts_dict["message_sent_text"])
            except exceptions.TelegramForbiddenError:
                userstable.delete_user(chatid, notify=False)
            except:
                await message.answer(texts_dict["send_message_error"])

        elif bot_state[:30] == "entering_mainconfigs_parameter":
            await state.update_data(bot_state = None)
            section = bot_state.split("!!")[-2]
            parameter = bot_state.split("!!")[-1]
            old_config = get_config(section, parameter)

            await message.answer(edit_parameter_value(section, parameter, message_text), parse_mode="HTML")

            username = get_username(userstable, user_id, message.from_user.full_name)
            msg_text = mainconfigs_edited_message(username, section, parameter, message_text, old_config)
            for creatorid in get_developers_id(userstable.users_table, user_id):
                if int(get_userconfig(creatorid, "notify_mce")) == 0: continue
                try: await bot.send_message(creatorid, msg_text, parse_mode="HTML")
                except exceptions.TelegramForbiddenError:
                    userstable.delete_user(user, notify=False)
                except: pass
        
        elif bot_state == "notifying_all_users_entering_msg":
            userstable.__init__()
            folderpath = get_system_docs_dirpath()
            username = get_username(userstable, user_id, message.from_user.full_name)
            notify_text = global_notify(message_text, username)
            list_of_files_full = get_files_from_dir(folderpath)
            list_of_files = list(map(lambda s: s.split(".")[0], list_of_files_full))

            if "notify_document" in list_of_files:
                doctype = list_of_files_full[list_of_files.index('notify_document')].split(".")[-1]
                filepath = f"{folderpath}/notify_document.{doctype}"

                ucnt = 0
                for user in userstable.users_table.index:
                    if int(get_userconfig(user, "notify_aun")) == 0: continue
                    try:
                        try:
                            if doctype in ["png", "jpg"]: msg = await bot.send_photo(chat_id=user, photo=FSInputFile(filepath),
                                                                caption=notify_text, parse_mode="HTML")
                            elif doctype in ["mp4"]: msg = await bot.send_video(chat_id=user, video=FSInputFile(filepath),
                                                                caption=notify_text, parse_mode="HTML")
                            elif doctype in ["ogg"]: msg = await bot.send_voice(chat_id=user, voice=FSInputFile(filepath),
                                                                caption=notify_text, parse_mode="HTML")
                            else: msg = await bot.send_document(chat_id=user, document=FSInputFile(filepath),
                                                                caption=notify_text, parse_mode="HTML")
                        
                        except: msg = await bot.send_message(chat_id=user,
                            text=notify_text, parse_mode="HTML")
                        await bot.pin_chat_message(chat_id=user, message_id=msg.message_id)
                        await asyncio.sleep(delay_time())
                        ucnt += 1
                    except Exception as e:
                        userstable.delete_user(user, notify=False)
                
                try: remove_file(filepath)
                except: pass
            
            else:
                ucnt = 0
                for user in userstable.users_table.index:
                    if int(get_userconfig(user, "notify_aun")) == 0: continue
                    try:
                        msg = await bot.send_message(chat_id=user,
                            text=notify_text, parse_mode="HTML")
                        await bot.pin_chat_message(chat_id=user, message_id=msg.message_id)
                        await asyncio.sleep(0.5)
                        ucnt += 1
                    except:
                        userstable.delete_user(user, notify=False)
                        
            try: userstable.delete_user(bot.id, notify=False)
            except: pass

            await message.answer(f"{texts_dict['notify_sent_text']} ({ucnt})")
            await state.update_data(bot_state = None)

        elif bot_state[:17] == "entering_homework":
            await state.update_data(bot_state = None)
            subject = bot_state.split("!")[-2]
            date = bot_state.split("!")[-1]

            homeworktable.add_homework(subject, message_text, _abc_ascii=True, date=date, notify=False)
                
            edit_hw_button = [
                [types.InlineKeyboardButton(text=texts_dict["edit_hw"], callback_data=f"add_homeworktask!{subject}!{current_day()}"),
                types.InlineKeyboardButton(text=texts_dict["delete_hw"], callback_data=f"delete_homeworktask!{subject}!{current_day()}")],
                [types.InlineKeyboardButton(text=texts_dict["add_document_hw"], callback_data=f"add_doc_hw!{subject}!{current_day()}")]
            ]
            edit_hw_keyboard = types.InlineKeyboardMarkup(inline_keyboard=edit_hw_button)
            await message.reply(texts_dict["hw_added_text"], reply_markup=edit_hw_keyboard)
        
        elif bot_state == "addingdocnotify":
            await message.reply(texts_dict["plz_send_me_a_document_text"], parse_mode="HTML")

        elif bot_state[:13] == "adding_doc_hw":
            await message.reply(texts_dict["plz_send_me_a_document_text"], parse_mode="HTML")

        elif bot_state[:15] == "entering_new_ls":
            await state.update_data(bot_state = None)
            day = bot_state.split("!")[-1]
            await message.answer(edit_lesson_shedule(day, message_text))
        
        elif bot_state[:16] == "making_sql_query":
            try:
                userstable.__init__()
                homeworktable.__init__()
                table = userstable.users_table if bot_state.split("!")[-1] == "users_csv" else homeworktable.operat_table
                sql_query(table, message_text, file = True)

                folderpath = get_system_docs_dirpath()
                filepath = f"{folderpath}/SQL_query.csv"
                await bot.send_document(user_id, FSInputFile(filepath))
                remove_file(filepath)

                await state.update_data(bot_state = None)
            except Exception as e:
                await message.answer(texts_dict["error_sql_query"] + " " + str(e), parse_mode="HTML")

        else: pass

# Callback handler
@router.callback_query()
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
    callback_data = str(callback.data)
    user_id = str(callback.from_user.id)
    tgusername = callback.from_user.username

    data = await state.get_data()
    if "bot_state" not in data: await state.update_data(bot_state = None)
    
    data = await state.get_data()
    bot_state = str(data["bot_state"])
    usercategory = get_usercategory(user_id, userstable, callback.from_user.full_name)

    bt = Buttons(user_id)

    if "&&&&" in bot_state: # after '&&&&' follows message id to delete
        try: await bot.delete_message(chat_id=user_id, message_id=int(bot_state.split("&&&&")[-1]))
        except: pass
        bot_state = bot_state.split("&&&&")[0]
    
    try: userstable.set_time(user_id, notify=False)
    except: pass
    
    await asyncio.sleep(delay_time())

    if usercategory == "Ban": await callback.message.answer(texts_dict["ur_banned_text"])

    elif callback_data == "change_name":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(texts_dict["enter_username_text"], reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"changing_username&&&&{msg.message_id}")
    
    elif callback_data == "edit_main_keyboard":
        buttons_msg_buttons = [
            [types.InlineKeyboardButton(text=bt.homework_button, callback_data="edit_hw_b")],
            [types.InlineKeyboardButton(text=bt.lessonshedule_button, callback_data="edit_ls_b")],
            [types.InlineKeyboardButton(text=bt.settings_button, callback_data="edit_set_b")]
        ]
        if usercategory in ["Dev", "MAdm"]:
            buttons_msg_buttons.append([types.InlineKeyboardButton(text=bt.management_button, callback_data="edit_mt_b")])
        
        buttons_msg_buttons.append([types.InlineKeyboardButton(text=texts_dict["set_stock_sets"], callback_data="set_stock_buttons")])
        buttons_msg_buttons.append([types.InlineKeyboardButton(text=texts_dict["back_to_sets"], callback_data="back_to_settings")])
        buttons_msg_keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons_msg_buttons)
        
        await state.update_data(bot_state = "editing_main_keyboard")
        try: await callback.message.edit_text(texts_dict["change_b_text"], reply_markup=buttons_msg_keyboard)
        except: await callback.message.answer(texts_dict["change_b_text"], reply_markup=buttons_msg_keyboard)
    
    elif callback_data == "cancel" and bot_state != None:
        await state.update_data(bot_state = None)
        try: await callback.message.delete()
        except: pass
        await callback.answer(texts_dict["operation_canceled_text"])

    elif callback_data == "edit_hw_b":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(f"{texts_dict['enter_button_text']}\n({bt.homework_button})", reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"editing_hw_b&&&&{msg.message_id}")
    
    elif callback_data == "edit_ls_b":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(f"{texts_dict['enter_button_text']}\n({bt.lessonshedule_button})", reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"editing_ls_b&&&&{msg.message_id}")

    elif callback_data == "edit_set_b":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(f"{texts_dict['enter_button_text']}\n({bt.settings_button})", reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"editing_set_b&&&&{msg.message_id}")
    
    elif callback_data == "edit_mt_b" and usercategory in ["Dev", "MAdm"]:
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(f"{texts_dict['enter_button_text']}\n({bt.management_button})", reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"editing_mt_b&&&&{msg.message_id}")
    
    elif callback_data == "set_stock_buttons":
        await callback.message.answer(set_stock_buttons(user_id))
        await state.update_data(bot_state = None)

    elif callback_data == "exit_system":
        await state.update_data(bot_state = None)
        try: await callback.message.edit_reply_markup(reply_markup=None)
        except: pass
        await callback.answer(texts_dict["exit_system"])

    elif callback_data == "edit_mainconfigs" and usercategory in ["Dev"]:
        await state.update_data(bot_state = "editing_mainconfigs")
        try: sections_list_limit = int(get_config("system", "sections_list_limit"))
        except: sections_list_limit = 40

        select_section_buttons = []
        for section in list(get_configs())[1:]:
            select_section_buttons.append(
                [types.InlineKeyboardButton(text=section, callback_data=f"edit_mainconfigs_section!!{section}")]
            )

        if len(select_section_buttons) > sections_list_limit:
            select_section_buttons = select_section_buttons[:sections_list_limit]
            select_section_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_sectpage-1")]
            ]
                
        select_section_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_section_buttons)
        await callback.message.answer(texts_dict["select_section_text"], reply_markup=select_section_keyboard)

    elif callback_data == "check_system" and usercategory in ["Dev"]:
        print(f"Running data backup ({current_time()})...")
        userstable.__init__()
        homeworktable.__init__()
        update_texts_dict()
        update_texts_dict_tgbot()
        all_files_prepare(notify=False)
        userstable.auto_users_delete(notify=False)
        userstable.data_backup(notify=False)
        homeworktable.data_backup(notify=False)
        homeworktable.remove_unnecessary_homeworks(notify=False)

        await callback.message.answer(texts_dict["system_checked"])

    elif callback_data == "sql_query" and usercategory in ["Dev"]:
        await state.update_data(bot_state = "selecting_table_for_sql_query")
        select_table_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["users_table"], callback_data="sql_query2!users_csv")],
            [types.InlineKeyboardButton(text=texts_dict["homework_table"], callback_data="sql_query2!homework_csv")],
            cancel_button
        ]
        select_table_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_table_buttons)

        await callback.message.answer(texts_dict["select_table_sql"], reply_markup=select_table_keyboard)
    
    elif callback_data[:10] == "sql_query2":
        table = callback_data.split("!")[-1]
        if table == "users_csv":
            msg_text = get_sql_query_message(userstable.users_table, table)
        elif table == "homework_csv":
            msg_text = get_sql_query_message(homeworktable.operat_table, table)
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        try: await callback.message.edit_text(msg_text, reply_markup=cancel_keyboard, parse_mode="HTML")
        except: await callback.message.answer(msg_text, reply_markup=cancel_keyboard, parse_mode="HTML")

        await state.update_data(bot_state = f"making_sql_query!{table}")

    elif callback_data == "change_category":
        await state.update_data(bot_state = "changing_category")
        edit_category_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["enter_password"], callback_data="edit_category_enter_password")]
        ]
        if usercategory not in ["Dev", "MAdm"]: edit_category_buttons.append(
            [types.InlineKeyboardButton(text=texts_dict["ask_sup"], callback_data="edit_category_support")]
        )
        edit_category_buttons.append(cancel_button)
        c_e_keyboard = types.InlineKeyboardMarkup(inline_keyboard=edit_category_buttons)

        await callback.message.answer(texts_dict["choose_way_editing_category"], reply_markup=c_e_keyboard)
    
    elif callback_data in ["edit_category_enter_password", "system_contol_enter_password"]:
        cancel_keyboard = c_e_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        if callback_data == "system_contol_enter_password" and usercategory in ["Dev"]:
            msg = await callback.message.answer(texts_dict["enter_password_text"], reply_markup=cancel_keyboard)
            await state.update_data(bot_state = f"entering_password_system_contol&&&&{msg.message_id}")

        else:
            try: msg = await callback.message.edit_text(texts_dict["enter_password_text"], reply_markup=cancel_keyboard)
            except: msg = await callback.message.answer(texts_dict["enter_password_text"], reply_markup=cancel_keyboard)
            await state.update_data(bot_state = f"entering_password_edit_category&&&&{msg.message_id}")

    elif callback_data == "edit_category_support":
        confirm_support_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["confirm_text"], callback_data="edit_category_confirm_support")],
            cancel_button
        ]
        confirm_support_keyboard = types.InlineKeyboardMarkup(inline_keyboard=confirm_support_buttons)

        await callback.message.edit_text(texts_dict["confirm_ask_sup"], reply_markup=confirm_support_keyboard)
    
    elif callback_data == "edit_category_confirm_support":
        select_category_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["short_descriptiondev"], callback_data="edit_category_sup!Dev")],
            [types.InlineKeyboardButton(text=texts_dict["short_descriptionmadm"], callback_data="edit_category_sup!MAdm")],
            [types.InlineKeyboardButton(text=texts_dict["short_descriptionadm"], callback_data="edit_category_sup!Adm")],
            [types.InlineKeyboardButton(text=texts_dict["short_descriptionaver"], callback_data="edit_category_sup!Aver")],
            [types.InlineKeyboardButton(text=texts_dict["short_descriptionban"], callback_data="edit_category_sup!Ban")]
        ]
        select_category_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_category_buttons)

        try: await callback.message.edit_text(texts_dict["which_category_u_want"], reply_markup=select_category_keyboard)
        except: await callback.message.answer(texts_dict["which_category_u_want"], reply_markup=select_category_keyboard)
    
    elif callback_data[:17] == "edit_category_sup":
        await state.update_data(bot_state = None)
        username = get_username(userstable, user_id, callback.from_user.full_name)

        edit_category_request_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["accept_text"], callback_data=f"edit_category_request_accept!{callback_data.split('!')[1]}!{user_id}"),
            types.InlineKeyboardButton(text=texts_dict["cancel2_text"], callback_data=f"edit_category_request_reject!{user_id}")]
        ]
        request_keyboard = types.InlineKeyboardMarkup(inline_keyboard=edit_category_request_buttons)

        cr_list = []
        for devid in get_developers_id(userstable.users_table, user_id).union(get_main_admins_id(userstable.users_table, user_id)):
            if get_userconfig(devid, "notify_sup") != "0": cr_list.append(int(devid))
        try: creatorid = random.choice(cr_list)
        except: creatorid = get_config("system", "developer_id")
        try:await bot.send_message(chat_id=creatorid, \
            text=support_notify_edit_category(user_id, username, callback_data.split('!')[1], tgusername), \
            parse_mode="HTML", reply_markup=request_keyboard)
        except exceptions.TelegramForbiddenError:
            userstable.delete_user(user_id, notify=False)
        
        try: await callback.message.edit_text(texts_dict["request_sent"])
        except: await callback.message.answer(texts_dict["request_sent"])

    elif callback_data[:28] == "edit_category_request_accept":
        new_category = callback_data.split('!')[1]
        requested_user_id = callback_data.split('!')[2]

        await callback.message.answer(accepted_request_edit_category(
            requested_user_id, userstable, new_category), parse_mode="HTML")
        try: await callback.message.edit_reply_markup(reply_markup=None)
        except: pass
        
        username = get_username(userstable, user_id, callback.from_user.full_name)
        old_category = get_usercategory(requested_user_id, userstable, callback.from_user.full_name)
        msg_text = userdata_edited_message(
                username, requested_user_id, "username", new_category, old_category
            )

        for creatorid in get_developers_id(userstable.users_table, user_id).union(get_main_admins_id(userstable.users_table, user_id)):
            if int(get_userconfig(creatorid, "notify_ude")) == 0: continue
            try: await bot.send_message(creatorid, msg_text, parse_mode="HTML")
            except exceptions.TelegramForbiddenError:
                userstable.delete_user(creatorid, notify=False)

        try:await bot.send_message(chat_id=requested_user_id, \
            text=f"{texts_dict['edit_category_request_accepted']} <u>{new_category}</u> !\n{texts_dict['press_start_to_update']}", \
            parse_mode="HTML")
        except exceptions.TelegramForbiddenError:
            userstable.delete_user(requested_user_id, notify=False)
    
    elif callback_data[:28] == "edit_category_request_reject":
        await callback.message.answer(texts_dict["edit_category_u_canceled_request"])
        try: await callback.message.edit_reply_markup(reply_markup=None)
        except: pass

        chatid = callback_data[-10:]
        try: await bot.send_message(chat_id=chatid, \
            text=texts_dict["edit_category_request_canceled"], \
            parse_mode="HTML")
        except exceptions.TelegramForbiddenError:
            userstable.delete_user(chatid, notify=False)
    
    elif callback_data[:19] == "edit_category_passw":
        new_category = callback_data.split("!")[1]
        await state.update_data(bot_state = None)
        
        msg_text = true_password_edit_category(user_id, userstable, new_category)
        reply_markup = None
            
        try: await callback.message.delete()
        except: pass
        await state.update_data(usercategory = new_category)
        await callback.message.answer(text=msg_text, parse_mode="HTML", reply_markup=reply_markup)

    elif callback_data == "support":
        await state.update_data(bot_state = "asking_support")

        confirm_support_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["confirm_text"], callback_data="confirm_asking_support")],
            cancel_button
        ]
        confirm_support_keyboard = types.InlineKeyboardMarkup(inline_keyboard=confirm_support_buttons)

        await callback.message.answer(texts_dict["confirm_ask_sup"], reply_markup=confirm_support_keyboard)

    elif callback_data == "confirm_asking_support":
        try: msg = await callback.message.edit_text(texts_dict["enter_ur_question_text"])
        except: msg = await callback.message.answer(texts_dict["enter_ur_question_text"])
        await state.update_data(bot_state = f"asking_support_entering_question&&&&{msg.message_id}")

    elif callback_data[:14] == "answer_request":
        try: await callback.message.edit_reply_markup(reply_markup=None)
        except: pass
        msg = await callback.message.answer(texts_dict["enter_answer_text"])
        await state.update_data(bot_state = f"answering_sup_request!{callback_data.split('!')[-1]}&&&&{msg.message_id}")

    elif callback_data == "ignore_request":
        try: await callback.message.edit_reply_markup(reply_markup=None)
        except: pass

        await callback.message.answer(texts_dict["u_ignored_sup_requests_text"])

    elif callback_data[:24] == "edit_mainconfigs_section":
        section = callback_data.split('!!')[-1]
        try: parameters_list_limit = int(get_config("system", "parameters_list_limit"))
        except: parameters_list_limit = 40
        parameters_list = []

        for parameter_name in get_configs()[section]:
            try:
                parameters_list.append(
                    [types.InlineKeyboardButton(text=parameter_name, \
                    callback_data=f"emp!!{section}!!{parameter_name}")]
                )
            except: pass

        if len(parameters_list) > parameters_list_limit:
            parameters_list = parameters_list[:parameters_list_limit]
            parameters_list += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_parrpage!!{section}-1")]
            ]
        
        parameters_list_keyboard = types.InlineKeyboardMarkup(inline_keyboard=parameters_list)
        try: await callback.message.edit_text(texts_dict["select_parameter_text"], \
            reply_markup=parameters_list_keyboard)
        except: await callback.message.answer(texts_dict["select_parameter_text"], \
            reply_markup=parameters_list_keyboard)

    elif callback_data[:3] == "emp":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        section = str(callback_data).split("!!")[-2]
        parameter = str(callback_data).split("!!")[-1]
        old_config = get_config(section, parameter)
        isa = 0
        if is_ascii(old_config):
            old_config = ascii_abc(old_config)
            isa = 1

        msg = await callback.message.answer(f"(ascii: {isa})\n{old_config}\n->\n" + texts_dict["enter_new_parameter_value"], reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"entering_mainconfigs_parameter!!{section}!!{parameter}&&&&{msg.message_id}")

    elif callback_data[:7] == "edit_ls":
        day = callback_data.split("!")[-1]
        editing_ls_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=texts_dict["return_ls"], callback_data=f"return_ls!{day}")],
            cancel_button
        ])
        msg = await callback.message.answer(texts_dict["enter_new_ls"],
            parse_mode="HTML", reply_markup=editing_ls_keyboard)
        await state.update_data(bot_state = f"entering_new_ls!{day}&&&&{msg.message_id}")

    elif callback_data[:9] == "return_ls":
        day = callback_data.split("!")[-1]
        await state.update_data(bot_state = None)
        old_ls = get_config("lessonshedules", f"{day}_old_ls")
        try: await callback.message.edit_text(edit_lesson_shedule(day, old_ls, _abc_ascii = False))
        except: await callback.message.answer(edit_lesson_shedule(day, old_ls, _abc_ascii = False))

    elif callback_data[:6] == "get_ls":
        day = callback_data.split("!")[-1]
        edit_ls_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=texts_dict["edit_ls"], callback_data=f"edit_ls!{day}")]
        ])
        if usercategory not in ["Dev", "MAdm", "Adm"]: edit_ls_keyboard = None
        await callback.message.answer(get_lesson_shedule(day) + "\n\n" + texts_dict["may_be_changes"],
            parse_mode="HTML", reply_markup=edit_ls_keyboard)

    elif callback_data == "all_days_ls":
        await callback.message.answer(
            f"{get_lesson_shedule('monday')}\n\n{get_lesson_shedule('tuesday')}\n\n" + \
            f"{get_lesson_shedule('wednesday')}\n\n{get_lesson_shedule('thursday')}\n\n" + \
            f"{get_lesson_shedule('friday')}\n\n" + texts_dict["may_be_changes"], parse_mode="HTML")

    elif callback_data == "statistics":
        userstable.__init__()
        folder = get_system_docs_dirpath()
        sys_files = get_files_from_dir(folder)
        for file in sys_files:
            if "stat" in file:
                try: remove_file(f"{folder}/{file}")
                except: pass

        statistics_text = get_statistics(userstable)
        filepaths = get_full_statistics(userstable)

        update_stat_button = [
            [types.InlineKeyboardButton(text=texts_dict["user_categories"], callback_data=f"statistics_get_{filepaths[0]}")],
            [types.InlineKeyboardButton(text=texts_dict["rush_hours"], callback_data=f"statistics_get_{filepaths[1]}")],
            [types.InlineKeyboardButton(text=texts_dict["users_count"], callback_data=f"statistics_get_{filepaths[2]}")],
            [types.InlineKeyboardButton(text=texts_dict["update_text"], callback_data="update_statistics")]
        ]
        update_keyboard = types.InlineKeyboardMarkup(inline_keyboard=update_stat_button)
        
        await callback.message.answer(statistics_text, parse_mode="HTML", reply_markup=update_keyboard)

    elif callback_data == "notify_all_users" and usercategory in ["Dev", "MAdm"]:
        await state.update_data(bot_state = "confirming_notify_all_users")

        confirm_notify_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["confirm_text"], callback_data="confirm_notify_all_users")],
            cancel_button
        ]
        confirm_notify_keyboard = types.InlineKeyboardMarkup(inline_keyboard=confirm_notify_buttons)

        await callback.message.answer(texts_dict["confirm_notify"], reply_markup=confirm_notify_keyboard)

    elif callback_data == "usersdata" and usercategory in ["Dev", "MAdm"]:
        await state.update_data(bot_state = "selecting_way")
        select_user_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["enter_id"], callback_data=f"select_user_enter_id")],
            [types.InlineKeyboardButton(text=texts_dict["select_from_list"], callback_data=f"select_user_from_list")],
            cancel_button
        ]
        select_user_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_user_buttons)

        await callback.message.answer(texts_dict["enter_way_determine_user"], reply_markup=select_user_keyboard)

    elif callback_data == "select_user_enter_id":
        try:
            msg = await callback.message.edit_text(texts_dict["enter_userid"], \
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[cancel_button]))
        except:
            msg = await callback.message.answer(texts_dict["enter_userid"], \
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[cancel_button]))
        
        await state.update_data(bot_state = f"userdata_entering_id&&&&{msg.message_id}")
    
    elif callback_data == "select_user_from_list":
        await state.update_data(bot_state = "editing_data_user_from_list")
        
        userstable.__init__()
        users_list = []
        try: users_list_limit = int(get_config("system", "users_list_limit"))
        except: users_list_limit = 40

        for userid in userstable.users_table.index:
            user_name = get_user_name(userid, userstable.users_table)
            users_list.append([types.InlineKeyboardButton(text=f"{userid} {user_name}", \
                callback_data=f"userdata!{userid}")])

        if len(users_list) > users_list_limit:
            users_list = users_list[:users_list_limit]
            users_list += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_usrspage-1")]
            ]
        
        users_list_keyboard = types.InlineKeyboardMarkup(inline_keyboard=users_list)
        try: await callback.message.edit_text(texts_dict["select_user"], reply_markup=users_list_keyboard)
        except: await callback.message.answer(texts_dict["select_user"], reply_markup=users_list_keyboard)
    
    elif callback_data[:8] == "userdata" and usercategory in ["Dev", "MAdm"]:
        userid = callback_data.split("!")[-1]
        userinfo_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["category_parpadezsh"], callback_data=f"edit_usercategory!{userid}"),
            types.InlineKeyboardButton(text=texts_dict["name_parpadezsh"], callback_data=f"edit_username!{userid}")],
            [types.InlineKeyboardButton(text=texts_dict["edit_userconfigs"], callback_data=f"edit_userconfigs!{userid}")],
            [types.InlineKeyboardButton(text=texts_dict["notify_user"], callback_data=f"notify_user!{userid}")],
            [types.InlineKeyboardButton(text=texts_dict["delete_user"], callback_data=f"deleteuser!{userid}")],
            [types.InlineKeyboardButton(text=texts_dict["back_to_list"], callback_data=f"select_user_from_list")],
        ]
        userinfo_keyboard = types.InlineKeyboardMarkup(inline_keyboard=userinfo_buttons)

        try: await callback.message.edit_text(user_info(userid, userstable.users_table), parse_mode="HTML", \
            reply_markup=userinfo_keyboard)
        except:
            try: await callback.message.answer(user_info(userid, userstable.users_table), parse_mode="HTML", \
                    reply_markup=userinfo_keyboard)
            except: await callback.message.answer(user_info(userid, userstable.users_table), \
                    reply_markup=userinfo_keyboard)

    elif callback_data[:16] == "edit_userconfigs":
        userid = callback_data.split("!")[-1]
        await state.update_data(bot_state = "editing_userconfig_selecting_parameter")
        
        userconfigs_buttons = []
        for config in get_usersconfig()[str(userid)]:
            userconfigs_buttons.append(
                [types.InlineKeyboardButton(text=config, callback_data=f"2edit_userconfigs!{config}!{userid}")]
            )
        
        userconfigs_keyboard = types.InlineKeyboardMarkup(inline_keyboard=userconfigs_buttons)
        await callback.message.answer(texts_dict["select_parameter_text"], reply_markup=userconfigs_keyboard)

    elif callback_data[:17] == "2edit_userconfigs":
        userid = callback_data.split("!")[-1]
        parameter = callback_data.split("!")[-2]
        await state.update_data(bot_state = f"editing_userconfigs!{parameter}!{userid}")

        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        await callback.message.answer(texts_dict["enter_new_parameter_value"], reply_markup=cancel_keyboard)

    elif callback_data[:17] == "edit_usercategory":
        userid = callback_data.split("!")[-1]
        edit_cat_man_buttons = [
            [types.InlineKeyboardButton(text="Dev", callback_data=f"edit2_usercategory!Dev!{userid}"),
            types.InlineKeyboardButton(text="MAdm", callback_data=f"edit2_usercategory!MAdm!{userid}")],
            [types.InlineKeyboardButton(text="Adm", callback_data=f"edit2_usercategory!Adm!{userid}"),
            types.InlineKeyboardButton(text="Aver", callback_data=f"edit2_usercategory!Aver!{userid}"),
            types.InlineKeyboardButton(text="Ban", callback_data=f"edit2_usercategory!Ban!{userid}")], 
            cancel_button
        ]
        edit_cat_man_keyboard = types.InlineKeyboardMarkup(inline_keyboard=edit_cat_man_buttons)

        await callback.message.answer(texts_dict["edit_user_category_text"], reply_markup=edit_cat_man_keyboard)

    elif callback_data[:18] == "edit2_usercategory":
        userid = str(callback_data)[-10:]
        new_category = str(callback_data).split("!")[1]
        old_category = get_usercategory(userid, userstable, callback.from_user.full_name)

        await callback.message.edit_text(accepted_request_edit_category(userid, userstable, \
            new_category), parse_mode="HTML")

        username = get_username(userstable, user_id, callback.from_user.full_name)
        msg_text = userdata_edited_message(
                username, userid, "username", new_category, old_category
            )
        for creatorid in get_developers_id(userstable.users_table, user_id).union(get_main_admins_id(userstable.users_table, user_id)):
            if int(get_userconfig(creatorid, "notify_ude")) == 0: continue
            try: await bot.send_message(creatorid, msg_text, parse_mode="HTML")
            except exceptions.TelegramForbiddenError:
                userstable.delete_user(creatorid, notify=False)
            except: pass
        
        sh_desk = texts_dict[f"users_cnt_{new_category.lower()}"] 
        try: await bot.send_message(chat_id=userid, \
            text=f"{texts_dict['edit_category_request_accepted']} {sh_desk}!\n{texts_dict['press_start_to_update']}", \
            parse_mode="HTML")
        except exceptions.TelegramForbiddenError:
            userstable.delete_user(userid, notify=False)

    elif callback_data[:10] == "deleteuser":
        userid = callback_data.split("!")[-1]
        await state.update_data(bot_state = "deleting_user")

        confirm_delete_user_buttons = [
            [types.InlineKeyboardButton(text=texts_dict['confirm_text'], callback_data=f"confirm_delete_user!{userid}")], 
            cancel_button
        ]
        confirm_delete_user_keyboard = types.InlineKeyboardMarkup(inline_keyboard=confirm_delete_user_buttons)

        await callback.message.answer(texts_dict['confirm_delete_user'], reply_markup=confirm_delete_user_keyboard)

    elif callback_data[:19] == "confirm_delete_user":
        userid = callback_data.split("!")[-1]
        await state.update_data(bot_state = None)

        try:
            userstable.delete_user(userid, notify=False)
            try: await callback.message.edit_text(f"{texts_dict['user_deleted1']} {userid} {texts_dict['user_deleted2']}")
            except: await callback.message.answer(f"{texts_dict['user_deleted1']} {userid} {texts_dict['user_deleted2']}")

        except:
            try: await callback.message.edit_text(f"{texts_dict['delete_user_error']} '{userid}'")
            except: await callback.message.answer(f"{texts_dict['delete_user_error']} '{userid}'")

    elif callback_data[:13] == "edit_username":
        userid = callback_data.split("!")[-1]

        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(texts_dict["enter_username_text"], reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"editing_username!{userid}&&&&{msg.message_id}")

    elif callback_data[:11] == "notify_user":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(texts_dict["enter_message_text"], reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"entering_message_notify_user!{callback_data.split('!')[-1]}&&&&{msg.message_id}")

    elif callback_data == "confirm_notify_all_users":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=texts_dict["add_doc_quest_yes"], callback_data="add_doc_quest_yes"),
            types.InlineKeyboardButton(text=texts_dict["add_doc_quest_no"], callback_data="notifying_all_users")]
        ])
        try: await callback.message.edit_text(texts_dict["add_doc_quest"], reply_markup=cancel_keyboard)
        except: await callback.message.answer(texts_dict["add_doc_quest"], reply_markup=cancel_keyboard)

    elif callback_data == "add_doc_quest_yes":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        try:
            msg = await callback.message.edit_text(texts_dict["send_me_a_document_text"], reply_markup=cancel_keyboard) 
        except:
            msg = await callback.message.answer(texts_dict["send_me_a_document_text"], reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"addingdocnotify&&&&{msg.message_id}")

    elif callback_data == "notifying_all_users":
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.edit_text(texts_dict["enter_message_text"], reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"notifying_all_users_entering_msg&&&&{msg.message_id}")

    elif callback_data[:12] == "get_homework":
        homeworktable.__init__()
        subject = str(callback_data).split("!")[-1]
        text, hw_list, date_list = get_homeworks_message(subject, homeworktable.operat_table)
        try: tasks_list_limit = int(get_config("system", "tasks_list_limit"))
        except: tasks_list_limit = 40

        select_hw_buttons = []
        for hw_date in hw_list:
            select_hw_buttons += [[types.InlineKeyboardButton(text=f"{texts_dict['hw_from_text']} {hw_date}", callback_data=f"homeworktask!{subject}!{hw_date[:-5]}")]]

        if len(select_hw_buttons) > tasks_list_limit:
            select_hw_buttons = select_hw_buttons[:tasks_list_limit]
            select_hw_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_taskpage!{subject}-1")]
            ]

        if current_day() not in date_list and usercategory in ["Dev", "MAdm", "Adm"]:
            select_hw_buttons += [[types.InlineKeyboardButton(text=texts_dict["public_task_text"], callback_data=f"add_homeworktask!{subject}!{current_day()}")]]

        select_hw_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_hw_buttons)

        await callback.message.answer(text, parse_mode="HTML", reply_markup=select_hw_keyboard)

    elif callback_data[:12] == "homeworktask":
        homeworktable.__init__()
        date = str(callback_data).split("!")[-1]
        subject = str(callback_data).split("!")[-2]
        homework = homeworktable.get_homework(subject, date, _ascii_abc = True)
        text =  f"<u>{texts_dict[f'{subject}_text']} ({date})</u>:\n\n" + \
                f"{homework[0]}"
        
        if usercategory not in ["Dev", "MAdm", "Adm"]:
            edit_hw_keyboard = None
        else:
            edit_hw_button = [
                [types.InlineKeyboardButton(text=texts_dict["edit_hw"], callback_data=f"edit_homeworktask!{subject}!{date}")]
            ]
            edit_hw_keyboard = types.InlineKeyboardMarkup(inline_keyboard=edit_hw_button)
        
        if homework[1]:
            for filepath in homework[1]:
                doctype = filepath.split(".")[-1]

                if doctype in ["png", "jpg"]: msg = await callback.message.answer_photo(photo=FSInputFile(filepath))
                elif doctype in ["mp4"]: msg = await callback.message.answer_video(video=FSInputFile(filepath))
                elif doctype in ["ogg"]: msg = await callback.message.answer_voice(voice=FSInputFile(filepath))
                else: msg = await callback.message.answer_document(document=FSInputFile(filepath))
                
                await asyncio.sleep(delay_time())

        await callback.message.answer(text, parse_mode="HTML", \
            reply_markup=edit_hw_keyboard)

    elif callback_data[:20] == "back_to_homeworktask":
        homeworktable.__init__()
        date = str(callback_data).split("!")[-1]
        subject = str(callback_data).split("!")[-2]
        homework = homeworktable.get_homework(subject, date, _ascii_abc = True)
        text =  f"<u>{texts_dict[f'{subject}_text']} ({date})</u>:\n\n" + \
                f"{homework[0]}"
        
        if usercategory not in ["Dev", "MAdm", "Adm"]:
            edit_hw_keyboard = None
        else:
            edit_hw_button = [
                [types.InlineKeyboardButton(text=texts_dict["edit_hw"], callback_data=f"edit_homeworktask!{subject}!{date}")]
            ]
            edit_hw_keyboard = types.InlineKeyboardMarkup(inline_keyboard=edit_hw_button)

        try: await callback.message.edit_text(text, parse_mode="HTML", reply_markup=edit_hw_keyboard)
        except: await callback.message.answer(text, parse_mode="HTML", reply_markup=edit_hw_keyboard)

    elif callback_data[:17] == "edit_homeworktask":
        date = str(callback_data).split("!")[-1]
        subject = str(callback_data).split("!")[-2]
        
        edit_hw_button = [
                [types.InlineKeyboardButton(text=texts_dict["edit_text_hw"], callback_data=f"add_homeworktask!{subject}!{date}")],
                [types.InlineKeyboardButton(text=texts_dict["delete_hw"], callback_data=f"delete_homeworktask!{subject}!{date}")],
                [types.InlineKeyboardButton(text=texts_dict["add_document_hw"], callback_data=f"add_doc_hw!{subject}!{date}")],
                [types.InlineKeyboardButton(text=texts_dict["back_to_hwtask"], callback_data=f"back_to_homeworktask!{subject}!{date}")]
            ]
        edit_hw_keyboard = types.InlineKeyboardMarkup(inline_keyboard=edit_hw_button)

        try: await callback.message.edit_text(texts_dict["select_way_edit_hw"], reply_markup=edit_hw_keyboard)
        except: await callback.message.answer(texts_dict["select_way_edit_hw"], reply_markup=edit_hw_keyboard)

    elif callback_data[:16] == "add_homeworktask":
        subject = str(callback_data).split("!")[-2]
        date = str(callback_data).split("!")[-1]
        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(texts_dict["enter_hw_text"], reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"entering_homework!{subject}!{date}&&&&{msg.message_id}")

    elif callback_data[:10] == "add_doc_hw":
        subject = str(callback_data).split("!")[-2]
        date = str(callback_data).split("!")[-1]

        cancel_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[cancel_button])
        msg = await callback.message.answer(texts_dict["send_me_a_document_text"], reply_markup=cancel_keyboard)
        await state.update_data(bot_state = f"adding_doc_hw!{subject}!{date}&&&&{msg.message_id}")

    elif callback_data == "stop_adding_hw_photos":
        await state.update_data(bot_state = None)
        await callback.message.answer(texts_dict["photos_publicated"])

    elif callback_data[:19] == "delete_homeworktask":
        date = str(callback_data).split("!")[-1]
        subject = str(callback_data).split("!")[-2]
        homework = homeworktable.get_homework(subject, date, _ascii_abc = True)
        if homework[1] != False:
            for filepath in homework[1]:
                remove_file(filepath)
        
        homeworktable.add_homework(subject, "", date=date, notify=False)
        try: await callback.message.edit_text(texts_dict["hw_deleted"])
        except: await callback.message.answer(texts_dict["hw_deleted"])

    elif callback_data == "update_homework_list":
        homeworktable.__init__()
        hw_msg = homework_message(homeworktable.operat_table)
        homewrk_list_limit = int(get_config("system", "homewrk_list_limit"))

        homework_buttons = []
        for subj in hw_msg[1]:
            homework_buttons += [
                [types.InlineKeyboardButton(text=hw_msg[1][subj]["text"],
                callback_data=hw_msg[1][subj]["callback"])]
            ]
        if len(homework_buttons) >= homewrk_list_limit:
            homework_buttons = homework_buttons[:homewrk_list_limit]
            homework_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data="next_hwpage-1")]
            ]
        update_hw_button = [types.InlineKeyboardButton(text=texts_dict["update_text"], callback_data="update_homework_list")]
        homework_buttons += [update_hw_button]
        homework_keyboard = types.InlineKeyboardMarkup(inline_keyboard=homework_buttons)

        try: await callback.message.edit_text(hw_msg[0], reply_markup=homework_keyboard, parse_mode="HTML")
        except: pass
        await callback.answer(texts_dict["updated_text"])

    elif callback_data == "update_statistics":
        userstable.__init__()
        folder = get_system_docs_dirpath()
        sys_files = get_files_from_dir(folder)
        for file in sys_files:
            if "stat" in file:
                try: remove_file(f"{folder}/{file}")
                except: pass
        
        statistics_text = get_statistics(userstable)
        filepaths = get_full_statistics(userstable)

        update_stat_button = [
            [types.InlineKeyboardButton(text=texts_dict["user_categories"], callback_data=f"statistics_get_{filepaths[0]}")],
            [types.InlineKeyboardButton(text=texts_dict["rush_hours"], callback_data=f"statistics_get_{filepaths[1]}")],
            [types.InlineKeyboardButton(text=texts_dict["users_count"], callback_data=f"statistics_get_{filepaths[2]}")],
            [types.InlineKeyboardButton(text=texts_dict["update_text"], callback_data="update_statistics")]
        ]
        update_keyboard = types.InlineKeyboardMarkup(inline_keyboard=update_stat_button)
        try: await callback.message.edit_text(statistics_text, parse_mode="HTML", reply_markup=update_keyboard)
        except: pass
        await callback.answer(texts_dict["updated_text"])

    elif callback_data[:14] == "statistics_get":
        system_folder = get_system_docs_dirpath()
        filepath = f"{system_folder}/{callback_data[15:]}"
        await callback.message.answer_document(document=FSInputFile(filepath))

    elif callback_data[:13] == "config_notify":
        setting = callback_data.split("!")[-2]
        setting_state = callback_data.split("!")[-1]

        if setting != "f":
            change_userconfig(user_id, f"notify_{setting}", setting_state)

        aun = int(get_userconfig(user_id, "notify_aun"))
        ude = int(get_userconfig(user_id, "notify_ude"))
        mce = int(get_userconfig(user_id, "notify_mce"))
        err = int(get_userconfig(user_id, "notify_err"))
        sup = int(get_userconfig(user_id, "notify_sup"))
        
        notify_buttons = []
        
        if aun == 1: notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_aun_on"], callback_data="config_notify!aun!0")])
        else: notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_aun_off"], callback_data="config_notify!aun!1")])
        
        if ude == 1 and usercategory in ["MAdm", "Dev"]:
            notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_ude_on"], callback_data="config_notify!ude!0")])
        elif ude == 0 and usercategory in ["MAdm", "Dev"]:
            notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_ude_off"], callback_data="config_notify!ude!1")])
        
        if mce == 1 and usercategory in ["Dev"]:
            notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_mce_on"], callback_data="config_notify!mce!0")])
        elif mce == 0 and usercategory in ["Dev"]:
            notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_mce_off"], callback_data="config_notify!mce!1")])
        
        if err == 1 and usercategory in ["Dev"]:
            notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_err_on"], callback_data="config_notify!err!0")])
        elif err == 0 and usercategory in ["Dev"]:
            notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_err_off"], callback_data="config_notify!err!1")])
        
        if sup == 1 and usercategory in ["Dev"]:
            notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_sup_on"], callback_data="config_notify!sup!0")])
        elif sup == 0 and usercategory in ["Dev"]:
            notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["notify_sup_off"], callback_data="config_notify!sup!1")])
        
        notify_buttons.append([types.InlineKeyboardButton(text=texts_dict["back_to_sets"], callback_data="back_to_settings")])

        notify_keyboard = types.InlineKeyboardMarkup(inline_keyboard=notify_buttons)

        try: await callback.message.edit_text(texts_dict["notify_settings"], reply_markup=notify_keyboard)
        except: await callback.message.answer(texts_dict["notify_settings"], reply_markup=notify_keyboard)

    elif callback_data == "back_to_settings":
        await state.update_data(bot_state = None)
        username = get_username(userstable, user_id, callback.message.from_user.full_name)

        settings_buttons = [
            [types.InlineKeyboardButton(text=texts_dict["change_username_text"], callback_data="change_name")],
            [types.InlineKeyboardButton(text=texts_dict["change_usercategory_text"], callback_data="change_category")],
            [types.InlineKeyboardButton(text=texts_dict["change_mainkeyboard_text"], callback_data="edit_main_keyboard")],
            [types.InlineKeyboardButton(text=texts_dict["notifications_text"], callback_data="config_notify!f!f")]
        ]
        if usercategory != "Dev": settings_buttons += [support_button]
        settings_keyboard = types.InlineKeyboardMarkup(inline_keyboard=settings_buttons)

        try: await callback.message.edit_text(settings_message(user_id, username, usercategory, tgusername), \
            parse_mode="HTML", reply_markup=settings_keyboard)
        except: await callback.message.answer(settings_message(user_id, username, usercategory, tgusername), \
            parse_mode="HTML", reply_markup=settings_keyboard)
    
    elif callback_data[:11] == "next_hwpage":
        page = int(callback_data.split("-")[-1])
        homeworktable.__init__()
        hw_msg = homework_message(homeworktable.operat_table)
        try: homewrk_list_limit = int(get_config("system", "homewrk_list_limit"))
        except: homewrk_list_limit = 40

        homework_buttons = []
        for subj in hw_msg[1]:
            homework_buttons += [
                [types.InlineKeyboardButton(text=hw_msg[1][subj]["text"],
                callback_data=hw_msg[1][subj]["callback"])]
            ]
        if len(homework_buttons) >= homewrk_list_limit:
            homework_buttons = homework_buttons[homewrk_list_limit*page:homewrk_list_limit*(page+1)]
            if len(hw_msg[1]) > homewrk_list_limit*(page+1):
                homework_buttons += [
                    [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_hwpage-{page+1}"),
                    types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_hwpage-{page+1}")]
                ]
            else:
                homework_buttons += [
                    [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_hwpage-{page+1}")]
                ]
        
        update_hw_button = [types.InlineKeyboardButton(text=texts_dict["update_text"], callback_data="update_homework_list")]
        homework_buttons += [update_hw_button]
        homework_keyboard = types.InlineKeyboardMarkup(inline_keyboard=homework_buttons)

        try: await callback.message.edit_text(hw_msg[0], reply_markup=homework_keyboard, parse_mode="HTML")
        except: await callback.message.answer(hw_msg[0], reply_markup=homework_keyboard, parse_mode="HTML")

    elif callback_data[:11] == "prev_hwpage":
        page = int(callback_data.split("-")[-1])

        homeworktable.__init__()
        hw_msg = homework_message(homeworktable.operat_table)
        try: homewrk_list_limit = int(get_config("system", "homewrk_list_limit"))
        except: homewrk_list_limit = 40

        homework_buttons = []
        for subj in hw_msg[1]:
            homework_buttons += [
                [types.InlineKeyboardButton(text=hw_msg[1][subj]["text"],
                callback_data=hw_msg[1][subj]["callback"])]
            ]
        if len(homework_buttons) > homewrk_list_limit:
            homework_buttons = homework_buttons[homewrk_list_limit*(page-2):homewrk_list_limit*(page-1)]
            if page-1 > 1 and len(hw_msg[1]) > homewrk_list_limit*(page-1):
                homework_buttons += [
                    [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_hwpage-{page-1}"),
                    types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_hwpage-{page-1}")]
                ]
            elif len(hw_msg[1]) > homewrk_list_limit*(page-1):
                homework_buttons += [
                    [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_hwpage-{page-1}")]
                ]
        
        update_hw_button = [types.InlineKeyboardButton(text=texts_dict["update_text"], callback_data="update_homework_list")]
        homework_buttons += [update_hw_button]
        homework_keyboard = types.InlineKeyboardMarkup(inline_keyboard=homework_buttons)

        try: await callback.message.edit_text(hw_msg[0], reply_markup=homework_keyboard, parse_mode="HTML")
        except: await callback.message.answer(hw_msg[0], reply_markup=homework_keyboard, parse_mode="HTML")

    elif callback_data[:13] == "next_taskpage":
        page = int(callback_data.split("-")[-1])
        homeworktable.__init__()
        subject = callback_data.split("!")[-1].split("-")[0]
        text, hw_list, date_list = get_homeworks_message(subject, homeworktable.operat_table)
        try: tasks_list_limit = int(get_config("system", "tasks_list_limit"))
        except: tasks_list_limit = 40

        select_hw_buttons = []
        for hw_date in hw_list:
            select_hw_buttons += [[types.InlineKeyboardButton(text=f"{texts_dict['hw_from_text']} {hw_date}", callback_data=f"homeworktask!{subject}!{hw_date[:-5]}")]]

        if len(select_hw_buttons) > tasks_list_limit*(page+1):
            select_hw_buttons = select_hw_buttons[tasks_list_limit*page:tasks_list_limit*(page+1)]
            select_hw_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_taskpage!{subject}-{page+1}"),
                types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_taskpage!{subject}-{page+1}")]
            ]
        else:
            select_hw_buttons = select_hw_buttons[tasks_list_limit*page:tasks_list_limit*(page+1)]
            select_hw_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_taskpage!{subject}-{page+1}")]
            ]

        if current_day() not in date_list and usercategory in ["Dev", "MAdm", "Adm"]:
            select_hw_buttons += [[types.InlineKeyboardButton(text=texts_dict["public_task_text"], callback_data=f"add_homeworktask!{subject}!{current_day()}")]]
        
        select_hw_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_hw_buttons)

        try: await callback.message.edit_text(text, reply_markup=select_hw_keyboard, parse_mode="HTML")
        except: await callback.message.answer(text, reply_markup=select_hw_keyboard, parse_mode="HTML")

    elif callback_data[:13] == "prev_taskpage":
        page = int(callback_data.split("-")[-1])
        homeworktable.__init__()
        subject = callback_data.split("!")[-1].split("-")[0]
        text, hw_list, date_list = get_homeworks_message(subject, homeworktable.operat_table)
        try: tasks_list_limit = int(get_config("system", "tasks_list_limit"))
        except: tasks_list_limit = 40

        select_hw_buttons = []
        for hw_date in hw_list:
            select_hw_buttons += [[types.InlineKeyboardButton(text=f"{texts_dict['hw_from_text']} {hw_date}", callback_data=f"homeworktask!{subject}-{hw_date[:-5]}")]]

        if page-1 > 1 and len(select_hw_buttons) > tasks_list_limit*(page-1):
            select_hw_buttons = select_hw_buttons[tasks_list_limit*(page-2):tasks_list_limit*(page-1)]
            select_hw_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_taskpage!{subject}-{page-1}"),
                types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_taskpage!{subject}-{page-1}")]
            ]
        elif len(select_hw_buttons) > tasks_list_limit*(page-1):
            select_hw_buttons = select_hw_buttons[tasks_list_limit*(page-2):tasks_list_limit*(page-1)]
            select_hw_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_taskpage!{subject}-{page-1}")]
            ]

        if current_day() not in date_list and usercategory in ["Dev", "MAdm", "Adm"]:
            select_hw_buttons += [[types.InlineKeyboardButton(text=texts_dict["public_task_text"], callback_data=f"add_homeworktask!{subject}!{current_day()}")]]

        select_hw_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_hw_buttons)

        try: await callback.message.edit_text(text, reply_markup=select_hw_keyboard, parse_mode="HTML")
        except: await callback.message.answer(text, reply_markup=select_hw_keyboard, parse_mode="HTML")

    elif callback_data[:13] == "next_usrspage":
        await state.update_data(bot_state = "editing_data_user_from_list")
        
        page = int(callback_data.split("-")[-1])
        userstable.__init__()
        users_list = []
        try: users_list_limit = int(get_config("system", "users_list_limit"))
        except: users_list_limit = 40

        for userid in userstable.users_table.index:
            user_name = get_user_name(userid, userstable.users_table)
            users_list.append([types.InlineKeyboardButton(text=f"{userid} {user_name}", \
                callback_data=f"userdata!{userid}")])
        
        if len(users_list) > users_list_limit*(page+1):
            users_list = users_list[users_list_limit*page:users_list_limit*(page+1)]
            users_list += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_usrspage-{page+1}"),
                types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_usrspage-{page+1}")]
            ]
        else:
            users_list = users_list[users_list_limit*page:users_list_limit*(page+1)]
            users_list += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_usrspage-{page+1}")]
            ]

        users_list_keyboard = types.InlineKeyboardMarkup(inline_keyboard=users_list)
        try: await callback.message.edit_text(texts_dict["select_user"], reply_markup=users_list_keyboard)
        except: await callback.message.answer(texts_dict["select_user"], reply_markup=users_list_keyboard)

    elif callback_data[:13] == "prev_usrspage":
        await state.update_data(bot_state = "editing_data_user_from_list")
        
        page = int(callback_data.split("-")[-1])
        userstable.__init__()
        users_list = []
        try: users_list_limit = int(get_config("system", "users_list_limit"))
        except: users_list_limit = 40

        for userid in userstable.users_table.index:
            user_name = get_user_name(userid, userstable.users_table)
            users_list.append([types.InlineKeyboardButton(text=f"{userid} {user_name}", \
                callback_data=f"userdata!{userid}")])

        if page-1 > 1 and len(users_list) > users_list_limit*(page-1):
            users_list = users_list[users_list_limit*(page-2):users_list_limit*(page-1)]
            users_list += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_usrspage-{page-1}"),
                types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_usrspage-{page-1}")]
            ]
        elif len(users_list) > users_list_limit*(page-1):
            users_list = users_list[users_list_limit*(page-2):users_list_limit*(page-1)]
            users_list += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_usrspage-{page-1}")]
            ]

        users_list_keyboard = types.InlineKeyboardMarkup(inline_keyboard=users_list)
        try: await callback.message.edit_text(texts_dict["select_user"], reply_markup=users_list_keyboard)
        except: await callback.message.answer(texts_dict["select_user"], reply_markup=users_list_keyboard)

    elif callback_data[:13] == "next_sectpage":
        page = int(callback_data.split("-")[-1])
        try: sections_list_limit = int(get_config("system", "sections_list_limit"))
        except: sections_list_limit = 40

        select_section_buttons = []
        for section in list(get_configs())[1:]:
            select_section_buttons.append(
                [types.InlineKeyboardButton(text=section, callback_data=f"edit_mainconfigs_section!!{section}")]
            )

        if len(select_section_buttons) > sections_list_limit*(page+1):
            select_section_buttons = select_section_buttons[sections_list_limit*page:sections_list_limit*(page+1)]
            select_section_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_sectpage-{page+1}"),
                types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_sectpage-{page+1}")]
            ]
        else:
            select_section_buttons = select_section_buttons[sections_list_limit*page:sections_list_limit*(page+1)]
            select_section_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_sectpage-{page+1}")]
            ]

        select_section_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_section_buttons)
        try: await callback.message.edit_text(texts_dict["select_section_text"], reply_markup=select_section_keyboard)
        except: await callback.message.answer(texts_dict["select_section_text"], reply_markup=select_section_keyboard)
    
    elif callback_data[:13] == "prev_sectpage":
        page = int(callback_data.split("-")[-1])
        try: sections_list_limit = int(get_config("system", "sections_list_limit"))
        except: sections_list_limit = 40

        select_section_buttons = []
        for section in list(get_configs())[1:]:
            select_section_buttons.append(
                [types.InlineKeyboardButton(text=section, callback_data=f"edit_mainconfigs_section!!{section}")]
            )

        if page-1 > 1 and len(select_section_buttons) > sections_list_limit*(page-1):
            select_section_buttons = select_section_buttons[sections_list_limit*(page-2):sections_list_limit*(page-1)]
            select_section_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_sectpage-{page-1}"),
                types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_sectpage-{page-1}")]
            ]
        elif len(select_section_buttons) > sections_list_limit*(page-1):
            select_section_buttons = select_section_buttons[sections_list_limit*(page-2):sections_list_limit*(page-1)]
            select_section_buttons += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_sectpage-{page-1}")]
            ]

        select_section_keyboard = types.InlineKeyboardMarkup(inline_keyboard=select_section_buttons)
        try: await callback.message.edit_text(texts_dict["select_section_text"], reply_markup=select_section_keyboard)
        except: await callback.message.answer(texts_dict["select_section_text"], reply_markup=select_section_keyboard)

    elif callback_data[:13] == "next_parrpage":
        section = callback_data.split('!!')[-1].split("-")[0]
        page = int(callback_data.split("-")[-1])
        try: parameters_list_limit = int(get_config("system", "parameters_list_limit"))
        except: parameters_list_limit = 40
        parameters_list = []

        for parameter_name in get_configs()[section]:
            parameters_list.append(
                [types.InlineKeyboardButton(text=parameter_name, \
                callback_data=f"emp!!{section}!!{parameter_name}")]
            )

        if len(parameters_list) > parameters_list_limit*(page+1):
            parameters_list = parameters_list[parameters_list_limit*page:parameters_list_limit*(page+1)]
            parameters_list += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_parrpage!!{section}-{page+1}"),
                types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_parrpage!!{section}-{page+1}")]
            ]
        else:
            parameters_list = parameters_list[parameters_list_limit*page:parameters_list_limit*(page+1)]
            parameters_list += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_parrpage!!{section}-{page+1}")]
            ]

        parameters_list_keyboard = types.InlineKeyboardMarkup(inline_keyboard=parameters_list)
        try: await callback.message.edit_text(texts_dict["select_parameter_text"], \
            reply_markup=parameters_list_keyboard)
        except: await callback.message.answer(texts_dict["select_parameter_text"], \
            reply_markup=parameters_list_keyboard)
    
    elif callback_data[:13] == "prev_parrpage":
        section = callback_data.split('!!')[-1].split("-")[0]
        page = int(callback_data.split("-")[-1])
        try: parameters_list_limit = int(get_config("system", "parameters_list_limit"))
        except: parameters_list_limit = 40
        parameters_list = []

        for parameter_name in get_configs()[section]:
            parameters_list.append(
                [types.InlineKeyboardButton(text=parameter_name, \
                callback_data=f"emp!!{section}!!{parameter_name}")]
            )

        if page-1 > 1 and len(parameters_list) > parameters_list_limit*(page-1):
            parameters_list = parameters_list[parameters_list_limit*(page-2):parameters_list_limit*(page-1)]
            parameters_list += [
                [types.InlineKeyboardButton(text=texts_dict["backward"], callback_data=f"prev_parrpage!!{section}-{page-1}"),
                types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_parrpage!!{section}-{page-1}")]
            ]
        elif len(parameters_list) > parameters_list_limit*(page-1):
            parameters_list = parameters_list[parameters_list_limit*(page-2):parameters_list_limit*(page-1)]
            parameters_list += [
                [types.InlineKeyboardButton(text=texts_dict["forward"], callback_data=f"next_parrpage!!{section}-{page-1}")]
            ]

        parameters_list_keyboard = types.InlineKeyboardMarkup(inline_keyboard=parameters_list)
        try: await callback.message.edit_text(texts_dict["select_parameter_text"], \
            reply_markup=parameters_list_keyboard)
        except: await callback.message.answer(texts_dict["select_parameter_text"], \
            reply_markup=parameters_list_keyboard)

    else: pass

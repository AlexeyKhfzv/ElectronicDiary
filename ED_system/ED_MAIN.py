RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m'

# Import aiogram library
try:
    from aiogram import Dispatcher
except ModuleNotFoundError:
    print(f"{RED}Please, install aiogram!{RESET}")
    exit()

try:
    import asyncio
except ModuleNotFoundError:
    print(f"{RED}Please, install asyncio!{RESET}")
    exit()

try:
    import ED_Maintools
except ModuleNotFoundError:
    print(f"{RED}Please, install full ED system! [ED_Maintools]{RESET}")
    exit()

try:
    import ED_telegrambot
except ModuleNotFoundError:
    print(f"{RED}Please, install full ED system! [ED_telegrambot]{RESET}")
    exit()

telegram_dp = Dispatcher()
async def telegram_bot():
    print("Starting telegram bot...")
    telegram_dp.include_router(ED_telegrambot.router)
    print(f"Telegram bot has been {GREEN}successfully launched{RESET}")

    await telegram_dp.start_polling(ED_telegrambot.bot)

async def system_check():
    while True:
        try:
            data_backup_interval_h = float(ED_Maintools.get_config("system", "data_backup_interval_h"))
            data_backup_interval_m = float(ED_Maintools.get_config("system", "data_backup_interval_m", read=False))
            data_backup_interval_s = float(ED_Maintools.get_config("system", "data_backup_interval_s", read=False))
            data_backup_interval = data_backup_interval_h * 3600 + data_backup_interval_m * 60 + data_backup_interval_s

            await asyncio.sleep(data_backup_interval)
        except: await asyncio.sleep(86400) # 24 hours

        print(f"Running data backup ({ED_Maintools.current_time()})...")
        ED_telegrambot.update_texts_dict_tgbot()
        ED_Maintools.update_texts_dict()
        ED_Maintools.Users_Table().auto_users_delete(notify=False)
        ED_Maintools.Users_Table().data_backup(notify=False)
        ED_Maintools.Homework_Table().data_backup(notify=False)
        ED_Maintools.Homework_Table().remove_unnecessary_homeworks(notify=False)

async def load_statistics(): # Every 1 hour
    dt = ED_Maintools.dt

    cur_time = dt.now()
    start_time = 86400 - (int(cur_time.hour) * 3600 + int(cur_time.minute) * 60 + int(cur_time.second))
    await asyncio.sleep(start_time)
    
    while True:
        ED_Maintools.load_statistics()
        sleep_time = 60.0 - float(dt.now().minute)
        await asyncio.sleep(sleep_time * 60.0)

async def main():
    tasks = [
        telegram_bot(),
        system_check(),
        load_statistics()
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

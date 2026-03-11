RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'

# Import necessary library
try:
    import pandas as pd
    from pandas import Categorical
except ModuleNotFoundError:
    print(f"{RED}Please, install pandas!{RESET}")
    exit()

try:
    from pandasql import sqldf
except ModuleNotFoundError:
    print(f"{RED}Please, install pandasql!{RESET}")
    exit()

try:
    from datetime import datetime as dt, timedelta
except ModuleNotFoundError:
    print(f"{RED}Please, install datetime!{RESET}")
    exit()

try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    print(f"{RED}Please, install plotly and kaleido!{RESET}")
    exit()

try:
    from ED_file_manager import *
except ModuleNotFoundError:
    print(f"{RED}Please, put ED_file_manager in this folder or download new!{RESET}")
    exit()

try:
    from ED_Configfile_reader import *
except ModuleNotFoundError:
    print(f"{RED}Please, put ED_Configfile_reader in this folder or download new!{RESET}")
    exit()


TOKEN = get_config("TOKEN", "token") # Token

def current_time() -> str: # Returns current time (Y-m-d H:M:S)
    return str(dt.now())[:-7]

def current_day() -> str: # Returns current time (Y-m-d)
    return str(dt.now())[:-16]

def all_files_prepare(*, notify: bool = True) -> None:
    if notify: print("----------")
    prepare_file("users_csv", "users_csv.csv", notify = notify)
    prepare_file("users_txt", "users_txt.txt", notify = notify)
    prepare_file("homework_constant_csv", "homework_C_csv.csv", notify = notify)
    prepare_file("homework_constant_txt", "homework_C_txt.txt", notify = notify)
    prepare_file("homework_operational_csv", "homework_O_csv.csv", notify = notify)
    prepare_file("statistics", "ED_statistics.txt", notify = notify)
    if notify: print("----------")

all_files_prepare()

class Buttons(): # Buttons texts
    def __init__(self, user_id):
        user_id = str(user_id)
        self.__user_id = user_id
        self.start_button = ascii_abc(get_userconfig(user_id, "start_button"))
        self.homework_button = ascii_abc(get_userconfig(user_id, "homework_button"))
        self.settings_button = ascii_abc(get_userconfig(user_id, "settings_button"))
        self.lessonshedule_button = ascii_abc(get_userconfig(user_id, "lessonshedule_button"))
        self.management_button = ascii_abc(get_userconfig(user_id, "management_button"))
    
    def change_button_text(self, button_name: str, new_text: str, *, _abc_bin: bool = True) -> None:
        if _abc_bin: new_text = abc_ascii(new_text)
        change_userconfig(self.__user_id, button_name, new_text)

class Users_Table(): # Class to work with tables in csv and txt files
    def __init__(self):
        self.csv_filepath = get_config("files", "users_csv")
        self.txt_filepath = get_config("files", "users_txt")
        self.users_table = self.get_csv_table(self.csv_filepath).set_index("telegram_id")
    
    def csvsave(self, dataframe: pd.DataFrame, /, *, index: bool = True, notify: bool = True) -> None:
        try:
            dataframe.to_csv(self.csv_filepath, index=index)
            if notify: print(f"User data {GREEN}has just been saved{RESET} ({current_time()})")
        except Exception as e: print(f"{RED}Error while saving user data: {e}{RESET} ({current_time()})")

    def get_csv_table(self, filepath: str, /) -> pd.DataFrame:
        try:
            users_dataframe = pd.read_csv(filepath)
        except pd.errors.EmptyDataError:
            print(f"{YELLOW}Users (csv): empty DataFrame.{RESET} Trying to get the table from the txt file...")
            while True:
                try:
                    edit_file(filepath, asciiread_file(self.txt_filepath))
                    users_dataframe = pd.read_csv(filepath)
                    break
                except FileNotFoundError:
                    prepare_file("users_csv",  "users_csv.csv")
                    prepare_file("users_txt",  "users_txt.txt")

                except pd.errors.EmptyDataError:
                    print(f"{YELLOW}Users (txt): empty DataFrame.{RESET}", end=" ")
                    users_dataframe = pd.DataFrame({
                        "telegram_id": [],
                        "username": [],
                        "category": [],
                        "last_visited": []
                    })
                    print(f"Successfully {GREEN}created{RESET} a new table.")
                    
                    self.data_backup(another_df=users_dataframe, reset_index=False)
                    break

        except Exception as e:
            print(f"{RED}An error found: {e}{RESET}")
            exit()
        
        finally:
            users_dataframe["last_visited"] = pd.to_datetime(users_dataframe["last_visited"], format="%Y-%m-%d %H:%M:%S")
            users_dataframe["telegram_id"] = users_dataframe["telegram_id"].astype(str)
            categories = ['Dev', 'MAdm', 'Adm', 'Aver', 'Ban']
            users_dataframe['category'] = Categorical(users_dataframe['category'], categories=categories, ordered=True)
            return users_dataframe

    def edit_value(self, user_id: str | int, column: str, new_value: str | pd.Timestamp, /,
                   *, _abc_ascii: bool = False, _ascii_abc: bool = False, notify: bool = True) -> None: # Save new user_data to csv file.
        user_id = str(user_id)
        
        self.__init__()
        if _abc_ascii:
            self.users_table.at[user_id, column] = abc_ascii(new_value)
        elif _ascii_abc:
            self.users_table.at[user_id, column] = ascii_abc(new_value)
        else:
            self.users_table.at[user_id, column] = new_value
        self.csvsave(self.users_table, notify=notify)

    def add_user(self, user_id: str | int, username: str, category: str, /) -> None:
        user_id = str(user_id)
        self.__init__()

        if user_id not in list(self.users_table.index):
            self.users_table.loc[user_id] = [username, category, current_time()]
            self.csvsave(self.users_table, notify=False) # Save user to the users table
            set_stock_usersettings(user_id)
            print(f"User with id '{user_id}' {GREEN}has been saved{RESET} to the table")
        else:
            print(f"User with telegram id '{user_id}' {YELLOW}is already in the user table{RESET}")

    def data_backup(self, *, another_df: bool | pd.DataFrame = False, reset_index: bool = True, notify: bool = True) -> None:
        if notify: print(f"Saving users data to txt file...")

        if str(another_df) == "False":
            self.__init__()
            dataframe_to_save = self.users_table
        else:
            dataframe_to_save = another_df
        
        if reset_index:
            dataframe_to_save = dataframe_to_save.reset_index()
            dataframe_to_save.rename(columns={'index': 'telegram_id'}, inplace=True)
        
        df_columns = abc_ascii(",").join([abc_ascii(i) for i in dataframe_to_save.columns]) + abc_ascii("\n")

        text_to_save = df_columns
        for string in dataframe_to_save.index:
            df_values = []
            for column in dataframe_to_save.columns:
                value = str(dataframe_to_save[column][string])
                
                if is_ascii(value):
                    df_values.append(f".{value}.")
                else:
                    df_values.append(abc_ascii(value))
            text_to_save += abc_ascii(",").join(df_values) + abc_ascii("\n")

        old_content = read_file(self.txt_filepath)
        edit_file(self.txt_filepath, text_to_save, notify=False)
        self.csvsave(dataframe_to_save, index=False, notify=False)

        # Check
        if read_file(self.csv_filepath).replace("nan", "") != asciiread_file(self.txt_filepath).replace("nan", ""):
            print(f"{RED}Error while saving user data to the txt file...{RESET}")
            edit_file(self.txt_filepath, old_content)

    def set_time(self, user_id: str | int, *, notify: bool = False) -> None:
        self.edit_value(str(user_id), "last_visited", current_time(), notify=notify)

    def delete_user(self, user_id: str | int, /, *, notify: bool = True) -> None:
        user_id = str(user_id)
        self.__init__()

        if user_id in list(self.users_table.index):
            self.users_table = self.users_table.drop(index=user_id)
            self.csvsave(self.users_table, notify=False)
            remove_usersettings(user_id)
            if notify: print(f"User with id '{user_id}' {GREEN}has been removed{RESET} from the table")
        else:
            print(f"User with telegram id '{user_id}' {YELLOW}has not been found in the user table{RESET}")

    def auto_users_delete(self, *, notify=True):
        active_users_days = timedelta(days=float(get_config("system", "active_users_days")))
        not_active_users = self.users_table[self.users_table["last_visited"] < \
            pd.to_datetime(current_time()) - active_users_days].index

        for user_id in not_active_users:
            self.delete_user(user_id, notify=notify)

class Homework_Table(): # Class to work with tables in csv and txt files
    def __init__(self):
        self.O_csv_filepath = get_config("files", "homework_operational_csv")
        self.C_csv_filepath = get_config("files", "homework_constant_csv")
        self.C_txt_filepath = get_config("files", "homework_constant_txt")

        self.const_table = self.get_C_csv_table().set_index("date")
        self.operat_table = self.get_O_csv_table().set_index("date")
    
    def csvsave(self, dataframe: pd.DataFrame, csv_filepath: str, /, *, index: bool = True, notify: bool = True) -> None:
        try:
            dataframe.to_csv(csv_filepath, index=index)
            if notify: print(f"Homework data {GREEN}has just been saved{RESET} ({current_time()})")
        except Exception as e: print(f"{RED}Error while saving {csv_filepath}: {e}{RESET} ({current_time()})")

    def get_O_csv_table(self) -> pd.DataFrame:
        for _ in range(3):
            try:
                return pd.read_csv(self.O_csv_filepath)

            except pd.errors.EmptyDataError:
                print(f"{YELLOW}Homework (O csv): empty DataFrame.{RESET} Trying to get the table from the C csv file...")
                for _ in range(3):
                    try:
                        edit_file(self.O_csv_filepath, read_file(self.C_csv_filepath))
                        break
                    except FileNotFoundError and FileExistsError:
                        try:
                            prepare_file("homework_constant_csv", "homework_C_csv.csv")
                            self.C_csv_filepath = get_config("files", "homework_constant_csv")

                            edit_file(self.O_csv_filepath, read_file(self.C_csv_filepath))
                            break
                        
                        except Exception as e:
                            print(f"{RED}An error found: {e}{RESET}")
                            exit()
                    
                    except pd.errors.EmptyDataError:
                        self.const_table = self.get_C_csv_table(self.C_csv_filepath)
                        edit_file(self.O_csv_filepath, read_file(self.C_csv_filepath))
                        break
                    except Exception as e:
                        print(f"{RED}An error found: {e}{RESET}")
                        exit()
            
            except FileNotFoundError and FileExistsError:
                try:
                    prepare_file("homework_operational_csv", "homework_O_csv.csv")
                    self.O_csv_filepath = get_config("files", "homework_operational_csv")

                    edit_file(self.O_csv_filepath, read_file(self.C_csv_filepath))
                except FileExistsError and FileNotFoundError:
                    prepare_file("homework_constant_csv", "homework_C_csv.csv")
                    self.C_csv_filepath = get_config("files", "homework_constant_csv")                    
                except Exception as e:
                    print(f"{RED}An error found: {e}{RESET}")
                    exit()

            except Exception as e:
                print(f"{RED}An error found: {e}{RESET}")
                exit()

    def get_C_csv_table(self) -> pd.DataFrame:
        for _ in range(3):
            try:
                return pd.read_csv(self.C_csv_filepath)
            except pd.errors.EmptyDataError:
                print(f"{YELLOW}Homework (C csv): empty DataFrame.{RESET} Trying to get the table from the txt file...")
                for _ in range(2):
                    try:
                        edit_file(self.C_csv_filepath, asciiread_file(self.C_txt_filepath))
                        return pd.read_csv(self.C_csv_filepath)
                    except FileExistsError and FileNotFoundError:
                        prepare_file("homework_constant_txt", "homework_C_txt.txt")
                        self.C_txt_filepath = get_config("files", "homework_constant_txt")
                    except pd.errors.EmptyDataError:
                        print(f"{YELLOW}Homework (C txt): empty DataFrame.{RESET}", end=" ")
                        users_dataframe = pd.DataFrame({
                            "date": [],
                            "algebra": [],
                            "algebra_mse": [],
                            "biology": [],
                            "geografy": [],
                            "geometry": [],
                            "englishlangue": [],
                            "englishlangkr": [],
                            "englishlangev": [],
                            "informaticssv": [],
                            "informaticsnv": [],
                            "history": [],
                            "literature": [],
                            "socialstud": [],
                            "sdmf": [],
                            "russianlang": [],
                            "technology": [],
                            "physics": [],
                            "pe": [],
                            "chemisty": []
                        })
                        print(f"Successfully {GREEN}created{RESET} a new table.")
                        
                        self.data_backup(another_df=users_dataframe, reset_index=False)
                        break

            except FileExistsError and FileNotFoundError:
                try:
                    prepare_file("homework_constant_csv", "homework_C_csv.csv")
                    self.C_csv_filepath = get_config("files", "homework_constant_csv")

                    edit_file(self.C_csv_filepath, asciiread_file(self.C_txt_filepath))
                except FileExistsError and FileNotFoundError:
                    self.C_txt_filepath = file_not_found_error_solve("homework_C_txt.txt")
                    change_config("files", "homework_constant_txt")            
                except Exception as e:
                    print(f"{RED}An error found: {e}{RESET}")
                    exit()

            except Exception as e:
                print(f"{RED}An error found: {e}{RESET}")
                exit()

    def add_homework(self, subject: str, new_value: str | pd.Timestamp, /,
                   *, _abc_ascii: bool = False, _ascii_abc: bool = False, \
                    notify: bool = True, filepath: None | str = None, \
                    date: str | None = None) -> None:
        if date == None: date = current_day()
        if _abc_ascii: homework = abc_ascii(new_value)
        elif _ascii_abc: homework = ascii_abc(new_value)
        else: homework = new_value

        if filepath: homework += f"&&&{filepath}" # homework&&&filepath

        self.__init__()
        if subject not in self.operat_table.columns or self.operat_table[subject].dtype != object:
            self.operat_table[subject] = self.operat_table[subject].astype(object)
                
        self.operat_table.at[str(date), subject] = str(homework)
        self.csvsave(self.operat_table, self.O_csv_filepath, notify=notify)

    def get_homework(self, subject: str, homework_date: str, *, _abc_ascii: bool = False, _ascii_abc: bool = False) -> list[str, list[str, str]] | list[str, False]: #returns homework: [homework, [file1, file2]]
        self.__init__()
        data = str(self.operat_table[subject][homework_date]).split("&&&")
        if len(data) == 1: datafile = False
        else: datafile = data[1:]

        if _abc_ascii: data[0] = abc_ascii(data[0])
        if _ascii_abc: data[0] = ascii_abc(data[0])

        return[data[0], datafile]

    def data_backup(self, *, another_df: bool | pd.DataFrame = False, reset_index: bool = True, notify: bool = True) -> None:
        if notify: print(f"Saving homework data to txt file...")

        if str(another_df) == "False":
            self.__init__()
            dataframe_to_save = self.operat_table
        else:
            dataframe_to_save = another_df

        prepare_file("homework_operational_csv", "homework_O_csv.csv", notify=notify)
        self.O_csv_filepath = get_config("files", "homework_operational_csv")
        prepare_file("homework_constant_csv", "homework_C_csv.csv", notify=notify)
        self.C_csv_filepath = get_config("files", "homework_constant_csv")
        prepare_file("homework_constant_txt", "homework_C_txt.txt", notify=notify)
        self.C_txt_filepath = get_config("files", "homework_constant_txt")

        if reset_index:
            dataframe_to_save = dataframe_to_save.reset_index()
            dataframe_to_save.rename(columns={'index': 'date'}, inplace=True)
        
        df_columns = abc_ascii(",").join([abc_ascii(i) for i in dataframe_to_save.columns]) + abc_ascii("\n")

        text_to_save = df_columns
        for string in dataframe_to_save.index:
            df_values = []
            for column in dataframe_to_save.columns:
                value = str(dataframe_to_save[column][string])
                
                if is_ascii(value):
                    df_values.append(f".{value}.")
                else:
                    df_values.append(abc_ascii(value))
            text_to_save += abc_ascii(",").join(df_values) + abc_ascii("\n")
        
        old_txtcontent = read_file(self.C_txt_filepath)
        old_csvcontent = read_file(self.C_csv_filepath)

        self.csvsave(dataframe_to_save, self.O_csv_filepath, index=False, notify=notify)
        self.csvsave(dataframe_to_save, self.C_csv_filepath, index=False, notify=notify)
        edit_file(self.C_txt_filepath, text_to_save, notify=notify)

        # Check
        if read_file(self.C_csv_filepath).replace("nan", "") != asciiread_file(self.C_txt_filepath).replace("nan", "") and read_file(self.C_csv_filepath).replace("nan", "") != read_file(self.O_csv_filepath).replace("nan", ""):
            print(f"{RED}Error while saving homework data to the txt file...{RESET}")
            edit_file(self.C_txt_filepath, old_txtcontent, notify=notify)
            edit_file(self.C_csv_filepath, old_csvcontent, notify=notify)

    def remove_unnecessary_homeworks(self, *, another_df: bool | pd.DataFrame = False, notify: bool = True) -> None: # removes unnecessary homeworks from dir ED_homework_docs
        ed_homework_docs_dir = get_homework_docs_dirpath()
        files = get_files_from_dir(ed_homework_docs_dir) # filename = subject_date
        max_days_ret = float(get_config("system", "homework_max_days_retention"))

        files_removed_cnt = 0
        for file in files:
            try:
                if pd.to_datetime(file.split(".")[0].split("_")[1]) < dt.now() - timedelta(days=max_days_ret):
                    remove_file(ed_homework_docs_dir + "/" + file)
                    files_removed_cnt += 1
            except: pass

        if str(another_df) == "False": df = self.operat_table
        else: df = another_df

        old_df_len = len(df)
        df = df[pd.to_datetime(df.index) >= dt.now() - timedelta(days=max_days_ret)]
        new_df_len = len(df)
        self.csvsave(df, self.O_csv_filepath, notify=notify)

        return f"Unnecessary homeworks removed: files - {files_removed_cnt}, texts - {old_df_len - new_df_len}"

# Bot functions | texts for user interaction
def get_texts() -> dict:
    texts_dict = {}
    for text in get_configs()["texts"]:
        texts_dict[text] = ascii_abc(get_config("texts", text))
    for text in get_configs()["subjects"]:
        texts_dict[text] = ascii_abc(get_config("subjects", text))
    for text in get_configs()["categories"]:
        texts_dict[text] = ascii_abc(get_config("categories", text))
    for text in get_configs()["weekdays"]:
       texts_dict[text] = ascii_abc(get_config("weekdays", text))
    return texts_dict
texts_dict = get_texts()

# Start
def user_registration(user_id: str | int, username: str, users_table: Users_Table) -> str:
    try:
        users_table.__init__()
        users_table.add_user(str(user_id), abc_ascii(username), "Aver")
        return abc_ascii(username)
    except: return abc_ascii("NameError")

def greetings(username: str) -> str:
    time_now = int(current_time().split()[1].split(":")[0])

    if 0 <= time_now < 4:
        time_of_day = "N"
    elif 4 <= time_now < 12:
        time_of_day = "M"
    elif 12 <= time_now < 18:
        time_of_day = "D"
    else:
        time_of_day = "E"
    
    return texts_dict[f"greeting1{time_of_day.lower()}"] + ascii_abc(username) + texts_dict["greeting2"]

def system_greetings(username: str) -> str:
    return f"{texts_dict['welcome_to_system']} {ascii_abc(username)}"

def get_username(userstable: Users_Table, user_id: int | str, full_name: str) -> str:
        user_id = str(user_id)
        userstable.__init__()
        try: return userstable.users_table["username"].loc[user_id]
        except KeyError: return user_registration(user_id, full_name, userstable)

def get_usercategory(user_id: str | int, userstable: Users_Table, full_name: str) -> str:
    userstable.__init__()
    try: return userstable.users_table["category"].loc[user_id]
    except KeyError:
        user_registration(user_id, full_name, userstable)
        return "Aver"

# Settings / support
def settings_message(user_id: int | str, username: str, category: str, tgusername: str) -> str:
    text =  f"{texts_dict['settings_text']}\n\n" + \
            f"{texts_dict['id_text']}<code>{user_id}</code>\n" + \
            f"{texts_dict['name_text']}{ascii_abc(username)}\n" + \
            f"{texts_dict['username_text']}@{tgusername}\n" + \
            f"{texts_dict['category_text']}<u>{category}</u> ({texts_dict[f'description{category.lower()}']})\n\n" + \
            f"{texts_dict['settings_function_text']}"
    return text

def set_stock_buttons(user_id:  int | str) -> str:
    set_stock_usersettings(user_id)
    return texts_dict["stock_sets_true"]

def support_notify_edit_category(user_id: str | int, username: str, category_wanted: str, tgusername: str) -> str:
    return  f"{texts_dict['edit_category_request']}\n{texts_dict['id_text']}<code>{user_id}</code>\n" + \
            f"{texts_dict['name_text']}{ascii_abc(username)}\n" + \
            f"{texts_dict['username_text']}@{tgusername}\n" + \
            f"{texts_dict['wanted_category']} <u>{category_wanted}</u>"

def accepted_request_edit_category(user_id: int | str, users_table: Users_Table, new_category: str) -> str:
    users_table.edit_value(user_id, "category", new_category, notify=False)
    return f"{texts_dict['edit_category_u_accepted_request']} <u>{new_category}</u>."

def true_password_edit_category(user_id: int | str, users_table: Users_Table, new_category: str) -> str:
    users_table.edit_value(user_id, "category", new_category, notify=False)
    return f"{texts_dict['edit_category_request_accepted']} <u>{new_category}</u> !\n{texts_dict['press_start_to_update']}"

def asking_support_message(user_id: str | int, username: str, tgusername: str, message_text: str) -> str:
    return  texts_dict["sup_request_text"] + \
            f"{texts_dict['id_text']}<code>{user_id}</code>\n" + \
            f"{texts_dict['name_text']}{ascii_abc(username)}\n" + \
            f"{texts_dict['username_text']}@{tgusername}\n" + \
            texts_dict["act_question"] + \
            message_text

def support_answer(answer_text: str, creator_name: str) -> str:
    return  texts_dict["message_from_sup"] + \
            f"{answer_text}\n\n" + \
            f"<i>{texts_dict['ps_1']} <b>{ascii_abc(creator_name)}</b></i>"

# Lesson shedule
def get_lesson_shedule(day: str) -> str:
    ls = get_config("lessonshedules", f"{day}_ls")
    is_temporary = 0
    if ls != get_config("lessonshedules", f"{day}_old_ls"): is_temporary = 1
    ls = ascii_abc(ls)

    if day in ["wednesday",  "friday"]:
        return f"<i>{texts_dict['ls_on_text'] if not is_temporary else texts_dict['temp_ls_on_text']} <b>{texts_dict[day][:-1]}y</b></i>\n\n{ls}"
    else: return f"<i>{texts_dict['ls_on_text'] if not is_temporary else texts_dict['temp_ls_on_text']} <b>{texts_dict[day]}</b></i>\n\n{ls}"

def edit_lesson_shedule(day: str, new_value: str, _abc_ascii = True) -> str:
    if _abc_ascii: new_value = abc_ascii(new_value)
    change_config("lessonshedules", f"{day}_ls", new_value)
    return texts_dict["ls_edited"]

# Management
def delay_time() -> float:
    try: return float(get_config("system", "delay"))
    except: return 1.5

def get_user_name(user_id: int | str, users_table:  pd.DataFrame) -> str:
    try:
        return ascii_abc(users_table["username"].loc[str(user_id)])
    except:
        return ""

def user_info(user_id: int | str, users_table:  pd.DataFrame) -> str:
    name = ascii_abc(users_table["username"].loc[str(user_id)])
    category = users_table["category"].loc[str(user_id)]
    last_visited = users_table["last_visited"].loc[str(user_id)]

    return  f"{texts_dict['user_text']}\n" + \
            f"{texts_dict['id_text']}<code>{user_id}</code>\n" + \
            f"{texts_dict['name_text']}{name}\n" + \
            f"{texts_dict['category_text']}<u>{category}</u>\n" + \
            f"{texts_dict['last_visited_text']}{last_visited}\n\n" + \
            texts_dict["change_text"]

def message_for_user(message_text: str, creator_name: str) -> str:
    return  f"{texts_dict['message_from_creator_text']}\n\n" + \
            f"{message_text}\n\n" + \
            f"<i>{texts_dict['ps_1']} <b>{ascii_abc(creator_name)}</b></i>"

def edit_parameter_value(section: str, parameter_name: str, new_value: str, *, _abc_ascii: bool | None = None, change=True) -> str:
    if _abc_ascii == True: new_value = abc_ascii(new_value)
    if _abc_ascii == None: new_value = abc_ascii(new_value) if is_ascii(get_config(section, parameter_name)) else new_value
    if change: change_config(section, parameter_name, new_value)
    return f"<b>Section</b>: {section}\n<b>Parameter</b>: {parameter_name}\n- {texts_dict['changed_text']}"

def edit_userparameter_value(user_id: str, parameter_name: str, new_value: str, *, _abc_ascii: bool | None = None, change=True) -> str:
    if _abc_ascii == True: new_value = abc_ascii(new_value)
    if _abc_ascii == None: new_value = abc_ascii(new_value) if is_ascii(get_userconfig(user_id, parameter_name)) else new_value
    if change == True: change_userconfig(user_id, parameter_name, new_value)
    return f"<b>ID</b>: <code>{user_id}</code>\n<b>Parameter</b>: {parameter_name}\n- {texts_dict['changed_text']}"

def global_notify(content: str, creator_name: str) -> str:
    return  f"{texts_dict['notify_text']}\n\n" + \
            f"{content}\n\n" + \
            f"<i>{texts_dict['ps_1']} <b>{ascii_abc(creator_name)}</b></i>"

def get_statistics(users_table: Users_Table) -> str:
    df = users_table.users_table
    list_online = df[df['last_visited'] >= dt.now() - timedelta(minutes=5)]
    list_today = df[df['last_visited'] >= current_day()]

    def get_limit(limit: str, *, read: bool = True) -> int:
        try:
            return int(get_config("system", limit, read=read))
        except:
            return 5

    text =  f"{texts_dict['statistics_text']}\n\n" + \
            f"{texts_dict['users_cnt']} {len(list(df.index))}\n" + \
            f"{texts_dict['users_online']} {len(list_online)}\n" + \
            ("    " + "\n    ".join(list_online.index[:get_limit("statistics_cnt_online", read=False)]) + "\n")*\
            (len(list_online.index[:get_limit("statistics_cnt_online", read=False)]) != 0) + \
            f"{texts_dict['users_today']} {len(list_today)}\n" + \
            ("    " + "\n    ".join(list_today.index[:get_limit("statistics_cnt_today", read=False)]) + "\n")*\
            (len(list_today.index[:get_limit("statistics_cnt_today", read=False)]) != 0)

    return text

def get_full_statistics(users_table: Users_Table) -> str:
    df = users_table.users_table
    df["last_visited"] = pd.to_datetime(df["last_visited"], format="%Y-%m-%d %H:%M:%S")

    prepare_file("statistics", "ED_statistics.txt", notify = False)
    statistics_filepath = get_config("files", "statistics")
    system_folder = get_system_docs_dirpath()

    userspie_filepath = f"{system_folder}/stat_userspie{current_time()[11:][:8]}.html"
    rushhourbar_filepath = f"{system_folder}/stat_rushhour{current_time()[11:][:8]}.html"
    dailyuserscnt_bar_filepath = f"{system_folder}/stat_dailyuserscnt{current_time()[11:][:8]}.html"

    def users_pie() -> None:
        user_categories_cnt_df = df.groupby('category', observed=False).agg({"category": "count"})["category"]
        user_categories_cnt = [
            user_categories_cnt_df["Dev"],
            user_categories_cnt_df["MAdm"],
            user_categories_cnt_df["Adm"],
            user_categories_cnt_df["Aver"],
            user_categories_cnt_df["Ban"]
        ]
        user_categories = [
            f"Dev - {user_categories_cnt[0]}", f"MAdm - {user_categories_cnt[1]}", 
            f"Adm - {user_categories_cnt[2]}", f"Aver - {user_categories_cnt[3]}",
            f"Ban - {user_categories_cnt[4]}"
        ]

        pull = [0]*5
        pull[0] = 0.1

        fig = go.Figure()
        fig.add_trace(go.Pie(values=user_categories_cnt, labels=user_categories,
            sort=False, pull=pull, hole=0.87))

        fig.update_layout(
            title=texts_dict["user_categories"],
            title_x = 0.5,
            margin = dict(l=0, r=0, t=150, b=0),
            legend_orientation = "h",
            font_size = 50)
        
        fig.write_html(userspie_filepath)

    def rushhour_bar() -> None:
        rushhour_statistics = list(map(
            lambda x: x.split(":")[1].split("!"),
            read_file(statistics_filepath).strip("\n").split("\n")[:-1]
        ))
        rushhour_statistics = sorted(rushhour_statistics, key=lambda x: int(x[1]))

        def func(mas: list) -> list[list, list]:
            mas2 = []
            mas3 = []
            i = 0
            lm = len(mas)

            while i < lm:
                if int(mas[i][1]) in mas2:
                    if mas3[-1] < int(mas[i][2]): mas3[-1] = int(mas[i][2])
                else:
                    mas2.append(int(mas[i][1]))
                    mas3.append(int(mas[i][2]))
                
                i += 1

            return [mas2, mas3]

        hours = list(range(0, 24))
        rush_hours, users_cnt = func(rushhour_statistics)
        rush_cnt = [[j[1] for j in rushhour_statistics].count(str(i)) for i in hours]
        users_cnt_on_rush_hours = [0] * 24
        for i in range(len(rush_hours)): users_cnt_on_rush_hours[rush_hours[i]] = users_cnt[i]

        fig = go.Figure(data=[go.Bar(
            x = hours, y = rush_cnt,
            text=users_cnt_on_rush_hours,
            marker_color = "rgb(0, 128, 128)"
        )])
        fig.update_layout(
            xaxis = dict(
                title = texts_dict["hours"],
                tickvals=list(range(24))
            ),
            yaxis = dict(
                title = texts_dict["count_of_days"],
                type='linear', tickmode='linear', dtick=1
            ),
            title = texts_dict["rush_hours"],
            title_x = 0.5,
            font_size = 30,
            plot_bgcolor='rgba(240, 240, 240, 1)'
        )

        fig.write_html(rushhourbar_filepath)

    def daily_userscnt() -> None:
        current_year = str(dt.now().year)

        dailyuserscnt_statistics = list(map(
            lambda x: x.split("!")[0].split(":"),
            read_file(statistics_filepath).strip("\n").split("\n")[:-1]
        ))
        days = {
            1: [], 2: [], 3: [], 4: [], 5: [], 6: [],
            7: [], 8: [], 9: [], 10: [], 11: [], 12: []
        }
        users_cnt = {
            1: [], 2: [], 3: [], 4: [], 5: [], 6: [],
            7: [], 8: [], 9: [], 10: [], 11: [], 12: []
        }
        for day in dailyuserscnt_statistics:
            if day[0][:4] == current_year:
                days[int(day[0][5:][:2])].append(int(day[0][8:][:2]))
                users_cnt[int(day[0][5:][:2])].append(int(day[1]))
        
        trace_list = [
            go.Bar(visible = True, x=days[1], y=users_cnt[1],
                name="", width=1, marker_color = 'rgba(0, 100, 200, 0.6)'),
            go.Scatter(visible = True, x=days[1], y=users_cnt[1], mode='lines+markers',
                name="", line=dict(width=5), marker=dict(size=20, color='rgb(255, 140, 0)'))
        ]

        for i in range(2, 13):
            trace_list.append(go.Bar(visible = False, x=days[i], y=users_cnt[i], name="", width=1))
            trace_list.append(go.Scatter(visible = False, x=days[i], y=users_cnt[i], mode='lines+markers', name="", line=dict(width=100), marker=dict(size=12, color='blue')))

        fig = go.Figure(data=trace_list)

        steps = []
        for i in range(12):
            step = dict(
                method = 'restyle',  
                args = ['visible', [False] * 24],
            )
            step['args'][1][2*i] = True
            step['args'][1][2*i+1] = True
            steps.append(step)

        sliders = [dict(
            steps = steps,
        )]

        fig.layout.sliders = sliders

        fig.update_layout(
            xaxis = dict(
                title = texts_dict["day"],
                tickvals=list(range(1, 32))
            ),
            yaxis = dict(
                title = texts_dict["userscnt_day"]
            ),
            sliders=[dict(steps=[dict(label = i) for i in texts_dict["months_short"].split(" ")])],
            title = texts_dict["users_count"],
            title_x = 0.5,
            font_size = 30
        )

        fig.write_html(dailyuserscnt_bar_filepath)

    users_pie()
    rushhour_bar()
    daily_userscnt()
    return [userspie_filepath.split("/")[-1], rushhourbar_filepath.split("/")[-1], dailyuserscnt_bar_filepath.split("/")[-1]]

def get_developers_id(users_df: pd.DataFrame, self_id: str | int, *, remove_self = True) -> set:
    developers_id_list = set(list(map(str, users_df[users_df["category"] == "Dev"].index)))
    if len(developers_id_list) == 0:
        developers_id_list = set([get_config("system", "developer_id")]) #The Developer
    if remove_self:
        try: developers_id_list.remove(str(self_id))
        except: pass
    return developers_id_list

def get_main_admins_id(users_df: pd.DataFrame, self_id: str | int) -> set:
    main_admins_id_list = set(list(map(str, users_df[users_df["category"] == "MAdm"].index)))
    try: main_admins_id_list.remove(str(self_id))
    except: pass
    if len(main_admins_id_list) == 0:
        main_admins_id_list = get_developers_id(users_df, self_id)
    return main_admins_id_list

def get_admins_id(users_df: pd.DataFrame, self_id: str | int) -> set:
    admins_id_list = set(list(map(str, users_df[users_df["category"] == "Adm"].index)))
    try: admins_id_list.remove(str(self_id))
    except: pass
    if len(admins_id_list) == 0:
        admins_id_list = get_main_admins_id(users_df, self_id) #The Developer
    return admins_id_list

def mainconfigs_edited_message(creatorname: str, section: str, parameter_name: str, new_value: str, old_config: str) -> str:
    if is_ascii(old_config): old_config = ascii_abc(old_config)
    return  f"{texts_dict['mainconf_edited1']} <b>{ascii_abc(creatorname)}</b> {texts_dict['mainconf_edited2']}:\n" + \
            f"{section}, {parameter_name}\n" + \
            f"'{old_config}' -> '{new_value}'"

def userconfigs_edited_message(creatorname: str, user_id: str, parameter_name: str, new_value: str, old_config: str) -> str:
    if is_ascii(old_config): old_config = ascii_abc(old_config)
    return  f"{texts_dict['mainconf_edited1']} <b>{ascii_abc(creatorname)}</b> {texts_dict['userconf_edited2']} <code>{user_id}</code>\n" + \
            f"<b>Parameter</b>: {parameter_name}\n" + \
            f"'{old_config}' -> '{new_value}'"

def userdata_edited_message(creatorname: str, edited_user_id: int | str, datasection: str, new_value: str, old_value: str) -> str:
    if is_ascii(old_value): old_value = ascii_abc(old_value)
    if datasection == "category":
        return  f"{texts_dict['mainconf_edited1']} {ascii_abc(creatorname)} {texts_dict['userdata_edited2']} <code>{edited_user_id}</code>:\n"  + \
                f"<b>Parameter</b>: {datasection}\n'{texts_dict[f'short_description{old_value.lower()}']}' -> '{texts_dict[f'short_description{new_value.lower()}']}'"
    else:
        return  f"{texts_dict['mainconf_edited1']} {ascii_abc(creatorname)} {texts_dict['userdata_edited2']} <code>{edited_user_id}</code>:\n"  + \
                f"<b>Parameter</b>: {datasection}\n'{old_value}' -> '{new_value}'"

def update_texts_dict():
    global texts_dict
    texts_dict = get_texts()

def sql_query(df: pd.DataFrame, query: str, *, file: bool = False) -> str:
    users_csv = df
    homework_csv = df
    result = sqldf(query=query)

    if file:
        folderpath = get_system_docs_dirpath()
        result.to_csv(f"{folderpath}/SQL_query.csv")

def get_sql_query_message(df: pd.DataFrame, tablename: str) -> str:
    df = df.reset_index()
    
    if tablename == "users_csv":
        first_key = "telegram_id"
        df.rename(columns={'index': 'date'}, inplace=True)
    
    elif tablename == "homework_csv":
        first_key = "date"
        df.rename(columns={'index': 'date'}, inplace=True)
    
    columns = df.columns

    sep_string = "\n    "
    return  f"{texts_dict['enter_sql_query_text']}\n" + \
            f"<b>{texts_dict['table_text']}</b>: {tablename}\n" + \
            f"<b>{texts_dict['columns_text']}</b>:\n    {sep_string.join(columns)}\n" + \
            f"<b>{texts_dict['first_key_text']}</b>: {first_key}"

def load_statistics():
    users_table = Users_Table().users_table
    prepare_file("statistics", "ED_statistics.txt", notify = False)
    statistics_filepath = get_config("files", "statistics")
    current_hour = int(dt.now().hour)
    text = ""

    if ":" in read_file(statistics_filepath).strip("\n"):
        text = f"{len(users_table[users_table['last_visited'] >= dt.now() - timedelta(hours=1)])},"
        
        #date:usrs_hour0,usrs_hour1,
        add_text_to_file(statistics_filepath, text, notify=False)
    else:
        text = f"{current_day()}:"
        add_text_to_file(statistics_filepath, text, notify=False)

    if current_hour == 0:
        all_statistics_text = read_file(statistics_filepath).strip("\n")
        try:
            rush_hour = list(map(int, all_statistics_text.split("\n")[-1].split(":")[1].split(",")[:-1]))
            rush_hour = f"{rush_hour.index(max(rush_hour))}!{max(rush_hour)}"
            s = "\n"
            text = f"{all_statistics_text.split(s)[-1].split(':')[0]}:" + \
                f"{len(users_table[users_table['last_visited'] >= dt.now() - timedelta(days=1)])}!" + \
                f"{rush_hour}\n{current_day()}:"
            
            # date:usrs_today!rush_hour!usrs_rush_hour
            edit_file(statistics_filepath, ("\n".join(all_statistics_text.split("\n")[:-1]) + "\n" + text).lstrip("\n"), notify=False)
        except:
            text = f"{current_day()}:"
            edit_file(statistics_filepath, text, notify=False)

# Homework
def homework_message(homework_table: pd.DataFrame) -> list:
    text = texts_dict["homework_message"]
    currentday = current_day()
    currentweekday = dt.weekday(dt.now())

    subjects_dict = {}
    for subject in homework_table:
        subject = str(subject).lower()
        subject_days = []
        subject_rus = texts_dict[subject + "_text"]
        if "englishlang" in subject: subject_rus = subject_rus[:-3]
        if "informatics" in subject: subject_rus = subject_rus[:-3]

        if subject_rus in ascii_abc(get_config("lessonshedules", "monday_ls")): subject_days.append(0)
        if subject_rus in ascii_abc(get_config("lessonshedules", "tuesday_ls")): subject_days.append(1)
        if subject_rus in ascii_abc(get_config("lessonshedules", "wednesday_ls")): subject_days.append(2)
        if subject_rus in ascii_abc(get_config("lessonshedules", "thursday_ls")): subject_days.append(3)
        if subject_rus in ascii_abc(get_config("lessonshedules", "friday_ls")): subject_days.append(4)
        
        subj_data = list(homework_table[subject].dropna().index)

        def is_hw_yes() -> bool:
            subject_previous_weekday = None
            for day in range(len(subject_days)):
                if currentweekday > subject_days[-(day+1)]:
                    subject_previous_weekday = subject_days[-(day+1)]
                    break
            else:
                try:
                    if subject_previous_weekday == None: subject_previous_weekday = subject_days[-1]
                except:
                    subject_previous_weekday = 6

            weekday_delta = currentweekday - subject_previous_weekday
            if weekday_delta < 0: weekday_delta = 7 + weekday_delta
            subject_previous_day = pd.to_datetime(currentday) - timedelta(days=weekday_delta)

            try: return True if pd.to_datetime(subj_data[-1]) + timedelta(hours=8) > subject_previous_day else False
            except: return False

        if currentday in subj_data: status = texts_dict["hw_new"]
        elif len(subj_data) == 0: status = texts_dict["hw_no"]
        elif is_hw_yes(): status = texts_dict["hw_yes"]
        else: status = texts_dict["hw_old"]
        
        subjects_dict[subject] = {
            "text": texts_dict[f"{subject}_text"] + " " + status,
            "callback": f"get_homework!{subject}"
        }
    
    return [text, subjects_dict]

def get_homeworks_message(subject: str, homework_table: pd.DataFrame) -> list:
    text1 = f"{texts_dict['subject_text']} <b>{texts_dict[f'{subject}_text']}</b>\n"
    weekdays = {0: texts_dict["monday_short"], 1: texts_dict["tuesday_short"], 
        2: texts_dict["wednesday_short"], 3: texts_dict["thursday_short"], 
        4: texts_dict["friday_short"], 5: texts_dict["saturday_short"], 
        6: texts_dict["sunday_short"]}

    hw_list = []
    date_list = []
    for i in homework_table.index:
        value = homework_table[subject][str(i)]
        if str(value) == "nan": continue
        hw_list.append(f"{str(i)} ({weekdays[int(dt.weekday(pd.to_datetime(str(i))))]})")
        date_list.append(i)
    
    text2 = texts_dict['no_hw_text'] if len(hw_list) == 0 else texts_dict['select_hw_text']

    return [text1 + text2, hw_list, date_list]

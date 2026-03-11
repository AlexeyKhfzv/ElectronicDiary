import os

RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'

def file_not_found_error_solve(file_name: str) -> str:
    while True:
        print(f"{RED}Cannot find file named '{file_name}'. Enter full path to file '{file_name}' (Example: /home/usr/folder/{file_name}){RESET}")
        print(f"{RED}(X - Exit){RESET}")
        filepath = input("Enter path: ")
        if filepath == 'X' or filepath == 'x':
            exit()
        try:
            if os.path.isfile(filepath):
                print(f"{GREEN}The file has been found.{RESET}")
            else:
                raise FileExistsError
            break
        except:
            continue
    return filepath

try:
    from ED_file_manager import get_directory, edit_file, search_file
except ModuleNotFoundError:
    print(f"{RED}Error while importing the file manager. Please, put file 'ED_file_manager.py' in this folder or download new.{RESET}")
    exit()

try:
    from ED_config_path import CONFIG_PATH # This config-opening program needs additional file 'ED_config_path', from which this config-file reader can import constant 'CONFIG_PATH' with full path to your config-file.
    ED_config_path = CONFIG_PATH
except Exception as e:
    file_name = "ED_config_path.py"
    print(f"{RED}Error while getting path to ED_configuration file. Opening new file '{file_name}'...{RESET}")
    edit_file(f"{get_directory('ED_Configfile_reader.py')}/{file_name}", "CONFIG_PATH = None")
    ED_config_path = None

from configparser import ConfigParser
config = ConfigParser() # Main configuration
usersconfig = ConfigParser() # Users configuration

try:
    print("Reading ED_configuration file...")
    config.read(ED_config_path)
    check_var = config['system']['check_var']
except:
    print(f"{YELLOW}Error with opening ED_configuration file: trying to search this file...{RESET}")
    try:
        ED_config_path = search_file("ED_mainconfigs.ini")
    except:
        ED_config_path = file_not_found_error_solve("ED_mainconfigs.ini")
    
    try:
        print(f"Trying to set new path to the config_path file...")
        edit_file(search_file("ED_config_path.py"), f"CONFIG_PATH = '{ED_config_path}'")
        print(f"{GREEN}Successfully set new path in the config_path file{RESET}")
    except:
        edit_file(file_not_found_error_solve('ED_config_path.py'), f"CONFIG_PATH = '{ED_config_path}'")
        print(f"{GREEN}Successfully set new path in the config_path file{RESET}")

    config.read(ED_config_path)

# Functions for import
def get_config(section: str, parameter_name: str, /, *, read: bool = True) -> str:
    try:
        if read: config.read(ED_config_path)
        return config[section][parameter_name]
    except:
        print(f"{RED}Error: wrong section or parameter name ({section}, {parameter_name})!{RESET}")
        return None

def change_config(section: str, parameter_name: str, new_value: any, /, *, update: bool = True) -> None:
    if update: config.read(ED_config_path)
    config[section][parameter_name] = new_value
    with open(ED_config_path, mode = "w") as configfile:
        config.write(configfile)

def prepare_file(parameter: str, filename: str, /, *, notify: bool = True) -> None:
    section = "files"
    if os.path.isfile(get_config(section, parameter)):
        if notify: print(f"Parameter '{parameter}' in section '{section}' [ {GREEN}FOUND{RESET} ]")
        return True
    else:
        print(f"Parameter '{parameter}' in section '{section}' [ {YELLOW}WRONG FILE PATH{RESET} ]")
        try:
            change_config(section, parameter, search_file(filename))
            print(f"Parameter '{parameter}' in section '{section}' [ {GREEN}FOUND AND CHANGED{RESET} ]")
            return True
        except:
            try:
                print(f"Parameter '{parameter}' in section '{section}' [ {RED}CREATING NEW '{filename}'!{RESET} ]")
                new_filename = f"{os.getcwd()}/{filename}"
                with open(new_filename, "w"): pass
                change_config(section, parameter, new_filename)
            except: 
                print(f"Parameter '{parameter}' in section '{section}' [ {RED}CAN'T CREATE '{filename}'!{RESET} ]")
                file_not_found_error_solve(filename)
            finally:
                print(f"Parameter '{parameter}' in section '{section}' [ {GREEN}CREATED{RESET} ]")

def get_homework_docs_dirpath() -> str:
    return "/".join(get_config("files", "usersconfigs").split("/")[:-2]) + "/ED_homework_docs"

def get_system_docs_dirpath() -> str:
    return "/".join(get_config("files", "usersconfigs").split("/")[:-2]) + "/ED_system/ED_system_docs"

def get_data_dirpath() -> str:
    return "/".join(get_config("files", "usersconfigs").split("/")[:-1])

try:
    prepare_file("usersconfigs", "ED_usersconfigs.ini")
    ED_usersconfigs_path = get_config("files", "usersconfigs")
    usersconfig.read(ED_usersconfigs_path)
except Exception as e:
    print(f"{RED}Error: {e}{RESET}.")
    exit()

# Functions for import
def set_stock_usersettings(user_id: str | int) -> None:
    user_id = str(user_id)
    usersconfig.read(ED_usersconfigs_path)

    try: usersconfig.add_section(user_id)
    except: pass

    usersconfig[user_id]["start_button"] = "a47a115a116a97a114a116"
    usersconfig[user_id]["homework_button"] = "a128218a32a1044a1086a1084a1072a1096a1085a1080a1077a32a1079a1072a1076a1072a1085a1080a1103"
    usersconfig[user_id]["settings_button"] = "a9881a65039a32a1053a1072a1089a1090a1088a1086a1081a1082a1080"
    usersconfig[user_id]["lessonshedule_button"] = "a128198a32a1056a1072a1089a1087a1080a1089a1072a1085a1080a1077"
    usersconfig[user_id]["management_button"] = "a128272a32a1059a1087a1088a1072a1074a1083a1077a1085a1080a1077"
    usersconfig[user_id]["notify_aun"] = "1" # all users notify
    usersconfig[user_id]["notify_ude"] = "0" # userdata edited
    usersconfig[user_id]["notify_mce"] = "0" # mainconfigs edited
    usersconfig[user_id]["notify_err"] = "1" # errors
    usersconfig[user_id]["notify_sup"] = "1" # support

    with open(ED_usersconfigs_path, mode = "w") as usersconfigs_file:
        usersconfig.write(usersconfigs_file)

def remove_usersettings(user_id: str | int) -> None:
    try:
        usersconfig.remove_section(str(user_id))
        with open(ED_usersconfigs_path, mode = "w") as usersconfigs_file:
            usersconfig.write(usersconfigs_file)
    except KeyError:
        print(f"{RED}Error: wrong user id ({user_id})!{RESET}")
        return None
    except:
        print(f"{RED}Something gone wrong while changing configuration in file {ED_usersconfigs_path}. "
              f"Try to delete section '{user_id}' by self.{RESET}")

def get_userconfig(user_id: str | int, parameter_name: str, /) -> str:
    try:
        usersconfig.read(ED_usersconfigs_path)
        return usersconfig[str(user_id)][parameter_name]
    except KeyError:
        set_stock_usersettings(user_id)
        usersconfig.read(ED_usersconfigs_path)
        return usersconfig[str(user_id)][parameter_name]
    except:
        print(f"{RED}Error: wrong user id or parameter name ({user_id}, {parameter_name})!{RESET}")
        return None

def change_userconfig(user_id: str | int, parameter_name: str, new_value: any, /, *, update=True) -> None:
    try:
        if update: usersconfig.read(ED_usersconfigs_path)
        usersconfig[str(user_id)][parameter_name] = new_value
        with open(ED_usersconfigs_path, mode = "w") as usersconfigs_file:
            usersconfig.write(usersconfigs_file)
    except:
        print(f"{RED}Something gone wrong while changing configuration in file {ED_usersconfigs_path}. "
              f"Try to change config parameter '{parameter_name}' value to '{new_value}' by self.{RESET}")

def get_configs() -> ConfigParser:
    return config

def get_usersconfig() -> ConfigParser:
    return usersconfig

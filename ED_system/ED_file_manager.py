import os

RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m'

# Functions which convert text to ASCII code and back.
def abc_ascii(text: str) -> str:
    if text == "":
        return ""
    return "a" + "a".join([str(ord(symb)) for symb in text])

def ascii_abc(ascii_string: str) -> str:
    try:
        return "".join([chr(int(i)) for i in ascii_string.strip().split("a")[1:]])
    except:
        return ""

def is_ascii(text: str) -> bool:
    return True if abc_ascii(ascii_abc(text)) == text else False

def search_file(file_name: str) -> str:
    for root, _, files in os.walk(os.getcwd()):
        for file in files:
            if file == file_name:
                file_path = os.path.join(root, file)
                return file_path
    
    raise FileExistsError(f"No file named '{file_name}' in storage '{os.getcwd()}'.")

def create_file(file_path: str) -> None:
    try:
        with open(file_path, mode="x"):
            pass
        print(f"Successfully {GREEN}created{RESET} file '{file_path}'.")

    except FileExistsError:
        print(f"{RED}There is one more file '{file_path}' in the directory!{RESET}")

    except Exception as e:
        print(f"{RED}An error found while creating file '{file_path}': {e}{RESET}")

def remove_file(file_path: str) -> None:
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"{RED}An error found while removing file '{file_path}': {e}{RESET}")

def edit_file(file_path: str, new_text: str, *, notify: bool = True) -> None:
    try:
        with open(file_path, mode="w") as file:
            file.write(new_text)
        if notify: print(f"File '{file_path}' {GREEN}has been edited{RESET} successfully.")

    except Exception as e:
        print(f"{RED}An error found while editing file '{file_path}': {e}{RESET}")

def add_text_to_file(file_path: str, additional_text: str, *, notify: bool = True) -> None:
    try:
        with open(file_path, mode="a") as file:
            file.write(additional_text)
        if notify: print(f"Text {GREEN}has been added{RESET} to file '{file_path}' successfully.")

    except Exception as e:
        print(f"{RED}An error found while adding text to file '{file_path}': {e}{RESET}")

def read_file(file_path: str) -> str:
    with open(file_path, mode="r") as f:
        return f.read()

def asciiread_file(file_path: str) -> str | None:
    try:
        with open(file_path, mode="r") as f:
            file_text = f.read().split(".")    # "." - separates ascii text (for conversion purposes) from (not for conversion purposes)
        
        final_text = ""
        is_index_even_num = True

        for subtext in file_text:
            if is_index_even_num:
                final_text += ascii_abc(subtext)
            else:
                final_text += subtext
            is_index_even_num = not is_index_even_num
        
        return final_text

    except Exception as e:
        print(f"{RED}An error found while ascii reading file '{file_path}': {e}{RESET}")
        return None

def get_directory(file_name: str) -> str:
    try:
        return '/'.join(search_file(file_name).split('/')[:-1])
    
    except FileExistsError:
        print(f"{RED}No file named '{file_name}' in directory '{os.getcwd()}'{RESET}")
        return None
    
    except Exception as e:
        print(f"{RED}An error found while reading file '{file_name}': {e}{RESET}")
        return None

def get_files_from_dir(directory: str) -> list:
    try:
        return list(os.walk(directory))[0][2]
    except Exception as e:
        print(f"{RED}An error found while getting files list from directory '{directory}': {e}{RESET}")
        return None

def is_file(filepath: str) -> bool:
    return os.path.isfile(filepath)

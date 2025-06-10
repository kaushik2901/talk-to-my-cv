def read_file_text(path: str) -> str:
    try:
        with open(path, "r", encoding = "utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find file at path: {path}")
    except PermissionError:
        raise PermissionError(f"Permission denied when trying to read file: {path}")
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Failed to decode file at {path} with UTF-8 encoding")
    except Exception as e:
        raise Exception(f"Unexpected error reading file {path}: {str(e)}")
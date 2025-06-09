def read_file_text(path: str) -> str:
    response = ""
    
    with open(path, "r", encoding = "utf-8") as file:
        response = file.read()

    return response
def is_valid_file_type(uploaded_file):
    name = uploaded_file.name
    if name.endswith('.png') or name.endswith('.jpg'):
        return True
    return False
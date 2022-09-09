def is_valid_file_type(uploaded_file):
    name = uploaded_file.name
    if name.endswith('.xlsx') or name.endswith('.xls') or name.endswith('.csv'):
        return True
    return False
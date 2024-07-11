class ExceptionHandler:
    @staticmethod
    def handle_error(errors, key, model_name):
        error_message = ""
        if 'unique' in errors[key]:
            error_message = f'{model_name} already has preset.'
        if 'does_not_exist' in errors[key]:
            error_message = f'{model_name} does not exist.'
        if 'incorrect_type' in errors[key]:
            error_message = f'Invalid {model_name} id.'
        return error_message

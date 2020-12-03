def importer_task(user_token, user_token_secret, csv_file_name):
    try:
        import tw_frnds_ei.main_importer as main_importer
        return main_importer.main(user_token, user_token_secret, csv_file_name)

    except Exception as exc:
        return False, f"Exception raised in tw_frnds_ei importer: {exc}", None

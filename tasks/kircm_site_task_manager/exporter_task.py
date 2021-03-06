def exporter_task(user_token, user_token_secret, export_for_user):
    try:
        import tw_frnds_ei.main_exporter as main_exporter
        return main_exporter.main(user_token, user_token_secret, export_for_user)

    except Exception as exc:
        return False, f"Exception raised in tw_frnds_ei exporter: {exc}", None

import configparser
import logging
import pathlib

logger = logging.getLogger(__name__)


def import_module_tw_frnds_ei():
    try:
        # noinspection PyUnresolvedReferences
        import tw_frnds_ei.config_app as config_app

    except ModuleNotFoundError as mnfe1:
        logger.info(f"Module not found: {mnfe1} - Finding through relative path in file system...")
        import sys
        p = pathlib.Path(__file__).resolve().parents[3].joinpath('tw_frnds_ei')
        sys.path.insert(0, str(p.absolute()))

        try:
            # noinspection PyUnresolvedReferences
            import tw_frnds_ei.config_app as config_app
            dot_env_file_path = pathlib.Path(__file__).resolve().parents[1].joinpath('.env')
            config = configparser.ConfigParser()
            config.read_file(open(dot_env_file_path))
            config_app.env_config = config['DEFAULT']
            config_app.MAX_NUM_FRIENDS = 3000

            # noinspection PyUnresolvedReferences
            import tw_frnds_ei.main_exporter as main_exporter
            # noinspection PyUnresolvedReferences
            import tw_frnds_ei.main_importer as main_importer
            logger.info("Modules of tw_frnds_ei application FOUND and loaded")

        except ModuleNotFoundError as mnfe2:
            logger.error(f"Module not found: {mnfe2} - Couldn't find it in path: {p.absolute()}")
            raise mnfe2

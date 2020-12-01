import logging
import pathlib

logger = logging.getLogger(__name__)


def import_module_tw_frnds_ei():
    try:
        # noinspection PyUnresolvedReferences
        import tw_frnds_ei.main_exporter as main_exporter
        # noinspection PyUnresolvedReferences
        import tw_frnds_ei.main_importer as main_importer

    except ModuleNotFoundError as mnfe1:
        logger.warning(f"Module not found: {mnfe1} - Finding through relative path in file system...")
        import sys
        p = pathlib.Path(__file__).resolve().parents[3].joinpath('tw_frnds_ei')
        sys.path.insert(0, str(p.absolute()))

        try:
            # noinspection PyUnresolvedReferences
            import tw_frnds_ei.main_exporter as main_exporter
            # noinspection PyUnresolvedReferences
            import tw_frnds_ei.main_importer as main_importer

        except ModuleNotFoundError as mnfe2:
            logger.error(f"Module not found: {mnfe2} - Couldn't find it in path: {p.absolute()}")
            raise mnfe2

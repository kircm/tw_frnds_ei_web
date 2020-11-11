#!/usr/bin/env python

import runpy

MODULE_NAME = "kircm_site_task_manager"
print(f"Running module: {MODULE_NAME}")
runpy.run_module(MODULE_NAME)
print(f"Running of module: {MODULE_NAME} finished.")

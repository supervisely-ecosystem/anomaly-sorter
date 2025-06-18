import os

from dotenv import load_dotenv

import supervisely as sly

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    # task_id = sly.app.development.enable_advanced_debug(team_id=sly.env.team_id())


api = sly.Api.from_env()
team_id = sly.env.team_id()
project_id = sly.env.project_id()
dataset_id = sly.env.dataset_id(raise_not_found=False)

target_class = "person"

AUTOMATION_INTERVAL = 60  # Default automation interval in seconds
project = api.project.get_info_by_id(project_id)
custom_data = project.custom_data
collection_id = None

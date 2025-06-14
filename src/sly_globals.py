import os

from dotenv import load_dotenv

import supervisely as sly
from supervisely.solution.scheduler import TasksScheduler

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api.from_env()
team_id = sly.env.team_id()
project_id = sly.env.project_id()

target_class = "person"

AUTOMATION_INTERVAL = 60  # Default automation interval in seconds
scheduler = TasksScheduler()
project = api.project.get_info_by_id(project_id)
custom_data = project.custom_data

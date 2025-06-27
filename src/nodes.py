import src.sly_globals as g
import supervisely as sly
from src.components.accept_anomalies import AcceptAnomaliesNode
from src.components.check_every import InfoCheckEvery
from src.components.class_selector import ClassSelector
from src.components.filtering import CustomFilters
from src.components.run import RunNode
from src.components.statistics import Statictics

BASE_X = 265
BASE_Y = 20

class_selector = ClassSelector(api=g.api, project_id=g.project.id, x=BASE_X + 335, y=BASE_Y + 55)

input_project = sly.solution.ProjectNode(
    api=g.api,
    x=BASE_X + 35,
    y=BASE_Y,
    project_id=g.project.id,
    title="Input Project" if g.dataset_id is None else "Input Dataset",
    description="Centralizes all incoming data. Data in this project will not be modified.",
    dataset_id=g.dataset_id,
    widget_id="input_project_widget",
    refresh_interval=300, # 5 min
)

check_every_node = InfoCheckEvery(x=BASE_X, y=BASE_Y + 220)

stats_node = Statictics(
    api=g.api,
    x=BASE_X,
    y=BASE_Y + 320,
    project_id=g.project.id,
    dataset_id=g.dataset_id,
)

filters_node = CustomFilters(x=BASE_X, y=BASE_Y + 420)
run_node = RunNode(api=g.api, project_id=g.project.id, x=BASE_X, y=BASE_Y + 520)
run_node.card.disable()

navigate = sly.solution.LinkNode(
    x=BASE_X,
    y=BASE_Y + 620,
    title="Navigate to Filtered Images",
    description="Click to navigate to the filtered images in the Images Labeling Toolbox. Images will be filtered based on Entities Collection created in the previous step.",
    # link=sly.utils.abs_url(f"/app/images2/?projectId={g.project_id}"),
    link=f"/app/images2/?projectId={g.project_id}",
    icon=sly.app.widgets.Icons(
        class_name="zmdi zmdi-open-in-new", color="#2196F3", bg_color="#E3F2FD"
    ),
)
accept_node = AcceptAnomaliesNode(api=g.api, project_id=g.project.id, x=BASE_X, y=BASE_Y + 720)

# * Create a SolutionGraphBuilder instance
graph_builder = sly.solution.SolutionGraphBuilder(height="900px")

# * Add nodes to the graph
graph_builder.add_node(input_project)
graph_builder.add_node(class_selector)
graph_builder.add_node(check_every_node)
graph_builder.add_node(stats_node)
graph_builder.add_node(filters_node)
graph_builder.add_node(run_node)
graph_builder.add_node(navigate)
graph_builder.add_node(accept_node)

# * Add edges between nodes
graph_builder.add_edge(
    class_selector,
    input_project,
    start_socket="left",
    end_socket="right",
    dash=True,
    end_plug="behind",
)
graph_builder.add_edge(input_project, check_every_node)
graph_builder.add_edge(check_every_node, stats_node)
graph_builder.add_edge(stats_node, filters_node)
graph_builder.add_edge(filters_node, run_node)
graph_builder.add_edge(run_node, navigate)
graph_builder.add_edge(navigate, accept_node)
# * Build the layout
layout = graph_builder.build()

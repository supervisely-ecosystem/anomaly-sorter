import src.sly_globals as g
import supervisely as sly
from src.components.class_selector import ClassSelector
from src.components.filtering import CustomFilters
from src.components.run import RunNode
from src.components.statistics import Statictics

class_selector = ClassSelector(api=g.api, project_id=g.project.id, x=700, y=307)

input_project = sly.solution.ProjectNode(
    api=g.api,
    x=400,
    y=250,
    project_id=g.project.id,
    title="Input Project",
    description="Centralizes all incoming data. Data in this project will not be modified.",
    widget_id="input_project_widget",
)
stats_node = Statictics(
    api=g.api,
    x=1050,
    y=307,
    project_id=g.project.id,
)

filters_node = CustomFilters(x=365, y=500)
run_node = RunNode(api=g.api, project_id=g.project.id, x=365, y=650)

navigate = sly.solution.LinkNode(
    x=365,
    y=800,
    title="Navigate to Filtered Images",
    description="Click to navigate to the filtered images in the project.",
    link=sly.utils.abs_url(f"/app/images2/?projectId={g.project_id}"),
)

# * Create a SolutionGraphBuilder instance
graph_builder = sly.solution.SolutionGraphBuilder(height="2000px")

# * Add nodes to the graph
graph_builder.add_node(input_project)
graph_builder.add_node(class_selector)
graph_builder.add_node(stats_node)
graph_builder.add_node(filters_node)
graph_builder.add_node(run_node)
graph_builder.add_node(navigate)

# * Add edges between nodes
graph_builder.add_edge(input_project, filters_node)
graph_builder.add_edge(
    stats_node,
    class_selector,
    start_sockert="left",
    end_socket="right",
    dash=True,
    end_plug="disc",
)
graph_builder.add_edge(
    class_selector,
    input_project,
    start_sockert="left",
    end_socket="right",
    dash=True,
    end_plug="disc",
    point_anchor={"x": "100%", "y": "50%"},
)
graph_builder.add_edge(filters_node, run_node)
graph_builder.add_edge(run_node, navigate)


# * Build the layout
layout = graph_builder.build()

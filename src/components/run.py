from typing import Dict, List, Optional

import numpy as np

from supervisely.api.api import Api
from supervisely.app.content import DataJson
from supervisely.app.widgets import SolutionCard
from supervisely.sly_logger import logger
from supervisely.solution.base_node import SolutionCardNode, SolutionElement


class RunNode(SolutionElement):
    """
    This class represents a node in the solution graph that allows users to run custom filters on images.
    """

    def __init__(
        self,
        api: Api,
        project_id: int,
        x: int = 0,
        y: int = 0,
        *args,
        **kwargs,
    ):
        self.api = api
        self.project_id = project_id
        self.card = self._create_card()
        self.node = SolutionCardNode(content=self.card, x=x, y=y)

        super().__init__(*args, **kwargs)

    def _create_card(self):
        return SolutionCard(
            title="Run Custom Filters",
            tooltip=self._create_tooltip(),
            width=250,
            tooltip_position="left",
        )

    def _create_tooltip(self):
        return SolutionCard.Tooltip(
            description="Apply custom filters to images in the project. All images will be processed, and the results will added to a new Entities Collection in the project.",
        )

    def run(self, filters: Dict, stats: Dict) -> None:
        """
        Runs the custom filters on the images in the project.

        :param filters: A dictionary containing the filters to be applied.
        :param stats: A dictionary containing statistics for the filters.
        """

        filtered_ids = self._filter_images(filters, stats)
        if not filtered_ids:
            logger.warning("No images found after applying filters.")
            return

        images_count = len(filtered_ids)
        logger.debug(f"Found {images_count} images after applying filters.")

        # * Create a new collection in the project and add filtered images to it
        collection_name = "Filter Results"
        collection = self.api.entities_collection.get_info_by_name(self.project_id, collection_name)
        if collection:
            self.api.entities_collection.remove(collection.id)
        collection = self.api.entities_collection.create(self.project_id, collection_name)
        self.api.entities_collection.add_items(collection.id, filtered_ids)
        logger.debug(f"Filtered images added to the collection '{collection_name}'")

        # * Set custom sort values for the filtered images
        max_prefix = len(str(len(filtered_ids)))
        sort_values = [f"{str(i + 1).zfill(max_prefix)}" for i in range(len(filtered_ids))]

        self.api.image.set_custom_sort_bulk(filtered_ids, sort_values)
        logger.debug("Custom sort values set for filtered images.")

        if "filtered" not in DataJson():
            DataJson()[self.widget_id]["filtered"] = []
            DataJson().send_changes()
        DataJson()[self.widget_id]["filtered"].append(
            {
                "projectId": self.project_id,
                "collectionId": collection.id,
                "imagesCount": images_count,
                "filters": filters,
                "imageIds": filtered_ids,
            }
        )
        DataJson().send_changes()

        return collection.id

    def _filter_images(self, filters: Dict, stats: Dict) -> Optional[List[int]]:
        """
        Filters images based on the provided filters and statistics.
        :param filters: A dictionary containing the filters to be applied.
        :param stats: A dictionary containing statistics for the filters.
        :return: A list of filtered image IDs or None if no images match the filters.
        """
        if not stats:
            logger.warning("No statistics provided for filtering.")
            return set()
        if not isinstance(stats, dict):
            logger.error("Statistics should be a dictionary.")
            return set()
        min_area = filters.get("min_area", 0)
        max_area = filters.get("max_area", float("inf"))
        min_num_objects = filters.get("min_num_labels", 0)
        max_num_objects = filters.get("max_num_labels", float("inf"))
        min_intensity_diff = filters.get("min_intensity_diff", 0)
        max_intensity_diff = filters.get("max_intensity_diff", float("inf"))

        sort_by = filters.get("sort_by")

        image_ids = np.asarray(stats.get("image_ids", []))
        max_area_stats = np.asarray(stats.get("_max_area", []))
        total_area = np.asarray(stats.get("_total_area", []))
        num_labels = np.asarray(stats.get("_labels", []))
        avg_intensity_diff = np.asarray(stats.get("_avg_intensity_diff", []))

        sets = []

        if min_area > 0 or max_area < float("inf"):
            area_filter = (total_area >= min_area) & (total_area <= max_area)
            if np.any(area_filter):
                area_indices = np.where(area_filter)[0]
                sets.append(set(area_indices))
        else:
            sets.append(set(np.arange(len(image_ids))))

        if min_num_objects > 0 or max_num_objects < float("inf"):
            num_labels_filter = (num_labels >= min_num_objects) & (num_labels <= max_num_objects)
            if np.any(num_labels_filter):
                num_labels_indices = np.where(num_labels_filter)[0]
                sets.append(set(num_labels_indices))
        else:
            sets.append(set(np.arange(len(image_ids))))

        if min_intensity_diff > 0 or max_intensity_diff < float("inf"):
            intensity_diff_filter = (avg_intensity_diff >= min_intensity_diff) & (
                avg_intensity_diff <= max_intensity_diff
            )
            if np.any(intensity_diff_filter):
                intensity_diff_indices = np.where(intensity_diff_filter)[0]
                sets.append(set(intensity_diff_indices))
        else:
            sets.append(set(np.arange(len(image_ids))))

        if not sets:
            logger.warning("No images found after applying filters.")
            return set()

        intersections = set.intersection(*sets)
        if not intersections:
            logger.warning("No images found after applying filters.")
            return None

        if sort_by == "_labels":
            sorted_indices = np.argsort(num_labels[list(intersections)])
        elif sort_by == "_total_area":
            sorted_indices = np.argsort(total_area[list(intersections)])
        elif sort_by == "_avg_intensity_diff":
            sorted_indices = np.argsort(avg_intensity_diff[list(intersections)])
        else:
            sorted_indices = np.arange(len(intersections))

        filtered_image_ids = image_ids[list(intersections)][sorted_indices].tolist()
        if not filtered_image_ids:
            logger.warning("No images found after applying filters.")
            return None

        return filtered_image_ids

    @staticmethod
    def prepare_link(project_id: int, collection_id: int) -> str:
        """
        Prepares a link to the filtered images collection.
        :param project_id: The ID of the project containing filtered images.
        :param collection_id: The ID of the collection containing filtered images.
        :return: A URL to the filtered images collection.
        """
        from supervisely._utils import abs_url

        path = f"/app/images2/?projectId={project_id}&entitiesFilter=%5B%7B%22type%22%3A%22entities_collection%22,%22data%22%3A%7B%22collectionId%22%3A{collection_id},%22include%22%3Atrue%7D%7D%5D"
        return abs_url(path)

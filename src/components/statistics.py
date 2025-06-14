from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np

import supervisely as sly
from supervisely.api.api import Api
from supervisely.app.content import DataJson
from supervisely.app.widgets import Button, SlyTqdm, SolutionCard
from supervisely.collection.str_enum import StrEnum
from supervisely.sly_logger import logger
from supervisely.solution.base_node import Automation, SolutionCardNode, SolutionElement
from supervisely.task.progress import tqdm_sly


class DefaultImgTags(StrEnum):
    MAX_AREA = "_max_area"
    TOTAL_AREA = "_total_area"
    NUMBER_OF_LABELS = "_labels"
    AVG_INTENSITY_DIFF = "_avg_intensity_diff"
    MIN_INTENSITY_DIFF = "_min_intensity_diff"
    MAX_INTENSITY_DIFF = "_max_intensity_diff"


class DefaultObjTags(StrEnum):
    INTENSITY_DIFF = "_intensity_diff"


# AUTOMATION_INTERVAL = 60  # Default automation interval in seconds


class StatisticsAuto(Automation):

    def __init__(self, func: Callable[[], None] = None):
        super().__init__()
        self.job_id = "statistics_auto_job"
        self.func = func

    def apply(self, sec) -> None:
        if sec is None:
            if self.scheduler.is_job_scheduled(self.job_id):
                self.scheduler.remove_job(self.job_id)
        else:
            self.scheduler.add_job(
                self.func, interval=sec, job_id=self.job_id, replace_existing=True
            )


class Statictics(SolutionElement):
    """
    This class is a placeholder for the Statistics node.
    It is used to calculate statistics for the project.
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
        self.automation = StatisticsAuto(self.run)
        self.node = SolutionCardNode(content=self.card, x=x, y=y)

        self.in_progress = False
        self.selected_class = None

        @self.run_btn.click
        def on_run_click():
            self.run()

        super().__init__(*args, **kwargs)

    def _create_card(self):
        return SolutionCard(
            title="Calculate Statistics",
            tooltip=self._create_tooltip(),
            width=250,
            tooltip_position="right",
        )

    def _create_tooltip(self):
        return SolutionCard.Tooltip(
            description="This node calculates statistics for the project.",
            content=[
                # self.automation_btn,
                self.run_btn,
                self.pbar,
            ],
        )

    @property
    def pbar(self):
        if not hasattr(self, "_pbar"):
            self._pbar = SlyTqdm()
        return self._pbar

    @property
    def run_btn(self):
        if not hasattr(self, "_run_btn"):
            self._run_btn = self._create_run_button()
        return self._run_btn

    def _create_run_button(self):
        """
        Create the button for running the statistics calculation.
        """
        btn = Button(
            "Run manually",
            icon="zmdi zmdi-play",
            button_size="mini",
            plain=True,
            button_type="text",
        )

        @btn.click
        def on_run_click():
            logger.info(f"Manually running statistics calculation...")
            self.run()
            logger.info(f"Statistics calculation completed.")

        return btn

    def set_selected_class(self, class_name: str) -> None:
        """
        Set the selected class for statistics calculation.

        :param class_name: The name of the class to be set.
        """
        if not isinstance(class_name, str):
            raise TypeError("Class name must be a string.")
        self.selected_class = class_name
        logger.info(f"Selected class for statistics calculation: {self.selected_class}")

    def run(self):
        if self.selected_class is None:
            raise ValueError("No class selected for statistics calculation.")
        if self.in_progress:
            logger.debug("Statistics calculation is already in progress.")
            return
        self.in_progress = True
        self.calculate_statistics(self.selected_class)
        self.in_progress = False

    def get_updates_state(self) -> Dict:
        if "last_updates" not in DataJson()[self.widget_id]:
            DataJson()[self.widget_id]["last_updates"] = {}
            DataJson().send_changes()
        return DataJson()[self.widget_id]["last_updates"]

    def get_img_idx_map(self) -> Dict:
        if "img_idx_map" not in DataJson()[self.widget_id]:
            DataJson()[self.widget_id]["img_idx_map"] = {}
            DataJson().send_changes()
        return DataJson()[self.widget_id]["img_idx_map"]

    @property
    def stats(self) -> Dict:
        """
        Get the statistics for the project from DataJson.
        If statistics are not present, initialize them.
        """
        res = {}
        for default_tag in DefaultImgTags.values():
            if default_tag in DataJson()[self.widget_id]:
                res[default_tag] = DataJson()[self.widget_id][default_tag]
        if "image_ids" in DataJson()[self.widget_id]:
            res["image_ids"] = DataJson()[self.widget_id]["image_ids"]
        return deepcopy(res)

    def calculate_statistics(self, target_class: str) -> dict:
        """
        Calculate statistics for the given target class in the project.

        :param target_class: The class for which to calculate statistics.
        :return: A dictionary containing the statistics.
        """
        img_tags_to_upload = []
        project_info = self.api.project.get_info_by_id(self.project_id)
        meta = self._validate_project_meta()
        datasets = self.api.dataset.get_list(self.project_id, recursive=True)

        last_updated_map = self.get_updates_state()
        img_idx_map = self.get_img_idx_map()

        for default_tag in DefaultImgTags.values():
            if default_tag not in DataJson()[self.widget_id]:
                DataJson()[self.widget_id][default_tag] = []
                DataJson().send_changes()
        if "image_ids" not in DataJson()[self.widget_id]:
            DataJson()[self.widget_id]["image_ids"] = []
            DataJson().send_changes()
        with self.pbar(total=project_info.images_count, message=f"Processing...") as pbar:
            for dataset in datasets:
                ds_updated_at_state = last_updated_map.get(dataset.id)
                if not self._recently_updated(dataset.updated_at, ds_updated_at_state):
                    logger.debug(
                        f"Skipping dataset {dataset.name} in project {self.project_id} "
                        f"due to no updates since last calculation."
                    )
                    pbar.update(dataset.images_count)
                    continue
                img_tags_to_delete = defaultdict(set)

                for batch in self.api.image.get_list_generator(dataset.id, batch_size=20):
                    img_infos = []
                    for img_info in batch:
                        if self._recently_updated(
                            img_info.updated_at, last_updated_map.get(img_info.id)
                        ):
                            img_infos.append(img_info)
                    if len(batch) - len(img_infos) > 0:
                        logger.debug(
                            f"Skipping {len(batch) - len(img_infos)} images in dataset {dataset.name} "
                            f"due to no updates since last calculation."
                        )
                        pbar.update(len(batch) - len(img_infos))
                    if not img_infos:
                        continue

                    img_ids = [img_info.id for img_info in img_infos]
                    loop = sly.utils.get_or_create_event_loop()
                    img_np = loop.run_until_complete(self.api.image.download_nps_async(img_ids))
                    anns = self.api.annotation.download_json_batch(dataset.id, img_ids)
                    anns = [sly.Annotation.from_json(ann, meta) for ann in anns]

                    for img, ann, info in zip(img_np, anns, img_infos):
                        exists = info.id in img_idx_map
                        img_stats = self._calculate_image_statistics(img, ann, target_class)
                        DataJson()[self.widget_id]["image_ids"].append(info.id)
                        DataJson().send_changes()
                        now = datetime.now(timezone.utc)
                        last_updated_map[info.id] = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                        for key, value in img_stats.items():
                            need_add = True
                            if ann.img_tags.has_key(key):
                                if ann.img_tags.get(key).value == value:
                                    need_add = False
                                else:
                                    tag_meta = meta.get_tag_meta(key)
                                    img_tags_to_delete[tag_meta.sly_id].add(info.id)

                            if need_add:
                                img_tags_to_upload.append(
                                    {
                                        "tagId": meta.get_tag_meta(key).sly_id,
                                        "entityId": info.id,
                                        "value": value,
                                    }
                                )

                            if not exists:
                                DataJson()[self.widget_id][key].append(value)
                                DataJson().send_changes()
                            elif need_add:
                                DataJson()[self.widget_id][key][img_idx_map[info.id]] = value
                                DataJson().send_changes()
                        if not exists:
                            img_idx_map[info.id] = len(img_idx_map)
                    pbar.update(len(img_infos))
                if len(img_tags_to_delete) > 0:
                    logger.info(
                        f"Removing {len(img_tags_to_delete)} tags from images in dataset {dataset.name}."
                    )
                    img_ids = set()
                    tag_ids = set()
                    for tag_id, img_ids_set in img_tags_to_delete.items():
                        img_ids.update(img_ids_set)
                        tag_ids.add(tag_id)
                    p = tqdm_sly(desc="Removing tags from entities", total=len(img_ids))
                    self.api.advanced.remove_tags_from_images(
                        list(tag_ids), list(img_ids), p.update
                    )

                last_updated_map[dataset.id] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )

        try:
            self.pbar.close()
        except Exception:
            pass

        if img_tags_to_upload:
            logger.info(
                f"Uploading {len(img_tags_to_upload)} tags to images in project {self.project_id}."
            )
            self.api.image.tag.add_to_entities_json(
                self.project_id, img_tags_to_upload, log_progress=True
            )

        if last_updated_map:
            DataJson()[self.widget_id]["last_updates"] = last_updated_map
            DataJson().send_changes()
            logger.debug("Last updates state saved.")

        if img_idx_map:
            DataJson()[self.widget_id]["img_idx_map"] = img_idx_map
            DataJson().send_changes()
            logger.debug("Image index map saved.")

    def _recently_updated(self, curr: str, state: Optional[str] = None) -> bool:
        if state is None:
            return True
        curr_dt = datetime.strptime(curr, "%Y-%m-%dT%H:%M:%S.%fZ")
        state_dt = datetime.strptime(state, "%Y-%m-%dT%H:%M:%S.%fZ")
        return curr_dt > state_dt

    def _calculate_image_statistics(
        self, img: np.array, ann: sly.Annotation, target_class: str
    ) -> dict:
        """
        Calculate statistics for a single image.

        :param img_info: The image information.
        :param ann: The annotation for the image.
        :param target_class: The class for which to calculate statistics.
        :return: A dictionary containing the statistics for the image.
        """
        areas = []

        intensity_diffs = []
        for label in ann.labels:
            if label.obj_class.name != target_class:
                continue
            areas.append(label.geometry.area)
            intensity_diff = self._calculate_intensity_diff(img, label)
            intensity_diffs.append(intensity_diff)

        if intensity_diffs:
            avg_intensity_diff = np.mean(intensity_diffs)
            max_intensity_diff = np.max(intensity_diffs)
            min_intensity_diff = np.min(intensity_diffs)
        else:
            avg_intensity_diff = 0.0
            max_intensity_diff = 0.0
            min_intensity_diff = 0.0

        labels_count = len(ann.labels)
        max_area = np.max(areas) if areas else 0

        return {
            DefaultImgTags.NUMBER_OF_LABELS.value: labels_count,
            DefaultImgTags.MAX_AREA.value: max_area,
            DefaultImgTags.TOTAL_AREA.value: np.sum(areas) if areas else 0,
            DefaultImgTags.AVG_INTENSITY_DIFF.value: avg_intensity_diff,
            DefaultImgTags.MAX_INTENSITY_DIFF.value: max_intensity_diff,
            DefaultImgTags.MIN_INTENSITY_DIFF.value: min_intensity_diff,
        }

    def _calculate_intensity_diff(self, img: np.array, label: sly.Label) -> float:
        """
        Computes intensity difference between mask and its 1-pixel outer border (neighbors).
        """
        mask = np.full(img.shape[:2], fill_value=False)
        label.draw(mask, color=True, thickness=0)

        if not np.any(mask):
            return 0.0

        # Get the outer border of the mask
        kernel = np.ones((3, 3), np.uint8)
        outer_border = cv2.dilate(mask.astype(np.uint8), kernel, iterations=1) - mask.astype(
            np.uint8
        )

        # Calculate the average intensity in the mask and its outer border
        mask_intensity = img[mask].mean() if np.any(mask) else 0.0
        border_intensity = img[outer_border > 0].mean() if np.any(outer_border) else 0.0

        return abs(mask_intensity - border_intensity)

    def _validate_project_meta(self) -> sly.ProjectMeta:
        """
        Check if the project meta has the required tags and upload them if not.
        """
        meta = sly.ProjectMeta.from_json(self.api.project.get_meta(self.project_id))
        need_updated = False
        for tag_name in DefaultImgTags.values():
            tag_name = str(tag_name)
            if not meta.tag_metas.has_key(tag_name):
                tag_meta = sly.TagMeta(
                    tag_name,
                    sly.TagValueType.ANY_NUMBER,
                    applicable_to=sly.TagApplicableTo.IMAGES_ONLY,
                )
                meta = meta.add_tag_meta(tag_meta)
                need_updated = True

        if need_updated:
            meta = self.api.project.update_meta(self.project_id, meta)
            logger.info("Project meta updated with new tags.")

        return meta

    def apply_automation(self, sec: Optional[int] = None) -> None:
        """Apply the automation function to the MoveLabeled node."""
        self.automation.apply(sec)
        self.node.show_automation_badge()
        self.card.update_property("Check for updates every", f"{sec} sec", highlight=True)

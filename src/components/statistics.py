from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np

from supervisely._utils import get_or_create_event_loop
from supervisely.annotation.annotation import Annotation
from supervisely.annotation.label import Label
from supervisely.annotation.tag_meta import TagApplicableTo, TagMeta, TagValueType
from supervisely.api.api import Api
from supervisely.app.content import DataJson
from supervisely.app.widgets import Button, Icons, SlyTqdm, SolutionCard
from supervisely.collection.str_enum import StrEnum
from supervisely.project.project_meta import ProjectMeta
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


# class DefaultObjTags(StrEnum):
#     INTENSITY_DIFF = "_intensity_diff"


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
        dataset_id: Optional[int] = None,
        *args,
        **kwargs,
    ):
        self.api = api
        self.project_id = project_id
        self.dataset_id = dataset_id

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
            icon=Icons(
                class_name="zmdi zmdi-chart",
                color="#2196F3",
                bg_color="#E3F2FD",
            ),
        )

    def _create_tooltip(self):
        description = "This node calculates statistics for the"
        description += " project." if self.dataset_id is None else " dataset."
        return SolutionCard.Tooltip(
            description=description,
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
        self.hide_is_finished_badge()
        self.show_in_progress_badge()
        if not self.selected_class:
            logger.warning("Class is not selected for statistics calculation.")
            return
        if self.in_progress:
            logger.debug("Statistics calculation is already in progress.")
            return
        self.in_progress = True
        self.calculate_statistics(self.selected_class)
        self.hide_in_progress_badge()
        self.show_is_finished_badge()
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
        Get the statistics for the project/dataset from DataJson.
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
        Calculate statistics for the given target class in the project/dataset.

        :param target_class: The class for which to calculate statistics.
        :return: A dictionary containing the statistics.
        """
        img_tags_to_upload = []
        project_info = self.api.project.get_info_by_id(self.project_id)
        meta = self._validate_project_meta()
        if self.dataset_id is not None:
            datasets = [self.api.dataset.get_info_by_id(self.dataset_id)]
            if datasets[0].project_id != self.project_id:
                raise ValueError(
                    f"Dataset {self.dataset_id} does not belong to project {self.project_id}."
                )
        else:
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
        total = project_info.images_count if self.dataset_id is None else datasets[0].images_count
        with self.pbar(total=total, message=f"Processing...") as pbar:
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

                for batch in self.api.image.get_list_generator(dataset.id, batch_size=50):
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
                    loop = get_or_create_event_loop()
                    img_np = loop.run_until_complete(self.api.image.download_nps_async(img_ids))
                    anns = self.api.annotation.download_json_batch(dataset.id, img_ids)
                    anns = [Annotation.from_json(ann, meta) for ann in anns]

                    for img, ann, info in zip(img_np, anns, img_infos):
                        exists = info.id in img_idx_map
                        img_stats = self._calculate_image_statistics(img, ann, target_class)
                        DataJson()[self.widget_id]["image_ids"].append(info.id)
                        # DataJson().send_changes()
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
                                # DataJson().send_changes()
                            elif need_add:
                                DataJson()[self.widget_id][key][img_idx_map[info.id]] = value
                                # DataJson().send_changes()
                        if not exists:
                            img_idx_map[info.id] = len(img_idx_map)
                    DataJson().send_changes()
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
            logger.info(f"Uploading {len(img_tags_to_upload)} tags to images.")
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
        self, img: np.array, ann: Annotation, target_class: str
    ) -> dict:
        """
        Calculate statistics for a single image.

        :param img_info: The image information.
        :param ann: The annotation for the image.
        :param target_class: The class for which to calculate statistics.
        :return: A dictionary containing the statistics for the image.
        """
        target_labels = [l for l in ann.labels if l.obj_class.name == target_class]
        if not target_labels:
            logger.warning(f"No labels found for class '{target_class}' in the image.")
            return {
                DefaultImgTags.NUMBER_OF_LABELS.value: 0,
                DefaultImgTags.MAX_AREA.value: 0,
                DefaultImgTags.TOTAL_AREA.value: 0,
                DefaultImgTags.AVG_INTENSITY_DIFF.value: 0.0,
                DefaultImgTags.MAX_INTENSITY_DIFF.value: 0.0,
                DefaultImgTags.MIN_INTENSITY_DIFF.value: 0.0,
            }

        areas = np.array([label.geometry.area for label in target_labels])
        intensity_diffs = np.array([self._calculate_intensity_diff(img, l) for l in target_labels])

        return {
            DefaultImgTags.NUMBER_OF_LABELS.value: len(target_labels),
            DefaultImgTags.MAX_AREA.value: np.max(areas) if areas.size > 0 else 0,
            DefaultImgTags.TOTAL_AREA.value: np.sum(areas) if areas.size > 0 else 0,
            DefaultImgTags.AVG_INTENSITY_DIFF.value: (
                np.mean(intensity_diffs) if intensity_diffs.size > 0 else 0.0
            ),
            DefaultImgTags.MAX_INTENSITY_DIFF.value: (
                np.max(intensity_diffs) if intensity_diffs.size > 0 else 0.0
            ),
            DefaultImgTags.MIN_INTENSITY_DIFF.value: (
                np.min(intensity_diffs) if intensity_diffs.size > 0 else 0.0
            ),
        }

    def _calculate_intensity_diff(self, img: np.array, label: Label) -> float:
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
        if img.ndim == 3:
            mask_intensity = np.mean(img[mask]) if np.any(mask) else 0.0
            border_intensity = np.mean(img[outer_border > 0]) if np.any(outer_border) else 0.0
        else:
            mask_intensity = img[mask].mean() if np.any(mask) else 0.0
            border_intensity = img[outer_border > 0].mean() if np.any(outer_border) else 0.0

        return abs(mask_intensity - border_intensity)

    def _validate_project_meta(self) -> ProjectMeta:
        """
        Check if the project meta has the required tags and upload them if not.
        """
        meta = ProjectMeta.from_json(self.api.project.get_meta(self.project_id))
        need_updated = False
        for tag_name in DefaultImgTags.values():
            tag_name = str(tag_name)
            if not meta.tag_metas.has_key(tag_name):
                tag_meta = TagMeta(
                    tag_name,
                    TagValueType.ANY_NUMBER,
                    applicable_to=TagApplicableTo.IMAGES_ONLY,
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
        # self.node.show_automation_badge()
        self.card.update_property("Check for updates every", f"{sec} sec", highlight=True)

    def show_in_progress_badge(self) -> None:
        self.update_in_progress_badge(True)

    def hide_in_progress_badge(self) -> None:
        self.update_in_progress_badge(False)

    def update_in_progress_badge(self, enable: bool) -> None:
        if enable:
            self.card.update_badge_by_key(
                key="In Progress", label="⚡", plain=True, badge_type="warning"
            )
        else:
            self.card.remove_badge_by_key("In Progress")

    def show_is_finished_badge(self) -> None:
        self.update_is_finished_badge(True)

    def hide_is_finished_badge(self) -> None:
        self.update_is_finished_badge(False)

    def update_is_finished_badge(self, enable: bool) -> None:
        if enable:
            self.card.update_badge_by_key(
                key="Finished",
                label="✅",
                plain=True,
            )
        else:
            self.card.remove_badge_by_key("In Progress")

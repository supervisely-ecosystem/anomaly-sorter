<div align="center" markdown>

<img src="https://github.com/supervisely-ecosystem/anomaly-sorter/releases/download/v0.1.0/poster.jpg">

# Anomaly Sorter

**Advanced anomaly sorting based on custom statistics and intelligent filtering.**

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Features">Features</a> •
  <a href="#Statistics-and-Tags">Statistics & Tags</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#Workflow">Workflow</a> •
  <a href="#Technical-Details">Technical Details</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](../../../../supervisely-ecosystem/anomaly-sorter)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/anomaly-sorter)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/anomaly-sorter.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/anomaly-sorter.png)](https://supervisely.com)

</div>

## Overview

Anomaly Sorter is a Supervisely application built on the Supervisely "Solution" engine that streamlines the process of reviewing large sets of labeled images. It automatically calculates statistical metrics for each image, provides flexible filtering and sorting options, and allows users to select a specific range of images based on these criteria. With a single action, all images in the chosen range can be tagged with a technical label, making it easy to quickly mark and set aside groups of images that are unlikely to require further manual review. This approach significantly accelerates the overall image review workflow.

![Anomaly Sorter in Action](https://github.com/supervisely-ecosystem/anomaly-sorter/releases/download/v0.1.0/gui.jpg)

### Key Benefits

- **Automated Statistics**: Calculates metrics for all images automatically. All statistics can be accessed as tags in the project.
- **Filter & Sort**: Customizable filtering and sorting options for targeted analysis
- **Efficient Tagging**: Batch tagging system for accepted anomalies
- **Interactive Workflow**: Node-based visual interface for easyly managing the analysis process

## Statistics and Tags

### Automatically Calculated Statistics

The application automatically generates and updates several key statistics for each image andbased on the objects. These statistics are stored as tags associated with the images.

> **Note**: Do not manually modify these tags as they are used for background statistics calculation. They are automatically generated and updated by the application.

These statistics are calculated and applied automatically in background processing:

| Tag Name              | Description                                                 | Type   | Control            |
| --------------------- | ----------------------------------------------------------- | ------ | ------------------ |
| `_max_area`           | Maximum area of any object in the image                     | Number | 🤖 Auto-calculated |
| `_total_area`         | Sum of all object areas in the image                        | Number | 🤖 Auto-calculated |
| `_labels`             | Total number of objects/labels in the image                 | Number | 🤖 Auto-calculated |
| `_avg_intensity_diff` | Average intensity difference between objects and background | Float  | 🤖 Auto-calculated |
| `_min_intensity_diff` | Minimum intensity difference between objects and background | Float  | 🤖 Auto-calculated |
| `_max_intensity_diff` | Maximum intensity difference between objects and background | Float  | 🤖 Auto-calculated |

### User-Controlled Tags

> **Important**: Users should only assign `_accepted_boundary` tags manually to mark start/end points. The `_accepted` tags are automatically applied by the system based on these boundaries.

These tags are managed through user actions and workflow decisions:

| Tag Name             | Description                                                                  | Control                             |
| -------------------- | ---------------------------------------------------------------------------- | ----------------------------------- |
| `_accepted`          | Indicates accepted anomalies in the image                                    | 🤖 Auto-applied based on boundaries |
| `_accepted_boundary` | Temporary markers for defining acceptance range. Cleaned up after processing | 👤 User-applied manually            |

## Workflow

The Anomaly Sorter application follows a structured workflow to efficiently analyze and manage anomalies in images. The workflow consists of several key steps, each represented as nodes in the application interface.

![Anomaly Sorter Workflow](https://github.com/supervisely-ecosystem/anomaly-sorter/releases/download/v0.1.0/schema.jpg)

## How To Run

### Prerequisites

- Supervisely project or dataset with labeled images

### Step-by-Step Guide

**Step 1: Launch the Application**

- Option 1: Find "Anomaly Sorter" in the Supervisely Ecosystem and run it on your project
- Option 2: Navigate to your project (or dataset) in Supervisely and run the application from the context menu

**Step 2: Select Target Class**

- Click on the "Class Selection" node
- Choose the object class you want to analyze for anomalies
- Click "Apply" to confirm your selection

After selecting a class, the application will automatically enable the "Calculate Statistics" node, which will start processing the images in the project. If you change the class, the statistics will be recalculated for the new selection in the next automatic run. If you want to recalculate statistics immediately, you can click the "Run Manually" button in the tooltip of the "Calculate Statistics" node.

**Step 3: Calculate Statistics**

- The "Calculate Statistics" node will automatically start processing
- Wait for completion (progress is shown in the tooltip)
- Statistics are calculated for all images with the selected class in the project (or dataset)

**Step 4: Configure Filters**

- Click on "Custom Filters" to open filter configuration
- Set your criteria:
  - **Number of Labels**: Min/max object count per image
  - **Area Filter**: Minimum area threshold for objects
  - **Sort By**: Choose sorting method (count, area, intensity)
- Click "Save" to apply filters

**Step 5: Apply Filters and Review**

- Click the "Apply" node to run filtering
- Navigate to the filtered results using the "Navigate to Filtered Images" link
- Review the sorted anomalies in order of severity

**Step 6: Define the Range of Images to Accept**

- In the filtered image view, manually add `_accepted_boundary` tags to:
  - **Start image**: First image in acceptable anomaly range
  - **End image**: Last image in acceptable anomaly range

> **Note**: Only 1 range of accepted anomalies can be tagged at a time. If you need to tag multiple ranges, you can repeat the process by assigning new `_accepted_boundary` tags.


![Add Boundary Tags](https://github.com/supervisely-ecosystem/anomaly-sorter/releases/download/v0.1.0/boundary_tag.jpg)


**Step 7: Tag Accepted Anomalies**
- Return to the application choose the mode to accept anomalies in the modal dialog:
  - **Keep previous tags**: Retain existing `_accepted` tags
  - **Remove previous tags**: Clear existing `_accepted` tags before applying new ones
- Click "Run" to process the boundaries
- All images between boundaries will be automatically tagged as `_accepted`


**Step 8 (optional): Access Accepted Images**

Once the accepted range is processed, you can easily access all images tagged with `_accepted` by applying a tag filtering on the project page. Here's how to do it:

1. Go to your project page in Supervisely and click on the "Filters" button.
   ![Navigate to the project](https://github.com/supervisely-ecosystem/anomaly-sorter/releases/download/v0.1.0/filtering1.jpg)
2. In the filter options, select "Images Tag", choose `_accepted` from the list and click "Apply" to filter the images. All images tagged with `_accepted` will be displayed.
   ![Apply filters](https://github.com/supervisely-ecosystem/anomaly-sorter/releases/download/v0.1.0/filtering2.jpg)
3. You can then click "Annotate" to open these images in the annotation tool for further review or editing. You can also copy these images to another project or create a Quality Control task based on them.
   ![Select task for filtered images](https://github.com/supervisely-ecosystem/anomaly-sorter/releases/download/v0.1.0/filtering3.jpg)

4. Alternatively, you can filter images directly in the Image Labeling Toolbox by selecting the `_accepted` tag from the tags list. This allows you to quickly access and review all accepted anomalies within the annotation interface.

![Filter Images in Labeling Toolbox](https://github.com/supervisely-ecosystem/anomaly-sorter/releases/download/v0.1.0/filtering4.jpg)

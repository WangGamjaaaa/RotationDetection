from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

from alpharotate.libs.models.samplers.samper import Sampler
from alpharotate.libs.utils.cython_utils.cython_bbox import bbox_overlaps
from alpharotate.libs.utils.rbbox_overlaps import rbbx_overlaps
from alpharotate.libs.utils import bbox_transform
from alpharotate.libs.utils.coordinate_convert import coordinate_present_convert


class AnchorSamplerRSDet(Sampler):

    def anchor_target_layer(self, gt_boxes_h, gt_boxes_r, anchors, gpu_id=0):

        anchor_states = np.zeros((anchors.shape[0],))
        labels = np.zeros((anchors.shape[0], self.cfgs.CLASS_NUM))
        if gt_boxes_r.shape[0]:
            # [N, M]

            if self.cfgs.METHOD == 'H':
                overlaps = bbox_overlaps(np.ascontiguousarray(anchors, dtype=np.float),
                                         np.ascontiguousarray(gt_boxes_h, dtype=np.float))
            else:
                overlaps = rbbx_overlaps(np.ascontiguousarray(anchors, dtype=np.float32),
                                         np.ascontiguousarray(gt_boxes_r[:, :-1], dtype=np.float32), gpu_id)

            argmax_overlaps_inds = np.argmax(overlaps, axis=1)
            max_overlaps = overlaps[np.arange(overlaps.shape[0]), argmax_overlaps_inds]

            # compute box regression targets
            target_boxes = gt_boxes_r[argmax_overlaps_inds]

            positive_indices = max_overlaps >= self.cfgs.IOU_POSITIVE_THRESHOLD
            ignore_indices = (max_overlaps > self.cfgs.IOU_NEGATIVE_THRESHOLD) & ~positive_indices

            anchor_states[ignore_indices] = -1
            anchor_states[positive_indices] = 1

            # compute target class labels
            labels[positive_indices, target_boxes[positive_indices, -1].astype(int) - 1] = 1
        else:
            # no annotations? then everything is background
            target_boxes = np.zeros((anchors.shape[0], gt_boxes_r.shape[1]))

        if self.cfgs.METHOD == 'H':
            x_c = (anchors[:, 2] + anchors[:, 0]) / 2
            y_c = (anchors[:, 3] + anchors[:, 1]) / 2
            h = anchors[:, 2] - anchors[:, 0] + 1
            w = anchors[:, 3] - anchors[:, 1] + 1
            theta = -90 * np.ones_like(x_c)
            anchors = np.vstack([x_c, y_c, w, h, theta]).transpose()

        ratios = (anchors[:, 2] / anchors[:, 3]).reshape(-1)

        if self.cfgs.ANGLE_RANGE == 180:
            anchors = coordinate_present_convert(anchors, mode=-1)
            target_boxes = coordinate_present_convert(target_boxes, mode=-1)
        target_delta = bbox_transform.rbbox_transform(ex_rois=anchors, gt_rois=target_boxes)

        return np.array(labels, np.float32), np.array(target_delta, np.float32), \
               np.array(anchor_states, np.float32), np.array(target_boxes, np.float32), np.array(ratios, np.float32)





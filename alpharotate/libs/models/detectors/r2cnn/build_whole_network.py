# -*-coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os
import tensorflow as tf
import tensorflow.contrib.slim as slim

from alpharotate.libs.models.detectors.two_stage_base_network import DetectionNetworkBase
from alpharotate.libs.models.losses.losses import Loss
from alpharotate.libs.utils import bbox_transform
from alpharotate.libs.utils import nms_rotate
from alpharotate.libs.models.samplers.r2cnn.anchor_sampler_r2cnn import AnchorSamplerR2CNN
from alpharotate.libs.models.samplers.r2cnn.proposal_sampler_r2cnn import ProposalSamplerR2CNN
from alpharotate.libs.models.roi_extractors.roi_extractors import RoIExtractor
from alpharotate.libs.models.box_heads.box_head_base import BoxHead


class DetectionNetworkR2CNN(DetectionNetworkBase):

    def __init__(self, cfgs, is_training):
        super(DetectionNetworkR2CNN, self).__init__(cfgs, is_training)
        self.anchor_sampler_r2cnn = AnchorSamplerR2CNN(cfgs)
        self.proposal_sampler_r2cnn = ProposalSamplerR2CNN(cfgs)
        self.losses = Loss(cfgs)
        self.roi_extractor = RoIExtractor(cfgs)
        self.box_head = BoxHead(cfgs)

    def build_loss(self, rpn_box_pred, rpn_bbox_targets, rpn_cls_score, rpn_labels,
                   bbox_pred, bbox_targets, cls_score, labels):

        with tf.variable_scope('build_loss'):

            with tf.variable_scope('rpn_loss'):

                rpn_reg_loss = self.losses.smooth_l1_loss_rpn(bbox_pred=rpn_box_pred,
                                                              bbox_targets=rpn_bbox_targets,
                                                              label=rpn_labels,
                                                              sigma=self.cfgs.RPN_SIGMA)
                rpn_select = tf.reshape(tf.where(tf.not_equal(rpn_labels, -1)), [-1])
                rpn_cls_score = tf.reshape(tf.gather(rpn_cls_score, rpn_select), [-1, 2])
                rpn_labels = tf.reshape(tf.gather(rpn_labels, rpn_select), [-1])
                rpn_cls_loss = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(logits=rpn_cls_score,
                                                                                             labels=rpn_labels))

                self.losses_dict['rpn_cls_loss'] = rpn_cls_loss * self.cfgs.RPN_CLASSIFICATION_LOSS_WEIGHT
                self.losses_dict['rpn_reg_loss'] = rpn_reg_loss * self.cfgs.RPN_LOCATION_LOSS_WEIGHT

            with tf.variable_scope('FastRCNN_loss'):
                reg_loss = self.losses.smooth_l1_loss_rcnn_r(bbox_pred=bbox_pred,
                                                             bbox_targets=bbox_targets,
                                                             label=labels,
                                                             num_classes=self.cfgs.CLASS_NUM + 1,
                                                             sigma=self.cfgs.FASTRCNN_SIGMA)

                # cls_score = tf.reshape(cls_score, [-1, cfgs.CLASS_NUM + 1])
                # labels = tf.reshape(labels, [-1])
                cls_loss = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(
                    logits=cls_score,
                    labels=labels))  # beacause already sample before

                self.losses_dict['fast_cls_loss'] = cls_loss * self.cfgs.FAST_RCNN_CLASSIFICATION_LOSS_WEIGHT
                self.losses_dict['fast_reg_loss'] = reg_loss * self.cfgs.FAST_RCNN_LOCATION_LOSS_WEIGHT

    def build_whole_detection_network(self, input_img_batch, gtboxes_batch_h=None, gtboxes_batch_r=None, gpu_id=0):

        if self.is_training:
            gtboxes_batch_h = tf.reshape(gtboxes_batch_h, [-1, 5])
            gtboxes_batch_h = tf.cast(gtboxes_batch_h, tf.float32)

            gtboxes_batch_r = tf.reshape(gtboxes_batch_r, [-1, 6])
            gtboxes_batch_r = tf.cast(gtboxes_batch_r, tf.float32)

        img_shape = tf.shape(input_img_batch)

        # 1. build backbone
        feature_pyramid = self.build_backbone(input_img_batch)

        # 2. build rpn
        fpn_box_pred, fpn_cls_score, fpn_cls_prob = self.rpn(feature_pyramid)

        # 3. generate anchors
        anchor_list = self.make_anchors(feature_pyramid)
        anchors = tf.concat(anchor_list, axis=0)

        # 4. postprocess rpn proposals. such as: decode, clip, NMS
        with tf.variable_scope('postprocess_FPN'):
            rois, roi_scores = self.postprocess_rpn_proposals(rpn_bbox_pred=fpn_box_pred,
                                                              rpn_cls_prob=fpn_cls_prob,
                                                              img_shape=img_shape,
                                                              anchors=anchors,
                                                              is_training=self.is_training)

        # 5. sample minibatch
        if self.is_training:
            with tf.variable_scope('sample_anchors_minibatch'):
                fpn_labels, fpn_bbox_targets = \
                    tf.py_func(
                        self.anchor_sampler_r2cnn.anchor_target_layer,
                        [gtboxes_batch_h, img_shape, anchors],
                        [tf.float32, tf.float32])
                fpn_bbox_targets = tf.reshape(fpn_bbox_targets, [-1, 4])
                fpn_labels = tf.to_int32(fpn_labels, name="to_int32")
                fpn_labels = tf.reshape(fpn_labels, [-1])
                self.add_anchor_img_smry(input_img_batch, anchors, fpn_labels, method=0)

            fpn_cls_category = tf.argmax(fpn_cls_prob, axis=1)
            kept_rpppn = tf.reshape(tf.where(tf.not_equal(fpn_labels, -1)), [-1])
            fpn_cls_category = tf.gather(fpn_cls_category, kept_rpppn)
            acc = tf.reduce_mean(tf.to_float(tf.equal(fpn_cls_category,
                                                      tf.to_int64(tf.gather(fpn_labels, kept_rpppn)))))
            tf.summary.scalar('ACC/fpn_accuracy', acc)

            with tf.control_dependencies([fpn_labels]):

                with tf.variable_scope('sample_RCNN_minibatch'):
                    rois, labels, _, bbox_targets, _, _ = \
                        tf.py_func(self.proposal_sampler_r2cnn.proposal_target_layer,
                                   [rois, gtboxes_batch_h, gtboxes_batch_r],
                                   [tf.float32, tf.float32, tf.float32, tf.float32, tf.float32, tf.float32])
                    rois = tf.reshape(rois, [-1, 4])
                    labels = tf.to_int32(labels)
                    labels = tf.reshape(labels, [-1])
                    bbox_targets = tf.reshape(bbox_targets, [-1, 5 * (self.cfgs.CLASS_NUM + 1)])
                    self.add_roi_batch_img_smry(input_img_batch, rois, labels, method=0)

        # 6. assign level
        if self.is_training:
            rois_list, labels, bbox_targets = self.assign_levels(all_rois=rois,
                                                                 labels=labels,
                                                                 bbox_targets=bbox_targets)
        else:
            rois_list = self.assign_levels(all_rois=rois)

        # 7. build Fast-RCNN, include roi align/pooling, box head
        bbox_pred, cls_score = self.box_head.fpn_fc_head(self.roi_extractor, rois_list, feature_pyramid,
                                                         img_shape, self.is_training)
        rois = tf.concat(rois_list, axis=0, name='concat_rois')
        cls_prob = slim.softmax(cls_score, 'cls_prob')

        if self.is_training:
            cls_category = tf.argmax(cls_prob, axis=1)
            fast_acc = tf.reduce_mean(tf.to_float(tf.equal(cls_category, tf.to_int64(labels))))
            tf.summary.scalar('ACC/fast_acc', fast_acc)

        #  8. build loss
        if self.is_training:
            self.build_loss(rpn_box_pred=fpn_box_pred,
                            rpn_bbox_targets=fpn_bbox_targets,
                            rpn_cls_score=fpn_cls_score,
                            rpn_labels=fpn_labels,
                            bbox_pred=bbox_pred,
                            bbox_targets=bbox_targets,
                            cls_score=cls_score,
                            labels=labels)

        # 9. postprocess_fastrcnn
        final_bbox, final_scores, final_category = self.postprocess_fastrcnn(rois=rois,
                                                                             bbox_ppred=bbox_pred,
                                                                             scores=cls_prob,
                                                                             gpu_id=gpu_id)
        if self.is_training:
            return final_bbox, final_scores, final_category, self.losses_dict
        else:
            return final_bbox, final_scores, final_category

    def postprocess_fastrcnn(self, rois, bbox_ppred, scores, gpu_id):
        '''
        :param rois:[-1, 4]
        :param bbox_ppred: [-1, (cfgs.Class_num+1) * 5]
        :param scores: [-1, cfgs.Class_num + 1]
        :return:
        '''

        with tf.name_scope('postprocess_fastrcnn'):
            rois = tf.stop_gradient(rois)
            scores = tf.stop_gradient(scores)
            bbox_ppred = tf.reshape(bbox_ppred, [-1, self.cfgs.CLASS_NUM + 1, 5])
            bbox_ppred = tf.stop_gradient(bbox_ppred)

            bbox_pred_list = tf.unstack(bbox_ppred, axis=1)
            score_list = tf.unstack(scores, axis=1)

            allclasses_boxes = []
            allclasses_scores = []
            categories = []

            x_c = (rois[:, 2] + rois[:, 0]) / 2
            y_c = (rois[:, 3] + rois[:, 1]) / 2
            h = rois[:, 2] - rois[:, 0] + 1
            w = rois[:, 3] - rois[:, 1] + 1
            theta = -90 * tf.ones_like(x_c)
            rois = tf.transpose(tf.stack([x_c, y_c, w, h, theta]))
            for i in range(1, self.cfgs.CLASS_NUM + 1):

                # 1. decode boxes in each class
                tmp_encoded_box = bbox_pred_list[i]
                tmp_score = score_list[i]

                tmp_decoded_boxes = bbox_transform.rbbox_transform_inv(boxes=rois, deltas=tmp_encoded_box,
                                                                       scale_factors=self.cfgs.ROI_SCALE_FACTORS)

                # 2. clip to img boundaries
                # tmp_decoded_boxes = boxes_utils.clip_boxes_to_img_boundaries(decode_boxes=tmp_decoded_boxes,
                #                                                              img_shape=img_shape)

                # 3. NMS
                if self.cfgs.SOFT_NMS:
                    print("Using Soft NMS.......")
                    raise NotImplementedError("soft NMS for rotate has not implemented")

                else:
                    max_output_size = 4000 if 'DOTA' in self.cfgs.NET_NAME else 200
                    keep = nms_rotate.nms_rotate(decode_boxes=tmp_decoded_boxes,
                                                 scores=tmp_score,
                                                 iou_threshold=self.cfgs.FAST_RCNN_NMS_IOU_THRESHOLD,
                                                 max_output_size=100 if self.is_training else max_output_size,
                                                 use_gpu=self.cfgs.ROTATE_NMS_USE_GPU,
                                                 gpu_id=gpu_id)

                perclass_boxes = tf.gather(tmp_decoded_boxes, keep)
                perclass_scores = tf.gather(tmp_score, keep)

                allclasses_boxes.append(perclass_boxes)
                allclasses_scores.append(perclass_scores)
                categories.append(tf.ones_like(perclass_scores) * i)

            final_boxes = tf.concat(allclasses_boxes, axis=0)
            final_scores = tf.concat(allclasses_scores, axis=0)
            final_category = tf.concat(categories, axis=0)

            if self.is_training:
                '''
                in training. We should show the detecitons in the tensorboard. So we add this.
                '''
                kept_indices = tf.reshape(tf.where(tf.greater_equal(final_scores, self.cfgs.VIS_SCORE)), [-1])
            else:
                kept_indices = tf.reshape(tf.where(tf.greater_equal(final_scores, self.cfgs.FILTERED_SCORE)), [-1])
            final_boxes = tf.gather(final_boxes, kept_indices)
            final_scores = tf.gather(final_scores, kept_indices)
            final_category = tf.gather(final_category, kept_indices)

            return final_boxes, final_scores, final_category

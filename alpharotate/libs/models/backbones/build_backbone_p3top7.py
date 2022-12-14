# -*-coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from alpharotate.libs.models.backbones import resnet, resnet_gluoncv, mobilenet_v2, darknet, resnet_pytorch
from alpharotate.libs.models.backbones.efficientnet import efficientnet_builder, efficientnet_lite_builder
from alpharotate.libs.models.necks import fpn_p3top7, bifpn_p3top7

from alpharotate.utils.pretrain_zoo import PretrainModelZoo


class BuildBackbone(object):

    def __init__(self, cfgs, is_training):
        self.cfgs = cfgs
        self.base_network_name = cfgs.NET_NAME
        self.is_training = is_training
        self.fpn_func = self.fpn_mode(cfgs.FPN_MODE)
        self.pretrain_zoo = PretrainModelZoo()

    def fpn_mode(self, fpn_mode):
        """
        :param fpn_mode: 0-bifpn, 1-fpn
        :return:
        """

        if fpn_mode == 'bifpn':
            fpn_func = bifpn_p3top7.NeckBiFPNRetinaNet(self.cfgs)
        elif fpn_mode == 'fpn':
            fpn_func = fpn_p3top7.NeckFPNRetinaNet(self.cfgs)
        else:
            raise Exception('only support [fpn, bifpn]')
        return fpn_func

    def build_backbone(self, input_img_batch):

        if self.base_network_name.startswith('resnet_v1'):

            feature_dict = resnet.ResNetBackbone(self.cfgs).resnet_base(input_img_batch,
                                                                        scope_name=self.base_network_name,
                                                                        is_training=self.is_training)

        elif self.base_network_name in self.pretrain_zoo.mxnet_zoo:

            feature_dict = resnet_gluoncv.ResNetGluonCVBackbone(self.cfgs).resnet_base(input_img_batch,
                                                                                       scope_name=self.base_network_name,
                                                                                       is_training=self.is_training)

        elif self.base_network_name in self.pretrain_zoo.pth_zoo:

            feature_dict = resnet_pytorch.ResNetPytorchBackbone(self.cfgs).resnet_base(input_img_batch,
                                                                                       scope_name=self.base_network_name,
                                                                                       is_training=self.is_training)

        elif self.base_network_name.startswith('MobilenetV2'):

            feature_dict = mobilenet_v2.MobileNetV2Backbone(self.cfgs).mobilenetv2_base(input_img_batch,
                                                                                        is_training=self.is_training)

        elif 'efficientnet-lite' in self.base_network_name:
            feature_dict = efficientnet_lite_builder.EfficientNetLiteBackbone(self.cfgs).build_model_fpn_base(
                input_img_batch,
                model_name=self.base_network_name,
                training=True)

        elif 'efficientnet' in self.base_network_name:
            feature_dict = efficientnet_builder.EfficientNetBackbone(self.cfgs).build_model_fpn_base(
                input_img_batch,
                model_name=self.base_network_name,
                training=True)
        elif 'darknet' in self.base_network_name:
            feature_dict = darknet.DarkNetBackbone(self.cfgs).darknet53_body(input_img_batch,
                                                                             is_training=self.is_training)

        else:
            raise ValueError('Sorry, we only support {}'.format(self.pretrain_zoo.all_pretrain))

        return self.fpn_func.fpn_retinanet(feature_dict, self.is_training)

# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

import numpy as np
from configs._base_.models.faster_rcnn_r50_fpn import *
from configs._base_.datasets.dota_detection import *
from configs._base_.schedules.schedule_1x import *
from alpharotate.utils.pretrain_zoo import PretrainModelZoo

# schedule
BATCH_SIZE = 1
GPU_GROUP = "0,1"
NUM_GPU = len(GPU_GROUP.strip().split(','))
LR = 0.001 * BATCH_SIZE * NUM_GPU
SAVE_WEIGHTS_INTE = 11725 * 2
DECAY_EPOCH = [8, 11, 20]
MAX_EPOCH = 12
WARM_EPOCH = 1 / 16.
DECAY_STEP = np.array(DECAY_EPOCH, np.int32) * SAVE_WEIGHTS_INTE
MAX_ITERATION = SAVE_WEIGHTS_INTE * MAX_EPOCH
WARM_SETP = int(WARM_EPOCH * SAVE_WEIGHTS_INTE)

# dataset
DATASET_NAME = 'DIOR-R'
CLASS_NUM = 20

# model
# backbone
pretrain_zoo = PretrainModelZoo()
PRETRAINED_CKPT = pretrain_zoo.pretrain_weight_path(NET_NAME, ROOT_PATH)
TRAINED_CKPT = os.path.join(ROOT_PATH, 'output/trained_weights')

# bbox head
LEVEL = ['P2', 'P3', 'P4', 'P5', 'P6']
BASE_ANCHOR_SIZE_LIST = [32, 64, 128, 256, 512]
ANCHOR_STRIDE = [4, 8, 16, 32, 64]
ANCHOR_SCALES = [1.0]
ANCHOR_RATIOS = [0.5, 1., 2.0]

# loss
FAST_RCNN_LOCATION_LOSS_WEIGHT = 1.0
FAST_RCNN_CLASSIFICATION_LOSS_WEIGHT = 1.0

KL_TAU = 1.0
KL_FUNC = 1   # 0: sqrt  1: log

VERSION = 'FPN_Res50D_DIOR_R_R2CNN_KL_2x_20211028'

"""
R2CNN + KL
FLOPs: 810673089;    Trainable params: 41791120

cls : airplane|| Recall: 0.6344374086702387 || Precison: 0.8931938967941025|| AP: 0.6256619138427124
F1:0.7423513567163579 P:0.8949991407458326 R:0.634193862640039
cls : airport|| Recall: 0.527027027027027 || Precison: 0.15954545454545455|| AP: 0.30102299067288746
F1:0.44656599228710675 P:0.47619047619047616 R:0.42042042042042044
cls : baseballfield|| Recall: 0.7000582411182295 || Precison: 0.8278236914600551|| AP: 0.7083766692882179
F1:0.7759789749443872 P:0.9183917197452229 R:0.6718112987769366
cls : basketballcourt|| Recall: 0.8890959925442684 || Precison: 0.7154105736782902|| AP: 0.8103964469349737
F1:0.9030765331398962 P:0.9675186368477103 R:0.8466915191053123
cls : bridge|| Recall: 0.4936268829663963 || Precison: 0.1645211122554068|| AP: 0.33386623930994985
F1:0.44560847922543056 P:0.5846925972396487 R:0.35998455001931245
cls : chimney|| Recall: 0.7623666343355965 || Precison: 0.6009174311926605|| AP: 0.7247659997659998
F1:0.8176123004675658 P:0.9783783783783784 R:0.7022308438409312
cls : dam|| Recall: 0.4646840148698885 || Precison: 0.09596928982725528|| AP: 0.22894407724106328
F1:0.3555923667635278 P:0.36 R:0.3513011152416357
cls : Expressway-Service-area|| Recall: 0.808294930875576 || Precison: 0.33575803981623276|| AP: 0.7340363774219829
F1:0.7658895535030583 P:0.823093220338983 R:0.7161290322580646
cls : Expressway-toll-station|| Recall: 0.7223837209302325 || Precison: 0.3742469879518072|| AP: 0.670124157992494
F1:0.7226414500618618 P:0.8676171079429735 R:0.6191860465116279
cls : golffield|| Recall: 0.8278260869565217 || Precison: 0.4779116465863454|| AP: 0.7633221670949667
F1:0.8096514761123197 P:0.8685258964143426 R:0.7582608695652174
cls : groundtrackfield|| Recall: 0.8891246684350133 || Precison: 0.5351213282247765|| AP: 0.755891985986202
F1:0.7923289464732854 P:0.7843035343035343 R:0.8005305039787799
cls : harbor|| Recall: 0.5214170692431562 || Precison: 0.17363792363792363|| AP: 0.3656628982084131
F1:0.45695382268692647 P:0.5555555555555556 R:0.38808373590982287
cls : overpass|| Recall: 0.6150392817059483 || Precison: 0.22785862785862787|| AP: 0.501923225246604
F1:0.5710268912892903 P:0.7493163172288059 R:0.4612794612794613
cls : ship|| Recall: 0.8650315466378673 || Precison: 0.8240693109516719|| AP: 0.8054695569307105
F1:0.8790508860897978 P:0.9318160114594939 R:0.8319502074688797
cls : stadium|| Recall: 0.7336309523809523 || Precison: 0.4358974358974359|| AP: 0.630879408610443
F1:0.6422118344167036 P:0.7099099099099099 R:0.5863095238095238
cls : storagetank|| Recall: 0.7615684260091605 || Precison: 0.8223249364455743|| AP: 0.7071057324808081
F1:0.8053474463109006 P:0.8935914831437219 R:0.732973759684945
cls : tenniscourt|| Recall: 0.8601389078033501 || Precison: 0.8682980478416277|| AP: 0.8106962580568989
F1:0.8883228203212277 P:0.9444700107378432 R:0.8384856325752418
cls : trainstation|| Recall: 0.6444007858546169 || Precison: 0.1938534278959811|| AP: 0.4985586455234944
F1:0.587565734433702 P:0.6914893617021277 R:0.5108055009823183
cls : vehicle|| Recall: 0.5272522522522523 || Precison: 0.4400789547889839|| AP: 0.485333021529553
F1:0.560516925697573 P:0.7560540402752995 R:0.44534534534534537
cls : windmill|| Recall: 0.7745163442294863 || Precison: 0.561005073689297|| AP: 0.6428690122008055
F1:0.77366339594664 P:0.8239728609121749 R:0.7291527685123416
mAP is : 0.605245339216959867
"""

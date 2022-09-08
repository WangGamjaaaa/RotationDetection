# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

import numpy as np

from configs._base_.models.retinanet_r50_fpn import *
from configs._base_.datasets.dota_detection import *
from configs._base_.schedules.schedule_1x import *
from alpharotate.utils.pretrain_zoo import PretrainModelZoo

# schedule
BATCH_SIZE = 1  # r3det only support 1
GPU_GROUP = '0,1,2'
NUM_GPU = len(GPU_GROUP.strip().split(','))
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
pretrain_zoo = PretrainModelZoo()
PRETRAINED_CKPT = pretrain_zoo.pretrain_weight_path(NET_NAME, ROOT_PATH)
TRAINED_CKPT = os.path.join(ROOT_PATH, 'output/trained_weights')

# bbox head
NUM_REFINE_STAGE = 1
NUM_SUBNET_CONV = 4
LEVEL = ['P3', 'P4', 'P5', 'P6', 'P7']
BASE_ANCHOR_SIZE_LIST = [32, 64, 128, 256, 512]
ANCHOR_STRIDE = [8, 16, 32, 64, 128]
ANCHOR_SCALES = [2 ** 0, 2 ** (1.0 / 3.0), 2 ** (2.0 / 3.0)]
ANCHOR_RATIOS = [1, 1 / 2, 2.]

# sample
REFINE_IOU_POSITIVE_THRESHOLD = [0.6, 0.7]
REFINE_IOU_NEGATIVE_THRESHOLD = [0.5, 0.6]

# loss
USE_IOU_FACTOR = False

VERSION = 'RetinaNet_DIOR_R_R3Det_2x_20211025'

"""
FLOPs: 1102856619;    Trainable params: 40940026

cls : airplane|| Recall: 0.5392109108621529 || Precison: 0.22580316165221825|| AP: 0.496059439099776
F1:0.59447769823236 P:0.8658280922431866 R:0.4526302971261568
cls : airport|| Recall: 0.6501501501501501 || Precison: 0.02398094816127603|| AP: 0.3240935532691441
F1:0.4040796138816405 P:0.39290780141843973 R:0.4159159159159159
cls : baseballfield|| Recall: 0.7580081537565522 || Precison: 0.2063253012048193|| AP: 0.6775206003795413
F1:0.7463384571264463 P:0.9631675874769797 R:0.6092020966802563
cls : basketballcourt|| Recall: 0.8909599254426841 || Precison: 0.12044094488188976|| AP: 0.8099597463999879
F1:0.8828288074435714 P:0.9423585404547858 R:0.8303821062441752
cls : bridge|| Recall: 0.38006952491309387 || Precison: 0.033575596273927734|| AP: 0.24574927888510772
F1:0.3170623791575209 P:0.525 R:0.22711471610660486
cls : chimney|| Recall: 0.7817652764306499 || Precison: 0.10810085836909872|| AP: 0.7257403554213905
F1:0.8327747239710434 P:0.9703225806451613 R:0.7293889427740058
cls : dam|| Recall: 0.5687732342007435 || Precison: 0.015641772734243213|| AP: 0.23137764591589188
F1:0.35721209902760015 P:0.4047058823529412 R:0.31970260223048325
cls : Expressway-Service-area|| Recall: 0.8 || Precison: 0.06548966349781198|| AP: 0.6511051056259687
F1:0.6978177396610905 P:0.8233082706766918 R:0.6055299539170507
cls : Expressway-toll-station|| Recall: 0.6177325581395349 || Precison: 0.0294811320754717|| AP: 0.5177000823321494
F1:0.6269185988485548 P:0.9261363636363636 R:0.4738372093023256
cls : golffield|| Recall: 0.8626086956521739 || Precison: 0.05305947796320069|| AP: 0.7285611866250103
F1:0.7632526154082988 P:0.8378378378378378 R:0.7008695652173913
cls : groundtrackfield|| Recall: 0.9188328912466843 || Precison: 0.09202486584134743|| AP: 0.7425256438949001
F1:0.7768950309090659 P:0.7984322508398656 R:0.7564986737400531
cls : harbor|| Recall: 0.4888888888888889 || Precison: 0.02588411826893565|| AP: 0.2638385397421329
F1:0.35949540447604467 P:0.4269264836138175 R:0.3104669887278583
cls : overpass|| Recall: 0.5673400673400674 || Precison: 0.03450983069361005|| AP: 0.4419218502227762
F1:0.5178261338808476 P:0.765934065934066 R:0.39113355780022446
cls : ship|| Recall: 0.6666856135963167 || Precison: 0.23385271804687421|| AP: 0.5758654691801544
F1:0.6405796626633304 P:0.7856788899900892 R:0.5407264252827829
cls : stadium|| Recall: 0.78125 || Precison: 0.09186351706036745|| AP: 0.5756752435746224
F1:0.5808075766348372 P:0.6927835051546392 R:0.5
cls : storagetank|| Recall: 0.5314840974273362 || Precison: 0.23415370108439415|| AP: 0.48351383602850095
F1:0.5711643984468853 P:0.8003240490702878 R:0.44403064937288644
cls : tenniscourt|| Recall: 0.8605474601661446 || Precison: 0.21281826754681396|| AP: 0.8049997356401498
F1:0.8553598258693578 P:0.9516182849516183 R:0.7767942257932725
cls : trainstation|| Recall: 0.6954813359528488 || Precison: 0.03363420427553444|| AP: 0.42022638585142597
F1:0.48648159369522015 P:0.5699208443271768 R:0.4243614931237721
cls : vehicle|| Recall: 0.33231981981981984 || Precison: 0.08508900080735074|| AP: 0.29570246385404025
F1:0.3738682707748296 P:0.6717943725051114 R:0.25900900900900903
cls : windmill|| Recall: 0.6867911941294196 || Precison: 0.09350165750874166|| AP: 0.5348028809946183
F1:0.6440821293203304 P:0.7442063839090511 R:0.5677118078719147
mAP is : 0.5273469521468646
"""



_base_ = ["../_base_/default_runtime.py",
          "../_base_/tests/segmentation.py"]

# misc custom setting
batch_size = 8  # bs: total bs in all gpus
mix_prob = 0
empty_cache = False
enable_amp = False

# model settings
model = dict(
    type="DefaultSegmentor",
    backbone=dict(
        type="MinkUNet34C",
        in_channels=4,
        out_channels=19
    ),
    criteria=[
        dict(type="CrossEntropyLoss",
             loss_weight=1.0,
             ignore_index=-1)
    ]
)

# scheduler settings
epoch = 100
optimizer = dict(type="AdamW", lr=0.002, weight_decay=0.005)
scheduler = dict(type="OneCycleLR",
                 max_lr=optimizer["lr"],
                 pct_start=0.04,
                 anneal_strategy="cos",
                 div_factor=10.0,
                 final_div_factor=100.0)

# dataset settings
dataset_type = "SemanticKITTIDataset"
data_root = "data/semantic_kitti"
ignore_index = -1
names = ["car", "bicycle", "motorcycle", "truck", "other-vehicle",
         "person", "bicyclist", "motorcyclist", "road", "parking",
         "sidewalk", "other-ground", "building", "fence", "vegetation",
         "trunk", "terrain", "pole", "traffic-sign"]
learning_map = {
    0: ignore_index,  # "unlabeled"
    1: ignore_index,  # "outlier" mapped to "unlabeled" --------------------------mapped
    10: 0,  # "car"
    11: 1,  # "bicycle"
    13: 4,  # "bus" mapped to "other-vehicle" --------------------------mapped
    15: 2,  # "motorcycle"
    16: 4,  # "on-rails" mapped to "other-vehicle" ---------------------mapped
    18: 3,  # "truck"
    20: 4,  # "other-vehicle"
    30: 5,  # "person"
    31: 6,  # "bicyclist"
    32: 7,  # "motorcyclist"
    40: 8,  # "road"
    44: 9,  # "parking"
    48: 10,  # "sidewalk"
    49: 11,  # "other-ground"
    50: 12,  # "building"
    51: 13,  # "fence"
    52: ignore_index,  # "other-structure" mapped to "unlabeled" ------------------mapped
    60: 8,  # "lane-marking" to "road" ---------------------------------mapped
    70: 14,  # "vegetation"
    71: 15,  # "trunk"
    72: 16,  # "terrain"
    80: 17,  # "pole"
    81: 18,  # "traffic-sign"
    99: ignore_index,  # "other-object" to "unlabeled" ----------------------------mapped
    252: 0,  # "moving-car" to "car" ------------------------------------mapped
    253: 6,  # "moving-bicyclist" to "bicyclist" ------------------------mapped
    254: 5,  # "moving-person" to "person" ------------------------------mapped
    255: 7,  # "moving-motorcyclist" to "motorcyclist" ------------------mapped
    256: 4,  # "moving-on-rails" mapped to "other-vehicle" --------------mapped
    257: 4,  # "moving-bus" mapped to "other-vehicle" -------------------mapped
    258: 3,  # "moving-truck" to "truck" --------------------------------mapped
    259: 4,  # "moving-other"-vehicle to "other-vehicle" ----------------mapped
}

data = dict(
    num_classes=19,
    ignore_index=ignore_index,
    names=names,
    train=dict(
        type=dataset_type,
        split="train",
        data_root=data_root,
        learning_map=learning_map,
        transform=[
            # dict(type="RandomDropout", dropout_ratio=0.2, dropout_application_ratio=0.2),
            # dict(type="RandomRotateTargetAngle", angle=(1/2, 1, 3/2), center=[0, 0, 0], axis="z", p=0.75),
            dict(type="RandomRotate", angle=[-1, 1], axis="z", center=[0, 0, 0], p=0.5),
            # dict(type="RandomRotate", angle=[-1/6, 1/6], axis="x", p=0.5),
            # dict(type="RandomRotate", angle=[-1/6, 1/6], axis="y", p=0.5),
            dict(type="PointClip", point_cloud_range=(-80, -80, -3, 80, 80, 1)),
            dict(type="RandomScale", scale=[0.9, 1.1]),
            # dict(type="RandomShift", shift=[0.2, 0.2, 0.2]),
            # dict(type="RandomFlip", p=0.5),
            # dict(type="RandomJitter", sigma=0.005, clip=0.02),
            # dict(type="ElasticDistortion", distortion_params=[[0.2, 0.4], [0.8, 1.6]]),
            dict(type="Voxelize", voxel_size=0.05, hash_type="fnv", mode="train",
                 keys=("coord", "strength", "segment") ,return_discrete_coord=True),
            # dict(type="SphereCrop", point_max=1000000, mode="random"),
            dict(type="CenterShift", apply_z=False),
            dict(type="NormalizeColor"),
            dict(type="ToTensor"),
            dict(type="Collect", keys=("coord", "discrete_coord", "segment"), feat_keys=("coord", "strength"))
        ],
        test_mode=False,
    ),

    val=dict(
        type=dataset_type,
        split="val",
        data_root=data_root,
        transform=[
            dict(type="PointClip", point_cloud_range=(-80, -80, -3, 80, 80, 1)),
            dict(type="Voxelize", voxel_size=0.05, hash_type="fnv", mode="train",
                 keys=("coord", "strength", "segment"), return_discrete_coord=True),
            # dict(type="SphereCrop", point_max=1000000, mode="center"),
            dict(type="ToTensor"),
            dict(type="Collect", keys=("coord", "discrete_coord", "segment"), feat_keys=("coord", "strength"))
        ],
        test_mode=False,
    ),

    test=dict(
        type=dataset_type,
        split="val",
        data_root=data_root,
        transform=[
            dict(type="CenterShift", apply_z=True),
            dict(type="NormalizeColor"),
        ],
        test_mode=True,
        test_cfg=dict(
            voxelize=dict(type="Voxelize",
                          voxel_size=0.05,
                          hash_type="fnv",
                          mode="test",
                          return_discrete_coord=True,
                          keys=("coord", "strength")
                          ),
            crop=None,
            post_transform=[
                dict(type="CenterShift", apply_z=False),
                dict(type="ToTensor"),
                dict(type="Collect", keys=("coord", "discrete_coord", "index"), feat_keys=("coord", "strength"))
            ],
            aug_transform=[
                [dict(type="RandomRotateTargetAngle", angle=[0], axis="z", center=[0, 0, 0], p=1)],
                [dict(type="RandomRotateTargetAngle", angle=[1/2], axis="z", center=[0, 0, 0], p=1)],
                [dict(type="RandomRotateTargetAngle", angle=[1], axis="z", center=[0, 0, 0], p=1)],
                [dict(type="RandomRotateTargetAngle", angle=[3/2], axis="z", center=[0, 0, 0], p=1)]
            ]
        )
    ),
)

import torch
from torch.utils.data import DataLoader
from torchmetrics.detection.mean_ap import MeanAveragePrecision
from utils import batch_to_mAP_list

from model import YOLOv1, YOLOv1ResNet, YOLOv1ViT
from data import VOCDataset
import config
from tqdm import tqdm

## Dataset
test_ds = VOCDataset("val")

def collate_fn(batch):
    imgs, targets = zip(*batch)
    return torch.stack(imgs), torch.stack(targets)

test_dataloader = DataLoader(test_ds, batch_size=config.BATCH_SIZE, collate_fn=collate_fn)

## Model and Metric
models = {
    "YOLOv1": YOLOv1,
    "YOLOv1Vit": YOLOv1ViT,
    "YOLOv1ResNet": YOLOv1ResNet
}
model = models[config.model_name]().to(config.device)
checkpoint = torch.load(f"checkpoints/{config.model_name}/best_model.pth", map_location=config.device)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

metric = MeanAveragePrecision(backend="faster_coco_eval")

with torch.no_grad():
    test_loss = 0
    for images, targets in tqdm(test_dataloader, desc='Test', leave=False):
        images, targets = images.to(config.device), targets.to(config.device)

        preds = model(images)

        # Calculate mAP
        preds_list, targets_list = batch_to_mAP_list(preds, targets)
        metric.update(preds=preds_list, target=targets_list)
    print(metric.compute())


# TODO: Save metric
import torch
import typing as th

try:
    import pytorch_lightning as pl
except ModuleNotFoundError:
    # install pytorch_lightning if it wasn't installed
    import pip

    pip.main(["install", "pytorch_lightning>=1.6"])
    import pytorch_lightning as pl

from ..made import MADE
from ..utils import get_value
from .criterion import MADETrainingCriterion
from .attack import PGDAttacker


class MADETrainer(pl.LightningModule):
    def __init__(
        self,
        model_cls: str = "made.MADE",
        model_args: th.Optional[dict] = None,
        criterion_args: th.Optional[dict] = None,
        attack_args: th.Optional[dict] = None,
    ):
        super().__init__()
        self.save_hyperparameters()
        self.model = get_value(self.hparams.model_cls)(
            **(self.hparams.model_args or dict())
        )
        self.criterion = MADETrainingCriterion(
            **(self.hparams.criterion_args or dict())
        )
        self.attacker = (
            PGDAttacker(**self.hparams.attack_args)
            if self.hparams.attack_args
            else None
        )

    def forward(self, inputs):
        self.model(inputs)

    def step(
        self,
        batch,
        batch_idx: th.Optional[int] = None,
        optimizer_idx: th.Optional[int] = None,
        name: str = "train",
    ):
        is_val = name == "val"
        inputs = batch[0] if isinstance(batch, (tuple, list)) else batch
        
        if isinstance(self.model, MADE):
            # for mlp models
            inputs = inputs.reshape(inputs.shape[0], -1)

        torch.set_grad_enabled(not is_val)
        if self.attacker and not is_val:
            adv_inputs, init_loss, final_loss = self.attacker(
                model=self.model, inputs=inputs, return_loss=True
            )
            results = self.criterion(model=self.model, inputs=adv_inputs)
            results["adv/init_loss"] = init_loss
            results["adv/final_loss"] = final_loss
            results["adv/loss_diff"] = final_loss - init_loss
        else:
            results = self.criterion(model=self.model, inputs=inputs)
        for item, value in results.items():
            self.log(
                f"{item}/{name}",
                value.mean(),
                on_step=not is_val,
                on_epoch=is_val,
                logger=True,
                sync_dist=True,
            )
        return results["loss"] if not is_val else None

    def training_step(self, batch, batch_idx, optimizer_idx=None):
        return self.step(batch, batch_idx, optimizer_idx, name="train")

    def validation_step(self, batch, batch_idx, optimizer_idx=None):
        return self.step(batch, batch_idx, optimizer_idx, name="val")
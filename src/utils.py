import os.path as osp

from omegaconf.listconfig import ListConfig
from omegaconf.dictconfig import DictConfig
from lightning.pytorch import LightningModule, Trainer, callbacks
from diffusers.configuration_utils import ConfigMixin, FrozenDict


class PipelineCheckpoint(callbacks.ModelCheckpoint):

    def on_save_checkpoint(self, trainer: Trainer, pl_module: LightningModule, checkpoint) -> None:
        if trainer.global_rank == 0:
            # only ema parameters (if any) saved in pipeline
            with pl_module.maybe_ema():
                pipe_path = osp.join(
                    self.dirpath,
                    f"pipeline-{pl_module.current_epoch:03d}",
                )
                pl_module.save_pretrained(pipe_path)
            print(f"Saved pipeline to {pipe_path}")
            print(f"Saving checkpoint to {self.dirpath}")
            return super().on_save_checkpoint(trainer, pl_module, checkpoint)
        return None


def _fix_hydra_config_serialization(conf_mixin: ConfigMixin):
    # This is a hack due to incompatibility between hydra and diffusers
    new_internal_dict = {}
    for k, v in conf_mixin._internal_dict.items():
        if isinstance(v, ListConfig):
            new_internal_dict[k] = list(v)
        elif isinstance(v, DictConfig):
            new_internal_dict[k] = dict(v)
        else:
            new_internal_dict[k] = v
    conf_mixin._internal_dict = FrozenDict(new_internal_dict)

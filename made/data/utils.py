import typing as th
from torchvision import transforms as tv_transforms
from ..utils import get_value

class ReshapeTensor:
    """Reshape Tensor
    """

    def __init__(self, shape: tuple) -> None:
        self.shape = tuple(shape)

    def __call__(self, tensor):
        """
        .. note::
        Args:
            tensor (torch.Tensor): tensor to be reshaped

        Returns:
            Tensor: Reshaped Tensor.
        """
        return tensor.reshape(self.shape)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(shape={self.shape})"

def initialize_transforms(transforms: th.Optional[th.Union[list, dict, th.Any]]):
    if transforms is None or not isinstance(transforms, (dict, list)):
        return transforms

    if isinstance(transforms, list):
        return tv_transforms.Compose([initialize_transforms(i) for i in transforms])

    return get_value(transforms["cls"])(**transforms.get("args", dict()))
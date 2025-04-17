import os
import sys
import importlib.util
from typing import Type, Optional, Union
from innovation.gendata.utils.logger import setup_logger

logger = setup_logger(__name__)

class ClassManager:
    # Using class-level variables to manage registrations
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'registered_classes'):
            raise NotImplementedError(f"{cls.__name__} must define class variable 'registered_classes'")


    @classmethod
    def list_classes(cls):
        """Retrieve all registered class names."""
        return cls.registered_classes.keys()

    @classmethod
    def get_class(cls, name: str) -> Type:
        """Retrieve a class by name."""
        if name in cls.registered_classes:
            return cls.registered_classes[name]
        raise KeyError(f"Class '{name}' not found in registered classes.")

    @classmethod
    def _register(cls, class_: Type, class_name: Optional[Union[str, list[str]]] = None, force: bool = True) -> None:
        """Internal method to register a class."""
        class_names = [class_.__name__] if class_name is None else ([class_name] if isinstance(class_name, str) else class_name)

        for name in class_names:
            if not force and name in cls.registered_classes:
                raise KeyError(f"{name} is already registered at {cls.registered_classes[name].__module__}")
            cls.registered_classes[name] = class_

    @classmethod
    def register(cls, class_name: Optional[Union[str, list[str]]] = None, force: bool = True, class_: Union[Type, None] = None) -> Union[Type, callable]:
        """Decorator or function to register a class."""
        if class_ is not None:
            cls._register(class_=class_, class_name=class_name, force=force)
            return class_

        def _register(class_cls):
            cls._register(class_=class_cls, class_name=class_name, force=force)
            return class_cls

        return _register

    @classmethod
    def import_class(cls, plugin_path: str) -> None:
        """Dynamically import a class from a file path."""
        if not os.path.isfile(plugin_path):
            raise FileNotFoundError(f"File not found: {plugin_path}")

        module_name = os.path.splitext(os.path.basename(plugin_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        module = importlib.util.module_from_spec(spec)

        sys.modules[module_name] = module  # Register module globally
        try:
            spec.loader.exec_module(module)
            logger.info(f"Successfully loaded module '{module_name}' from {plugin_path}")
        except Exception as e:
            logger.error(f"Failed to load module '{module_name}' from {plugin_path}: {e}")


class MixinClass:
    def __call__(self, method_name, *args, **kwargs):
        for cls in type(self).__mro__:
            if hasattr(cls, "mixinRoot"):
                continue

            method = cls.__dict__.get(method_name)
            if method is not None:
                method(self, *args, **kwargs)

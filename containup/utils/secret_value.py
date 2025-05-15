import inspect


class SecretValue:
    __slots__ = ("__label", "__value")

    def __init__(self, label: str, value: str):
        self.__label = label
        self.__value = value

    def __repr__(self):
        return f"<Secret: {self.__label}>"

    def __str__(self):
        return f"<Secret: {self.__label}>"

    def __getattribute__(self, name):  # type: ignore
        if name == "_SecretValue__value":
            # autorise if we come from reveal method
            stack = inspect.stack()
            allowed = any(
                f.function in ("reveal", "__init__")
                and f.frame.f_locals.get("self") is self
                for f in stack[1:3]  # Limit analysis to 2 levels for performance
            )
            if not allowed:
                raise AttributeError(f"'SecretValue' object has no attribute '{name}'")
        return super().__getattribute__(name)  # type: ignore

    def reveal(self) -> str:
        return self.__value

    def label(self) -> str:
        return self.__label

    def __getstate__(self):
        raise TypeError("SecretValue cannot be pickled or serialized")

    def __reduce__(self):
        raise TypeError("SecretValue cannot be pickled or serialized")

    def __dir__(self):
        # Hide attributes to avoir exploration
        return ["reveal"]

    def __getattr__(self, name):  # type: ignore
        # Empêche l’accès à __value ou __label par introspection forcée
        raise AttributeError(f"'SecretValue' object has no attribute '{name}'")

    def __hash__(self):
        return hash((self.__label,))

    def __eq__(self, other):  # type: ignore
        raise TypeError("SecretValue cannot be compared")

    def __ne__(self, other):  # type: ignore
        raise TypeError("SecretValue cannot be compared")

    def __lt__(self, other):  # type: ignore
        raise TypeError("SecretValue cannot be compared")

    def __le__(self, other):  # type: ignore
        raise TypeError("SecretValue cannot be compared")

    def __gt__(self, other):  # type: ignore
        raise TypeError("SecretValue cannot be compared")

    def __ge__(self, other):  # type: ignore
        raise TypeError("SecretValue cannot be compared")

    def __contains__(self, item):  # type: ignore
        raise TypeError("SecretValue does not support containment checks")

    def __getitem__(self, key):  # type: ignore
        raise TypeError("SecretValue does not support item access")


def secret(placeholder: str, value: str) -> SecretValue:
    """Creates a secret (password, apikey, etc.). Use that in your environment variables."""
    return SecretValue(placeholder, value)

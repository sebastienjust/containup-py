import pytest
import pickle
import operator

from containup.utils.secret_value import SecretValue  # À adapter à ton module réel


def test_secret_str_repr_do_not_leak_value():
    s = SecretValue("api_key", "supersecret")
    output = str(s)
    assert "supersecret" not in output
    assert "api_key" in output
    output = repr(s)
    assert "supersecret" not in output
    assert "api_key" in output


def test_secret_reveal_returns_value():
    s = SecretValue("token", "12345")
    assert s.reveal() == "12345"


def test_secret_label_returns_value():
    s = SecretValue("token", "12345")
    assert s.label() == "token"


def test_secret_dir_is_limited():
    s = SecretValue("x", "y")
    assert dir(s) == ["reveal"]


def test_secret_direct_access_blocked():
    s = SecretValue("mylabel", "mypassword")
    with pytest.raises(AttributeError):
        _ = s.__value  # type: ignore
    with pytest.raises(AttributeError):
        _ = getattr(s, "__value")
    with pytest.raises(AttributeError):
        _ = getattr(s, "_SecretValue__value")


def test_secret_pickle_blocked():
    s = SecretValue("x", "y")
    with pytest.raises(TypeError):
        pickle.dumps(s)
    with pytest.raises(TypeError):
        s.__getstate__()
    with pytest.raises(TypeError):
        s.__reduce__()


def test_secret_comparisons_blocked():
    s1 = SecretValue("a", "1")
    s2 = SecretValue("b", "1")
    with pytest.raises(TypeError):
        _ = s1 == s2
    with pytest.raises(TypeError):
        _ = s1 != s2
    with pytest.raises(TypeError):
        _ = s1 < s2
    with pytest.raises(TypeError):
        _ = s1 <= s2
    with pytest.raises(TypeError):
        _ = s1 > s2
    with pytest.raises(TypeError):
        _ = s1 >= s2


@pytest.mark.parametrize(
    "op",
    [
        operator.eq,
        operator.ne,
        operator.lt,
        operator.le,
        operator.gt,
        operator.ge,
    ],
)
def test_secret_comparison_with_non_secretvalue(op):  # type: ignore
    s = SecretValue("x", "y")
    with pytest.raises(TypeError):
        op(s, "y")
    with pytest.raises(TypeError):
        op(s, 123)


def test_reverse_comparison_raises():
    s = SecretValue("x", "y")
    with pytest.raises(TypeError):
        _ = "y" == s


def test_secret_contains_blocked():
    s = SecretValue("x", "secretvalue")
    with pytest.raises(TypeError):
        _ = "sec" in s


def test_secret_getitem_blocked():
    s = SecretValue("x", "secretvalue")
    with pytest.raises(TypeError):
        _ = s[0]


def test_secret_hash_ok_and_label_based():
    s1 = SecretValue("label1", "aaa")
    s2 = SecretValue("label1", "bbb")
    assert hash(s1) == hash(s2)
    # même label, même hash


def test_secret_object_repr_cannot_be_evaled():
    s = SecretValue("x", "y")
    rep = repr(s)
    with pytest.raises(SyntaxError):
        eval(rep)  # Ne doit pas être exécutable


def test_secretvalue_getattribute_allows_internal_access():
    s = SecretValue("x", "y")
    assert (
        s.reveal() == "y"
    )  # Ce test valide aussi que getattribute ne bloque pas reveal


def test_secretvalue_getattr_on_non_sensitive_raises():
    s = SecretValue("label", "value")
    with pytest.raises(AttributeError):
        _ = s.foobar


def test_secret_hash_differs_on_label():
    s1 = SecretValue("a", "1")
    s2 = SecretValue("b", "1")
    assert hash(s1) != hash(s2)


def test_secret_label_used_in_str_and_repr():
    s = SecretValue("visible", "hidden")
    assert "visible" in str(s)
    assert "visible" in repr(s)


def test_secret_cannot_set_new_attributes():
    s = SecretValue("a", "b")
    with pytest.raises(AttributeError):
        s.new_attr = "oops"  # type: ignore


def test_secret_cannot_delete_existing_slots():
    s = SecretValue("a", "b")
    with pytest.raises(AttributeError):
        del s.__label  # type: ignore

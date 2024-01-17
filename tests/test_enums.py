import enum
import omidb


def test_lookup():
    class E(enum.Enum):
        A = "a"
        B = "b"

    for e in E:
        got = omidb.utilities.enum_lookup(e.value, E)
        expected = getattr(E, e.name)
        assert got == expected

    for e in E:
        got = omidb.utilities.enum_lookup(e.name, E)
        expected = getattr(E, e.name)
        assert got == expected

    assert omidb.utilities.enum_lookup(None, E) is None


def test_nbss_str_to_enum_for_list_like():
    codes = (
        "IDC",
        "ILC",
        "IMC",
        "IMU",
        "IPX",
        "ITC",
        "Invalid"
    )

    value = (" ").join(codes)

    result = omidb.utilities.nbss_str_to_enum(
        value,
        omidb.lesion.InvasiveCarcinomaComponent,
        "InvasiveComponents",
    )
    expected = [
        omidb.lesion.InvasiveCarcinomaComponent.IDC,
        omidb.lesion.InvasiveCarcinomaComponent.ILC,
        omidb.lesion.InvasiveCarcinomaComponent.IMC,
        omidb.lesion.InvasiveCarcinomaComponent.IMU,
        omidb.lesion.InvasiveCarcinomaComponent.IPX,
        omidb.lesion.InvasiveCarcinomaComponent.ITC,
    ]

    assert result == expected

def test_nbss_str_to_enum_for_single_str():

    result = omidb.utilities.nbss_str_to_enum(
        "H2",
        omidb.events.Opinion,
    )

    assert result == omidb.events.Opinion.H2
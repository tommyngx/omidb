import omidb


def test_lesion_is_invasive_no_attributes() -> None:

    lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L)

    assert not lesion.is_invasive


def test_lesion_is_invasive_malignancy_types() -> None:

    for mtype, expected in zip(
        (
            omidb.lesion.MalignancyType.a,
            omidb.lesion.MalignancyType.b,
            omidb.lesion.MalignancyType.c,
        ),
        (False, True, False),
    ):

        biopsy_wide = omidb.lesion.LesionBiopsyWide(malignant_type=mtype)

        lesion = omidb.lesion.Lesion("", omidb.lesion.Side.L, biopsy_wide=biopsy_wide)

        assert lesion.is_invasive == expected


def test_lesion_is_invasive_biopsy_conditions() -> None:

    biopsy_wides = [
        omidb.lesion.LesionBiopsyWide(
            invasive_components=omidb.lesion.InvasiveCarcinomaComponent.IDC
        ),
        omidb.lesion.LesionBiopsyWide(
            invasive_type=omidb.lesion.InvasiveCarcinomaType.IN
        ),
        omidb.lesion.LesionBiopsyWide(disease_grade=omidb.lesion.HistologicalGrade.G1),
    ]

    for biopsy_wide in biopsy_wides:
        lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L, biopsy_wide=biopsy_wide)

        assert lesion.is_invasive


def test_lesion_is_invasive_surgery_conditions() -> None:

    surgeries = [
        omidb.lesion.LesionSurgery(
            invasive_components=omidb.lesion.InvasiveCarcinomaComponent.IDC
        ),
        omidb.lesion.LesionSurgery(invasive_type=omidb.lesion.InvasiveCarcinomaType.IN),
        omidb.lesion.LesionSurgery(disease_grade=omidb.lesion.HistologicalGrade.G1),
    ]

    for surgery in surgeries:
        lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L, surgery=surgery)

        assert lesion.is_invasive


def test_lesion_is_not_insitu_if_invasive(mocker) -> None:  # type: ignore

    mocker.patch("omidb.lesion.Lesion.is_invasive", new_callable=lambda: True)

    # This condition would otherwise result in `is_insitu` being True
    biopsy_wide = omidb.lesion.LesionBiopsyWide(
        malignant_type=omidb.lesion.MalignancyType.a
    )

    lesion = omidb.lesion.Lesion("", omidb.lesion.Side.L, biopsy_wide=biopsy_wide)

    assert not lesion.is_insitu


def test_lesion_is_insitu_malignancy_types() -> None:

    for mtype, expected in zip(
        (
            omidb.lesion.MalignancyType.a,
            omidb.lesion.MalignancyType.b,
            omidb.lesion.MalignancyType.c,
        ),
        (True, False, False),
    ):

        biopsy_wide = omidb.lesion.LesionBiopsyWide(malignant_type=mtype)

        lesion = omidb.lesion.Lesion("", omidb.lesion.Side.L, biopsy_wide=biopsy_wide)

        assert lesion.is_insitu == expected


def test_lesion_is_insitu_biopsy_conditions() -> None:

    biopsy_wides = [
        omidb.lesion.LesionBiopsyWide(
            insitu_components=omidb.lesion.InSituCarcinomaComponent.NID
        ),
        omidb.lesion.LesionBiopsyWide(dcis_grade=omidb.lesion.DCISGrade.NDH),
    ]

    for biopsy_wide in biopsy_wides:
        lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L, biopsy_wide=biopsy_wide)

        assert lesion.is_insitu


def test_lesion_is_insitu_surgery_conditions() -> None:

    surgeries = [
        omidb.lesion.LesionSurgery(
            insitu_components=omidb.lesion.InSituCarcinomaComponent.NID
        ),
        omidb.lesion.LesionSurgery(dcis_grade=omidb.lesion.DCISGrade.NDH),
    ]

    for surgery in surgeries:
        lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L, surgery=surgery)

        assert lesion.is_insitu


def test_lesion_grade_none() -> None:
    lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L)
    assert lesion.grade == None


def test_lesion_grade() -> None:

    params = [
        [
            {
                "disease_grade": omidb.lesion.HistologicalGrade.G1,
                "dcis_grade": omidb.lesion.DCISGrade.NDH,
            },
            {
                "disease_grade": omidb.lesion.HistologicalGrade.G2,
                "dcis_grade": omidb.lesion.DCISGrade.NDL,
            },
            omidb.lesion.HistologicalGrade.G2,
        ],
        [
            {
                "disease_grade": omidb.lesion.HistologicalGrade.G1,
                "dcis_grade": omidb.lesion.DCISGrade.NDH,
            },
            {"dcis_grade": omidb.lesion.DCISGrade.NDL},
            omidb.lesion.HistologicalGrade.G1,
        ],
        [
            {"dcis_grade": omidb.lesion.DCISGrade.NDH},
            {"dcis_grade": omidb.lesion.DCISGrade.NDL},
            omidb.lesion.DCISGrade.NDL,
        ],
        [
            {"dcis_grade": omidb.lesion.DCISGrade.NDH},
            {"insitu_components": None},
            omidb.lesion.DCISGrade.NDH,
        ],
    ]

    for i in range(len(params)):

        b = omidb.lesion.LesionBiopsyWide(**params[i][0])

        s = omidb.lesion.LesionSurgery(**params[i][1])

        lesion = omidb.lesion.Lesion("", omidb.lesion.Side.L, biopsy_wide=b, surgery=s)

        assert lesion.grade == params[i][2]


def test_lesion_status_none() -> None:
    lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L)
    assert lesion.status is None


def test_lesion_status_invasive(mocker) -> None:
    mocker.patch("omidb.lesion.Lesion.is_invasive", new_callable=lambda: True)
    mocker.patch("omidb.lesion.Lesion.is_insitu", new_callable=lambda: False)
    lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L)
    assert lesion.status == omidb.lesion.Status.Invasive


def test_lesion_status_invasive_trumps(mocker) -> None:
    mocker.patch("omidb.lesion.Lesion.is_invasive", new_callable=lambda: True)
    mocker.patch("omidb.lesion.Lesion.is_insitu", new_callable=lambda: True)
    lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L)
    assert lesion.status == omidb.lesion.Status.Invasive


def test_lesion_status_insitu(mocker) -> None:
    mocker.patch("omidb.lesion.Lesion.is_invasive", new_callable=lambda: False)
    mocker.patch("omidb.lesion.Lesion.is_insitu", new_callable=lambda: True)
    lesion = omidb.lesion.Lesion("a", omidb.lesion.Side.L)
    assert lesion.status == omidb.lesion.Status.Insitu

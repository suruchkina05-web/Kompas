from app.rules.engine import evaluate_rules
from app.schemas import BreastAssessment, MammographyResult, PatientState


def mammo(ctx, right=None, left=None):
    return MammographyResult(
        clinical_context=ctx,
        right_breast=right or BreastAssessment(),
        left_breast=left or BreastAssessment(),
    )


def test_hrt_acr_c():
    state = PatientState(
        patient_id="1", sex="f", age=52, clinical_context="menopausal_HRT_monitoring",
        mammography=[mammo("menopausal_HRT_monitoring", BreastAssessment(birads=2, acr_density="C"), BreastAssessment(birads=2, acr_density="B"))],
    )
    ids = evaluate_rules(state)
    assert "hrt_acr_cd_ultrasound" in ids
    assert "hrt_abnormal_mammo_consult" in ids


def test_suspected_breast_cancer_biopsy():
    state = PatientState(
        patient_id="2", sex="f", age=47, clinical_context="suspected_breast_cancer",
        mammography=[mammo("suspected_breast_cancer", left=BreastAssessment(birads=4, acr_density="C", findings=["узловое образование"]))],
    )
    ids = evaluate_rules(state)
    assert "breast_cancer_biopsy" in ids
    assert "breast_cancer_ultrasound_nodes" in ids


def test_mastitis_does_not_trigger_without_no_response():
    state = PatientState(patient_id="3", sex="f", age=35, clinical_context="inflammatory_breast_disease")
    assert "inflammation_no_response_exclude_malignancy" not in evaluate_rules(state)


def test_mastitis_triggers_with_no_response():
    state = PatientState(patient_id="4", sex="f", age=35, clinical_context="inflammatory_breast_disease", no_response_to_antiinflammatory_treatment=True)
    assert "inflammation_no_response_exclude_malignancy" in evaluate_rules(state)


def test_unknown_primary_requires_relevant_metastatic_site():
    no_site = PatientState(patient_id="5", sex="f", age=61, clinical_context="cancer_of_unknown_primary")
    assert "unknown_primary_mammography_40_plus" not in evaluate_rules(no_site)
    with_site = PatientState(patient_id="6", sex="f", age=61, clinical_context="cancer_of_unknown_primary", metastatic_sites=["аксиллярные лимфатические узлы"])
    assert "unknown_primary_mammography_40_plus" in evaluate_rules(with_site)


def test_kr598_screening_40_75_without_mammo():
    state = PatientState(patient_id="7", sex="f", age=40, clinical_context="screening")
    ids = evaluate_rules(state)
    assert "ddmj_screening_mammography_40_75" in ids


def test_kr598_birads3_followup_and_oncology():
    state = PatientState(
        patient_id="8", sex="f", age=45, clinical_context="screening",
        mammography=[mammo("screening", right=BreastAssessment(birads=3, acr_density="B"))],
    )
    ids = evaluate_rules(state)
    assert "ddmj_birads_3_six_month_followup" in ids
    assert "ddmj_birads_3_oncology_consult" in ids


def test_kr598_birads4_is_biopsy_not_cancer_diagnosis():
    state = PatientState(
        patient_id="9", sex="f", age=48, clinical_context="palpable_mass",
        mammography=[mammo("palpable_mass", right=BreastAssessment(birads=4, birads_subcategory="4A", acr_density="C", findings=["узловое образование"]))],
    )
    ids = evaluate_rules(state)
    assert "ddmj_birads_4_5_biopsy" in ids
    assert "ddmj_birads_4_5_oncology" in ids
    assert "ddmj_birads_6_oncology" not in ids


def test_kr598_acr_c_additional_imaging_and_short_interval():
    state = PatientState(
        patient_id="10", sex="f", age=52, clinical_context="screening",
        mammography=[mammo("screening", right=BreastAssessment(birads=2, acr_density="C"), left=BreastAssessment(birads=2, acr_density="B"))],
    )
    ids = evaluate_rules(state)
    assert "ddmj_acr_cd_additional_imaging" in ids
    assert "ddmj_acr_cd_shorter_screening_interval" in ids


def test_kr598_palpable_mass_mammo_any_age():
    state = PatientState(patient_id="11", sex="f", age=27, clinical_context="palpable_mass")
    assert "ddmj_palpable_mass_mammography" in evaluate_rules(state)

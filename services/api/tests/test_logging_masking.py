from services.api.app.logging_utils import mask_pii, mask_in_structure


def test_mask_pnr_strings() -> None:
    assert mask_pii("19860101-1234") == "******-1234"
    assert mask_pii("8601011234") == "******-1234"
    assert mask_pii("text 20000101+9876 end") == "text ******-9876 end"


def test_mask_in_nested_structures() -> None:
    data = {"user": {"pnr": "19751212-9999"}, "list": ["9001011234", 1]}
    masked = mask_in_structure(data)
    assert masked["user"]["pnr"].endswith("-9999") and masked["user"]["pnr"].startswith("******")
    assert masked["list"][0] == "******-1234".replace("1234", "1234")  # stable format



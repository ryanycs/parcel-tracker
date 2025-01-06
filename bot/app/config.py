from enum import Enum

from discord.ext.commands import Choice


class Platform(Enum):
    SEVEN_ELEVEN = "seven_eleven"
    FAMILY_MART  = "family_mart"
    OK_MART  = "ok_mart"
    SHOPEE = "shopee"
    LSA = "lsa"

PLATFORM_TO_ENUM = {
    "小七": Platform.SEVEN_ELEVEN,
    "7-11": Platform.SEVEN_ELEVEN,
    "seven": Platform.SEVEN_ELEVEN,
    "seven-eleven": Platform.SEVEN_ELEVEN,
    "seven_eleven": Platform.SEVEN_ELEVEN,
    "711": Platform.SEVEN_ELEVEN,
    "全家": Platform.FAMILY_MART,
    "family": Platform.FAMILY_MART,
    "family-mart": Platform.FAMILY_MART,
    "family_mart": Platform.FAMILY_MART,
    "fami": Platform.FAMILY_MART,
    "ok": Platform.OK_MART,
    "okmart": Platform.OK_MART,
    "ok-mart": Platform.OK_MART,
    "ok_mart": Platform.OK_MART,
    "蝦皮": Platform.SHOPEE,
    "shopee": Platform.SHOPEE,
    "lsa": Platform.LSA,
}

PLATFORM_CHOICES = [
    Choice(name=name, value=value)
    for value, name in {
        "seven_eleven": "7-11",
        "family_mart": "全家",
        "ok_mart": "OK",
        "shopee": "蝦皮",
        "lsa": "LSA",
    }.items()
]
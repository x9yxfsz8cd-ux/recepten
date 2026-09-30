#!/usr/bin/env python3
"""
Bouwt de twee Opdrachten (Shortcuts) die de website aanroept.

  Boodschappen — zet de ingrediënten in je lijst in Herinneringen
  Kooktimer    — start een timer in de Klok-app met de naam van de stap

De site roept ze aan via shortcuts://run-shortcut?name=…&input=text&text=…
De namen moeten dus exact kloppen.

Een .shortcut is een plist die ondertekend moet zijn voordat iOS hem accepteert.
macOS kan dat zelf met `shortcuts sign`, dus hier is geen Apple-account voor nodig.

Gebruik:
    python3 Scripts/maak_shortcuts.py
Daarna de twee bestanden uit Scripts/Opdrachten/ naar je iPhone sturen.
"""

import plistlib
import subprocess
import uuid
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
DOEL = WORTEL / "Scripts" / "Opdrachten"

LIJSTNAAM = "Boodschappen"        # de lijst in Herinneringen


def nieuw_id():
    return str(uuid.uuid4()).upper()


def tekst(s):
    """Een letterlijke tekstwaarde."""
    return {"Value": {"string": s, "attachmentsByRange": {}},
            "WFSerializationType": "WFTextTokenString"}


def uitvoer_van(uuid_bron, naam):
    """Verwijzing naar wat een eerdere actie opleverde."""
    return {"Value": {"OutputUUID": uuid_bron, "OutputName": naam,
                      "Type": "ActionOutput"},
            "WFSerializationType": "WFTextTokenAttachment"}


def variabele(naam):
    return {"Value": {"Type": "Variable", "VariableName": naam},
            "WFSerializationType": "WFTextTokenAttachment"}


def tekst_met_variabele(ding):
    """Een tekstveld dat volledig uit één variabele bestaat."""
    return {"Value": {"string": "￼",
                      "attachmentsByRange": {"{0, 1}": ding["Value"]}},
            "WFSerializationType": "WFTextTokenString"}


def actie(identifier, parameters):
    return {"WFWorkflowActionIdentifier": identifier,
            "WFWorkflowActionParameters": parameters}


def omhulsel(acties, naam):
    return {
        "WFWorkflowClientVersion": "2038.1.1",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 4282601983,
            "WFWorkflowIconGlyphNumber": 59511,
        },
        "WFWorkflowTypes": ["NCWidget", "WatchKit"],
        "WFWorkflowInputContentItemClasses": [
            "WFAppStoreAppContentItem", "WFArticleContentItem",
            "WFContactContentItem", "WFDateContentItem",
            "WFEmailAddressContentItem", "WFFolderContentItem",
            "WFGenericFileContentItem", "WFImageContentItem",
            "WFiTunesProductContentItem", "WFLocationContentItem",
            "WFDCMapsLinkContentItem", "WFAVAssetContentItem",
            "WFPDFContentItem", "WFPhoneNumberContentItem",
            "WFRichTextContentItem", "WFSafariWebPageContentItem",
            "WFStringContentItem", "WFURLContentItem",
        ],
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowHasShortcutInputVariables": True,
        "WFWorkflowActions": acties,
        "WFWorkflowName": naam,
    }


# ── Boodschappen ───────────────────────────────────────────────────────────
# De site stuurt de ingrediënten als tekst, één per regel. We splitsen op
# regeleindes en zetten elk item als los herinneringetje in je lijst.

def boodschappen():
    splits_id = nieuw_id()
    herhaal_id = nieuw_id()

    acties = [
        actie("is.workflow.actions.text.split", {
            "UUID": splits_id,
            "text": tekst_met_variabele(variabele("Shortcut Input")),
            "WFTextSeparator": "New Lines",
        }),
        actie("is.workflow.actions.repeat.each", {
            "GroupingIdentifier": herhaal_id,
            "WFControlFlowMode": 0,
            "WFInput": uitvoer_van(splits_id, "Split Text"),
        }),
        actie("is.workflow.actions.addnewreminder", {
            "WFCalendarItemTitle": tekst_met_variabele(variabele("Repeat Item")),
            "WFCalendarItemListName": tekst(LIJSTNAAM),
        }),
        actie("is.workflow.actions.repeat.each", {
            "GroupingIdentifier": herhaal_id,
            "WFControlFlowMode": 2,
        }),
    ]
    return omhulsel(acties, "Boodschappen")


# ── Kooktimer ──────────────────────────────────────────────────────────────
# De site stuurt "300|Noedels en gyoza": seconden, streepje, naam van de stap.
# We splitsen daarop, starten de timer met het aantal seconden en tonen de
# naam als melding, zodat je ziet waar de timer bij hoort.

def kooktimer():
    splits_id = nieuw_id()
    seconden_id = nieuw_id()
    naam_id = nieuw_id()

    acties = [
        actie("is.workflow.actions.text.split", {
            "UUID": splits_id,
            "text": tekst_met_variabele(variabele("Shortcut Input")),
            "WFTextSeparator": "Custom",
            "WFTextCustomSeparator": "|",
        }),
        actie("is.workflow.actions.getitemfromlist", {
            "UUID": seconden_id,
            "WFInput": uitvoer_van(splits_id, "Split Text"),
            "WFItemSpecifier": "Item At Index",
            "WFItemIndex": 1,
        }),
        actie("is.workflow.actions.getitemfromlist", {
            "UUID": naam_id,
            "WFInput": uitvoer_van(splits_id, "Split Text"),
            "WFItemSpecifier": "Item At Index",
            "WFItemIndex": 2,
        }),
        actie("is.workflow.actions.timer.start", {
            "WFDuration": {
                "Value": {
                    "Magnitude": tekst_met_variabele(uitvoer_van(seconden_id, "Item from List")),
                    "Unit": "sec",
                },
                "WFSerializationType": "WFQuantityFieldValue",
            },
        }),
        actie("is.workflow.actions.notification", {
            "WFNotificationActionTitle": tekst("Timer gestart"),
            "WFNotificationActionBody": tekst_met_variabele(uitvoer_van(naam_id, "Item from List")),
            "WFNotificationActionSound": False,
        }),
    ]
    return omhulsel(acties, "Kooktimer")


def bouw(shortcut, naam):
    DOEL.mkdir(parents=True, exist_ok=True)
    # shortcuts sign kijkt naar de extensie: .plist wordt geweigerd
    kaal = DOEL / f"{naam}_onondertekend.shortcut"
    klaar = DOEL / f"{naam}.shortcut"

    kaal.write_bytes(plistlib.dumps(shortcut))
    res = subprocess.run(
        ["shortcuts", "sign", "--mode", "anyone",
         "--input", str(kaal), "--output", str(klaar)],
        capture_output=True, text=True,
    )
    if res.returncode == 0:
        kaal.unlink()
        print(f"  {klaar.relative_to(WORTEL)}  ({klaar.stat().st_size // 1024} kB)")
        return True
    print(f"  {naam}: ondertekenen mislukt — {res.stderr.strip()[:160]}")
    print(f"  onondertekend bewaard: {kaal.relative_to(WORTEL)}")
    return False


if __name__ == "__main__":
    print("Opdrachten bouwen...")
    ok = bouw(boodschappen(), "Boodschappen")
    ok &= bouw(kooktimer(), "Kooktimer")
    if ok:
        print("\nKlaar. Stuur beide bestanden naar je iPhone (AirDrop) en open ze.")

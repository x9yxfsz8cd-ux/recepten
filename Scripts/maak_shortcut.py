#!/usr/bin/env python3
"""
Genereert een 'Recept Saver' shortcut-bestand voor de Opdrachten-app.
"""
import plistlib
import uuid
import subprocess
import sys
import os

API_KEY_PLACEHOLDER = "PLAK_HIER_JE_API_SLEUTEL"

def gen_uuid():
    return str(uuid.uuid4()).upper()

# ── Token helpers ──

def text_str(s):
    """Gewone tekst zonder variabelen."""
    return {
        "Value": {
            "string": s,
            "attachmentsByRange": {}
        },
        "WFSerializationType": "WFTextTokenString"
    }

def text_with_var(before, var_attachment, after=""):
    """Tekst met één variabele erin."""
    pos = len(before)
    s = before + "\ufffc" + after
    return {
        "Value": {
            "string": s,
            "attachmentsByRange": {
                f"{{{pos}, 1}}": var_attachment
            }
        },
        "WFSerializationType": "WFTextTokenString"
    }

def var_named(name):
    return {"Type": "Variable", "VariableName": name}

def action_output(uid, name):
    return {"Type": "ActionOutput", "OutputUUID": uid, "OutputName": name}

def ext_input():
    return {"Type": "ExtensionInput"}

def token_attachment(ref):
    return {
        "Value": ref,
        "WFSerializationType": "WFTextTokenAttachment"
    }

# ── Dictionary field helpers ──

def dict_field(key_str, value, item_type=0):
    """item_type: 0=text, 3=number, 4=array, 1=boolean, 2=dictionary"""
    return {
        "WFItemType": item_type,
        "WFKey": text_str(key_str),
        "WFValue": value
    }

def dict_value(fields):
    return {
        "Value": {
            "WFDictionaryFieldValueItems": fields
        },
        "WFSerializationType": "WFDictionaryFieldValue"
    }

# ── Build the shortcut ──

actions = []

# --- Actie 1: Tekst (bouw het volledige JSON-verzoek) ---
# We bouwen de hele API body als tekst, met de Shortcut Input erin
prompt_text = (
    "Extraheer het recept uit de onderstaande invoer en vertaal het "
    "volledig naar het Nederlands. Geef een nette samenvatting met: "
    "titel, ingrediënten met hoeveelheden, en genummerde stappen. "
    "Stappen maximaal 3 zinnen. Altijd Nederlandse eenheden "
    "(g, ml, el, tl, stuks).\\n\\nInvoer:\\n"
)

json_before = (
    '{"model":"claude-haiku-4-5-20251001","max_tokens":2000,'
    '"messages":[{"role":"user","content":[{"type":"text","text":"'
    + prompt_text
)
json_after = '"}]}]}'

text_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
    "WFWorkflowActionParameters": {
        "UUID": text_uuid,
        "WFTextActionText": text_with_var(json_before, ext_input(), json_after)
    }
})

# --- Actie 2: Stel variabele in → "Verzoek" ---
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "Verzoek",
        "WFInput": token_attachment(action_output(text_uuid, "Text"))
    }
})

# --- Actie 3: Haal inhoud van URL op (Claude API) ---
download_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
    "WFWorkflowActionParameters": {
        "UUID": download_uuid,
        "WFURL": text_str("https://api.anthropic.com/v1/messages"),
        "WFHTTPMethod": "POST",
        "WFHTTPHeaders": dict_value([
            dict_field("x-api-key", text_str(API_KEY_PLACEHOLDER)),
            dict_field("anthropic-version", text_str("2023-06-01")),
            dict_field("content-type", text_str("application/json")),
            dict_field("anthropic-dangerous-direct-browser-access", text_str("true")),
        ]),
        "WFHTTPBodyType": "File",
        "WFRequestVariable": token_attachment(var_named("Verzoek")),
    }
})

# --- Actie 4: Stel variabele in → "APIResultaat" ---
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "APIResultaat",
        "WFInput": token_attachment(action_output(download_uuid, "Contents of URL"))
    }
})

# --- Actie 5: Haal woordenboekwaarde op → "content" ---
dict1_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
    "WFWorkflowActionParameters": {
        "UUID": dict1_uuid,
        "WFInput": token_attachment(var_named("APIResultaat")),
        "WFDictionaryKey": text_str("content")
    }
})

# --- Actie 6: Haal onderdeel op uit lijst → eerste ---
list_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
    "WFWorkflowActionParameters": {
        "UUID": list_uuid,
        "WFInput": token_attachment(action_output(dict1_uuid, "Dictionary Value")),
        "WFItemSpecifier": "First Item"  # might need to be integer 0
    }
})

# --- Actie 7: Haal woordenboekwaarde op → "text" ---
dict2_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
    "WFWorkflowActionParameters": {
        "UUID": dict2_uuid,
        "WFInput": token_attachment(action_output(list_uuid, "Item from List")),
        "WFDictionaryKey": text_str("text")
    }
})

# --- Actie 8: Stel variabele in → "ReceptTekst" ---
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "ReceptTekst",
        "WFInput": token_attachment(action_output(dict2_uuid, "Dictionary Value"))
    }
})

# --- Actie 9: Maak notitie aan ---
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.evernote.new",
    "WFWorkflowActionParameters": {
        # Apple Notes "Create Note" uses the identifier for Apple Notes
    }
})

# Actually, Apple Notes "Create Note" has a different identifier.
# Let me use the correct one.
actions.pop()  # remove the wrong one

actions.append({
    "WFWorkflowActionIdentifier": "com.apple.mobilenotes.SharingExtension",
    "WFWorkflowActionParameters": {
        "WFCreateNoteInput": token_attachment(var_named("ReceptTekst")),
    }
})

# --- Actie 10: Toon melding ---
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
    "WFWorkflowActionParameters": {
        "WFNotificationActionTitle": text_str("Recept Saver"),
        "WFNotificationActionBody": text_str("Recept opgeslagen!")
    }
})

# ── Workflow wrapper ──

shortcut = {
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {
        "WFWorkflowIconStartColor": 463140863,  # green-ish
        "WFWorkflowIconGlyphNumber": 59511,  # cooking pot icon
    },
    "WFWorkflowClientVersion": "2302.0.4",
    "WFWorkflowHasShortcutInputVariables": True,
    "WFWorkflowInputContentItemClasses": [
        "WFStringContentItem",
        "WFURLContentItem",
        "WFImageContentItem"
    ],
    "WFWorkflowTypes": ["WatchKit", "NCWidget"],
    "WFWorkflowImportQuestions": [
        {
            "ActionIndex": 2,  # index of the download action
            "Category": "Parameter",
            "DefaultValue": "",
            "ParameterKey": "WFHTTPHeaders",
            "Text": "Vul je Claude API-sleutel in (sk-ant-...)"
        }
    ],
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowActions": actions,
    "WFWorkflowName": "Recept Saver"
}

# ── Save and sign ──

output_dir = os.path.dirname(os.path.abspath(__file__))
unsigned_path = os.path.join(output_dir, "ReceptSaver_unsigned.plist")
signed_path = os.path.join(output_dir, "Recept Saver.shortcut")

with open(unsigned_path, "wb") as f:
    plistlib.dump(shortcut, f)

print(f"Unsigned plist opgeslagen: {unsigned_path}")

# Sign it
result = subprocess.run(
    ["shortcuts", "sign", "--mode", "anyone", "--input", unsigned_path, "--output", signed_path],
    capture_output=True, text=True
)

if result.returncode == 0:
    print(f"Signed shortcut opgeslagen: {signed_path}")
    os.remove(unsigned_path)
    print("Klaar! Open het bestand om de shortcut te importeren.")
else:
    print(f"Fout bij ondertekenen: {result.stderr}")
    print("Het unsigned bestand staat nog klaar voor handmatig ondertekenen.")

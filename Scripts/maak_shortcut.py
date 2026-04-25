#!/usr/bin/env python3
"""
Genereert een 'Recept Saver' shortcut voor de Opdrachten-app (iPhone/Mac).

Het resulterende .shortcut bestand:
- Accepteert URL's, tekst, of foto's via het deelmenu
- Vraagt de API-sleutel bij installatie (importvraag)
- Stuurt het recept naar Claude en vraagt om HTML voor Apple Notes
- Slaat de notitie op in de map 'Recepten'
"""
import plistlib
import uuid
import subprocess
import os

# ── Token helpers ──

def gen_uuid():
    return str(uuid.uuid4()).upper()

def text_str(s):
    return {
        "Value": {"string": s, "attachmentsByRange": {}},
        "WFSerializationType": "WFTextTokenString"
    }

def text_with_var(before, var_attachment, after=""):
    pos = len(before)
    s = before + "\ufffc" + after
    return {
        "Value": {
            "string": s,
            "attachmentsByRange": {f"{{{pos}, 1}}": var_attachment}
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
    return {"Value": ref, "WFSerializationType": "WFTextTokenAttachment"}

def dict_field(key_str, value, item_type=0):
    return {
        "WFItemType": item_type,
        "WFKey": text_str(key_str),
        "WFValue": value
    }

def dict_value(fields):
    return {
        "Value": {"WFDictionaryFieldValueItems": fields},
        "WFSerializationType": "WFDictionaryFieldValue"
    }


# ── Prompt ──

HTML_TEMPLATE = (
    '<div><b><span style=\\"font-size: 24px\\">NAAM</span></b></div>'
    '<div><font color=\\"#808080\\">X min . Y porties</font></div>'
    '<div>#tag1 #tag2</div>'
    '<div><br></div>'
    '<div><b><span style=\\"font-size: 18px\\">Ingredienten</span></b></div>'
    '<ul><li>hoeveelheid eenheid ingredient</li></ul>'
    '<div><br></div>'
    '<div><b><span style=\\"font-size: 18px\\">Bereiding</span></b></div>'
    '<ol><li>Stap 1.</li></ol>'
    '<div><br></div>'
    '<div>Bron: sitenaam</div>'
)

REGELS = (
    '\\n\\nRegels:\\n'
    '- Tags uit: vis, vlees, vegetarisch, vegan, snel, comfort food, Aziatisch, Italiaans, ontbijt, lunch, diner, snack\\n'
    '- Eenheden: g, ml, el, tl, stuks\\n'
    '- Stappen max 3 zinnen\\n'
    '- Geef ALLEEN de HTML terug, geen andere tekst'
)

PROMPT_URL = (
    'Extraheer het recept uit de onderstaande invoer en vertaal naar het Nederlands. '
    'Geef ALLEEN de HTML-notitie terug in dit format:\\n\\n'
    + HTML_TEMPLATE + REGELS + '\\n\\nInvoer:\\n'
)

PROMPT_FOTO = (
    'Extraheer het recept uit deze afbeelding en vertaal naar het Nederlands. '
    'Geef ALLEEN de HTML-notitie terug in dit format:\\n\\n'
    + HTML_TEMPLATE + REGELS
)


# ── Acties bouwen ──

actions = []

# Invoer opslaan
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "Invoer",
        "WFInput": token_attachment(ext_input())
    }
})

# Als het een afbeelding is
if_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
    "WFWorkflowActionParameters": {
        "UUID": if_uuid,
        "GroupingIdentifier": if_uuid,
        "WFControlFlowMode": 0,
        "WFCondition": 8,
        "WFInput": token_attachment(var_named("Invoer")),
        "WFContentItemClass": "WFImageContentItem"
    }
})

# Foto-tak: base64 coderen
b64_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.base64encode",
    "WFWorkflowActionParameters": {
        "UUID": b64_uuid,
        "WFInput": token_attachment(var_named("Invoer")),
        "WFEncodeMode": "Encode",
        "WFBase64LineBreakMode": "None"
    }
})

foto_before = (
    '{"model":"claude-haiku-4-5-20251001","max_tokens":3000,"messages":[{"role":"user","content":['
    '{"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":"'
)
foto_after = '"}},{"type":"text","text":"' + PROMPT_FOTO + '"}]}]}'

foto_body_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
    "WFWorkflowActionParameters": {
        "UUID": foto_body_uuid,
        "WFTextActionText": text_with_var(foto_before, action_output(b64_uuid, "Base64 Encoded"), foto_after)
    }
})

actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "APIBody",
        "WFInput": token_attachment(action_output(foto_body_uuid, "Text"))
    }
})

# Anders-tak (URL/tekst)
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
    "WFWorkflowActionParameters": {
        "UUID": if_uuid,
        "GroupingIdentifier": if_uuid,
        "WFControlFlowMode": 1
    }
})

url_before = (
    '{"model":"claude-haiku-4-5-20251001","max_tokens":3000,"messages":[{"role":"user","content":[{"type":"text","text":"'
    + PROMPT_URL
)
url_after = '"}]}]}'

url_body_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
    "WFWorkflowActionParameters": {
        "UUID": url_body_uuid,
        "WFTextActionText": text_with_var(url_before, var_named("Invoer"), url_after)
    }
})

actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "APIBody",
        "WFInput": token_attachment(action_output(url_body_uuid, "Text"))
    }
})

# Einde als
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.conditional",
    "WFWorkflowActionParameters": {
        "UUID": if_uuid,
        "GroupingIdentifier": if_uuid,
        "WFControlFlowMode": 2
    }
})

# Claude API aanroepen
api_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
    "WFWorkflowActionParameters": {
        "UUID": api_uuid,
        "WFURL": text_str("https://api.anthropic.com/v1/messages"),
        "WFHTTPMethod": "POST",
        "WFHTTPHeaders": dict_value([
            dict_field("x-api-key", text_str("IMPORTVRAAG_API_SLEUTEL")),
            dict_field("anthropic-version", text_str("2023-06-01")),
            dict_field("content-type", text_str("application/json")),
            dict_field("anthropic-dangerous-direct-browser-access", text_str("true")),
        ]),
        "WFHTTPBodyType": "File",
        "WFRequestVariable": token_attachment(var_named("APIBody")),
    }
})

# API-resultaat opslaan
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "APIResultaat",
        "WFInput": token_attachment(action_output(api_uuid, "Contents of URL"))
    }
})

# content[0].text ophalen
dict1_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
    "WFWorkflowActionParameters": {
        "UUID": dict1_uuid,
        "WFInput": token_attachment(var_named("APIResultaat")),
        "WFDictionaryKey": text_str("content")
    }
})

list_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
    "WFWorkflowActionParameters": {
        "UUID": list_uuid,
        "WFInput": token_attachment(action_output(dict1_uuid, "Dictionary Value")),
        "WFItemSpecifier": "First Item"
    }
})

dict2_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.getvalueforkey",
    "WFWorkflowActionParameters": {
        "UUID": dict2_uuid,
        "WFInput": token_attachment(action_output(list_uuid, "Item from List")),
        "WFDictionaryKey": text_str("text")
    }
})

actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
    "WFWorkflowActionParameters": {
        "WFVariableName": "ReceptHTML",
        "WFInput": token_attachment(action_output(dict2_uuid, "Dictionary Value"))
    }
})

# Maak rijke tekst van HTML
richtext_uuid = gen_uuid()
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.makerichtextfromhtml",
    "WFWorkflowActionParameters": {
        "UUID": richtext_uuid,
        "WFInput": token_attachment(var_named("ReceptHTML"))
    }
})

# Notitie aanmaken in map Recepten
actions.append({
    "WFWorkflowActionIdentifier": "com.apple.mobilenotes.SharingExtension",
    "WFWorkflowActionParameters": {
        "WFCreateNoteInput": token_attachment(action_output(richtext_uuid, "Rich Text")),
        "WFFolderName": text_str("Recepten")
    }
})

# Bevestiging
actions.append({
    "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
    "WFWorkflowActionParameters": {
        "WFNotificationActionTitle": text_str("Recept Saver"),
        "WFNotificationActionBody": text_str("Recept opgeslagen in Recepten!")
    }
})


# ── Workflow wrapper ──

api_action_idx = next(
    i for i, a in enumerate(actions)
    if a.get("WFWorkflowActionIdentifier") == "is.workflow.actions.downloadurl"
)

shortcut = {
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {
        "WFWorkflowIconStartColor": 431817727,
        "WFWorkflowIconGlyphNumber": 59511,
    },
    "WFWorkflowClientVersion": "2302.0.4",
    "WFWorkflowHasShortcutInputVariables": True,
    "WFWorkflowInputContentItemClasses": [
        "WFStringContentItem",
        "WFURLContentItem",
        "WFImageContentItem"
    ],
    "WFWorkflowTypes": ["NCWidget"],
    "WFWorkflowImportQuestions": [
        {
            "ActionIndex": api_action_idx,
            "Category": "Parameter",
            "DefaultValue": "",
            "ParameterKey": "WFHTTPHeaders",
            "Text": "Vul je Claude API-sleutel in (begint met sk-ant-...)"
        }
    ],
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowActions": actions,
    "WFWorkflowName": "Recept Saver"
}


# ── Opslaan en ondertekenen ──

output_dir = os.path.dirname(os.path.abspath(__file__))
unsigned_path = os.path.join(output_dir, "ReceptSaver_unsigned.plist")
signed_path = os.path.join(output_dir, "Recept Saver.shortcut")

with open(unsigned_path, "wb") as f:
    plistlib.dump(shortcut, f)

print(f"Unsigned plist opgeslagen: {unsigned_path}")

result = subprocess.run(
    ["shortcuts", "sign", "--mode", "anyone", "--input", unsigned_path, "--output", signed_path],
    capture_output=True, text=True
)

if result.returncode == 0:
    print(f"Signed shortcut opgeslagen: {signed_path}")
    os.unlink(unsigned_path)
    print("Klaar! Stuur Recept Saver.shortcut naar je iPhone om te installeren.")
else:
    print(f"Fout bij ondertekenen: {result.stderr}")
    print(f"Unsigned bestand beschikbaar: {unsigned_path}")

// Leest tekst uit een afbeelding met Apple's Vision-framework.
// Draait volledig lokaal: er gaat niets naar buiten. Geeft alleen de gevonden
// tekst op stdout, zodat het filteren daarna ook op deze Mac kan gebeuren.
//
// Bouwen:  swiftc -O Scripts/ocr.swift -o Scripts/ocr
// Gebruik: Scripts/ocr <pad-naar-afbeelding>

import Foundation
import Vision
import CoreImage

guard CommandLine.arguments.count > 1 else {
    FileHandle.standardError.write("gebruik: ocr <afbeelding>\n".data(using: .utf8)!)
    exit(2)
}

let pad = CommandLine.arguments[1]
guard let bron = CIImage(contentsOf: URL(fileURLWithPath: pad)) else {
    FileHandle.standardError.write("kan niet lezen: \(pad)\n".data(using: .utf8)!)
    exit(1)
}

let verzoek = VNRecognizeTextRequest()
verzoek.recognitionLevel = .accurate
verzoek.usesLanguageCorrection = true
verzoek.recognitionLanguages = ["nl-NL", "en-US"]

let uitvoerder = VNImageRequestHandler(ciImage: bron, options: [:])
do {
    try uitvoerder.perform([verzoek])
} catch {
    FileHandle.standardError.write("ocr mislukt: \(error)\n".data(using: .utf8)!)
    exit(1)
}

let regels = (verzoek.results ?? []).compactMap { waarneming -> String? in
    waarneming.topCandidates(1).first?.string
}
print(regels.joined(separator: "\n"))

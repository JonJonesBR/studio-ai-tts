"""
Studio AI TTS - Catálogo de Vozes
"""

from dataclasses import dataclass
from typing import ClassVar, List, Optional


@dataclass(frozen=True)
class Voice:
    """Representa uma voz TTS."""
    id: str
    name: str
    category: str = ""
    engine: str = ""
    gender: str = ""


class VoiceCatalog:
    """Catálogo centralizado de vozes expandido via JSON."""
    
    GEMINI_VOICES: ClassVar[List[Voice]] = [
        # Femininas Conversacionais
        Voice("Aoede", "Aoede (Conversacional)", "Gemini: Feminina Conversacional", "gemini", "F"),
        Voice("Kore", "Kore (Energética)", "Gemini: Feminina Conversacional", "gemini", "F"),
        Voice("Leda", "Leda (Profissional)", "Gemini: Feminina Conversacional", "gemini", "F"),
        Voice("Zephyr", "Zephyr (Brilhante)", "Gemini: Feminina Conversacional", "gemini", "F"),
        # Femininas Especializadas
        Voice("Achird", "Achird (Jovem/Curiosa)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Algenib", "Algenib (Confiante)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Callirrhoe", "Callirrhoe (Profissional)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Despina", "Despina (Acolhedora)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Erinome", "Erinome (Articulada)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Laomedeia", "Laomedeia (Inquisitiva)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Pulcherrima", "Pulcherrima (Animada)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Sulafat", "Sulafat (Persuasiva)", "Gemini: Feminina Especializada", "gemini", "F"),
        Voice("Vindemiatrix", "Vindemiatrix (Calma)", "Gemini: Feminina Especializada", "gemini", "F"),
        # Masculinas Principais
        Voice("Puck", "Puck (Animado)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Charon", "Charon (Suave)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Orus", "Orus (Maduro/Grave)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Autonoe", "Autonoe (Maduro/Ressonante)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Iapetus", "Iapetus (Clara)", "Gemini: Masculina Principal", "gemini", "M"),
        Voice("Umbriel", "Umbriel (Suave/Experiente)", "Gemini: Masculina Principal", "gemini", "M"),
        # Masculinas Especializadas
        Voice("Achernar", "Achernar (Amigável)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Alnilam", "Alnilam (Energético)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Enceladus", "Enceladus (Entusiasta)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Fenrir", "Fenrir (Natural)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Gacrux", "Gacrux (Confiante)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Rasalgethi", "Rasalgethi (Conversacional)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Sadachbia", "Sadachbia (Grave/Cool)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Sadaltager", "Sadaltager (Entusiasta)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Schedar", "Schedar (Casual)", "Gemini: Masculina Especializada", "gemini", "M"),
        Voice("Zubenelgenubi", "Zubenelgenubi (Poderoso)", "Gemini: Masculina Especializada", "gemini", "M"),
    ]
    
    EDGE_VOICES: ClassVar[List[Voice]] = [
        # Multilingual (As melhores para Audiobooks)
        Voice("pt-BR-ThalitaMultilingualNeural", "Thalita Multilingual (PT-BR) ⭐", "Edge: Multilingual", "edge", "F"),
        Voice("en-US-AvaMultilingualNeural", "Ava (Multilingual EUA) ⭐", "Edge: Multilingual", "edge", "F"),
        Voice("en-US-BrianMultilingualNeural", "Brian (Multilingual EUA) ⭐", "Edge: Multilingual", "edge", "M"),
        Voice("en-US-AndrewMultilingualNeural", "Andrew (Multilingual EUA) ⭐", "Edge: Multilingual", "edge", "M"),
        Voice("en-US-EmmaMultilingualNeural", "Emma (Multilingual EUA) ⭐", "Edge: Multilingual", "edge", "F"),
        Voice("en-AU-WilliamMultilingualNeural", "William (Multilingual AUS)", "Edge: Multilingual", "edge", "M"),
        Voice("fr-FR-RemyMultilingualNeural", "Remy (Multilingual FR)", "Edge: Multilingual", "edge", "M"),
        Voice("fr-FR-VivienneMultilingualNeural", "Vivienne (Multilingual FR)", "Edge: Multilingual", "edge", "F"),
        Voice("de-DE-FlorianMultilingualNeural", "Florian (Multilingual DE)", "Edge: Multilingual", "edge", "M"),
        Voice("de-DE-SeraphinaMultilingualNeural", "Seraphina (Multilingual DE)", "Edge: Multilingual", "edge", "F"),
        Voice("it-IT-GiuseppeMultilingualNeural", "Giuseppe (Multilingual IT)", "Edge: Multilingual", "edge", "M"),
        Voice("ko-KR-HyunsuMultilingualNeural", "Hyunsu (Multilingual KR)", "Edge: Multilingual", "edge", "M"),
    ]

    @classmethod
    def get_by_engine(cls, engine: str) -> List[Voice]:
        if engine == "gemini":
            return cls.GEMINI_VOICES
        return cls.EDGE_VOICES
    
    @classmethod
    def get_by_id(cls, voice_id: str) -> Optional[Voice]:
        all_voices = cls.GEMINI_VOICES + cls.EDGE_VOICES
        for v in all_voices:
            if v.id == voice_id:
                return v
        return None

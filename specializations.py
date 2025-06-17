from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class Subject:
    def __init__(self, name: str, coefficient: float, has_td: bool = False, has_tp: bool = False):
        self.name = name
        self.coefficient = coefficient
        self.has_td = has_td
        self.has_tp = has_tp

class Specialization(ABC):
    def __init__(self):
        self.levels: Dict[str, Dict[str, Subject]] = {}
        self.unsupported_years: List[str] = []
        self._init_levels()

    @abstractmethod
    def _init_levels(self):
        pass

    def get_subjects(self, level: str) -> Dict[str, Subject]:
        return self.levels.get(level, {})

    def is_year_supported(self, level: str) -> bool:
        return level not in self.unsupported_years

    def calculate_average(self, level: str, subject: str, grades: List[float]) -> float:
        if not self.is_year_supported(level):
            raise ValueError(f"Year {level} is not supported yet. Please wait for upcoming updates.")
            
        subject_info = self.levels.get(level, {}).get(subject)
        if not subject_info:
            raise ValueError(f"Subject {subject} not found in level {level}")

        if subject_info.has_td:
            # (exam1 + exam2 + td) / 3
            return sum(grades[:3]) / 3
        else:
            # (exam1 + exam2) / 2
            return sum(grades[:2]) / 2

class ArabicSpecialization(Specialization):
    def _init_levels(self):
        # First year subjects
        arabic1 = {
            "AdabJahili": Subject("AdabJahili", 3, has_td=True),
            "NaqdQadim": Subject("NaqdQadim", 3, has_td=True),
            "Lissaneyat": Subject("Lissaneyat", 3, has_td=True),
            "Nahw": Subject("Nahw", 3, has_td=True),
            "Aroud": Subject("Aroud", 2),
            "Balagha": Subject("Balagha", 2),
            "Sarf": Subject("Sarf", 2),
            "Fiqh": Subject("Fiqh", 2),
            "FanT3bir": Subject("FanT3bir", 1),
            "HadharaIslam": Subject("HadharaIslam", 1),
            "Informatique": Subject("Informatique", 1),
            "OuloumIslamia": Subject("OuloumIslamia", 1),
            "Anglais": Subject("Anglais", 1),
            "OuloumTarbawiya": Subject("OuloumTarbawiya", 1)
        }
        self.levels["arabic1"] = arabic1
        
        # Add unsupported years
        self.unsupported_years = ["arabic2", "arabic3", "arabic4 (+4)", "arabic4 (+5)", "arabic5"]

class MathSpecialization(Specialization):
    def _init_levels(self):
        # First year subjects
        math1 = {
            "analyse": Subject("analyse", 4),
            "algebre": Subject("algebre", 2),
            "thermo": Subject("thermo", 3),
            "stm": Subject("stm", 3),
            "mecanique": Subject("mecanique", 3),
            "elect": Subject("elect", 3),
            "tarikh l3olom": Subject("tarikh l3olom", 1),
            "tarbiya": Subject("tarbiya", 1)
        }
        self.levels["math1"] = math1

        # Second year subjects
        math2 = {
            "topologie": Subject("topologie", 4),
            "analyse 2": Subject("analyse 2", 2),
            "calculs différentiels": Subject("calculs différentiels", 2),
            "informatiquee": Subject("informatiquee", 2),
            "psychologie 'enfant'": Subject("psychologie 'enfant'", 2),
            "géométrie": Subject("géométrie", 2),
            "algèbre linéaire": Subject("algèbre linéaire", 2),
            "algèbre générale": Subject("algèbre générale", 2)
        }
        self.levels["math2"] = math2

        # Third year subjects
        math3 = {
            "analyse numérique": Subject("analyse numérique", 4),
            "analyse complexe": Subject("analyse complexe", 2),
            "algèbre3": Subject("algèbre3", 2),
            "théorie de mesure و de l'intégration1": Subject("théorie de mesure و de l'intégration1", 2),
            "psychologie éducative": Subject("psychologie éducative", 2),
            "géométrie": Subject("géométrie", 2),
            "statistiques و probabilités": Subject("statistiques و probabilités", 2),
            "logic math": Subject("logic math", 1)
        }
        self.levels["math3"] = math3

        # Fourth year subjects (+5)
        math4_5 = {
            "didactiques mathématiques": Subject("didactiques mathématiques", 2),
            "Analyse complexe": Subject("Analyse complexe", 2),
            "Algèbre4": Subject("Algèbre4", 2),
            "Théorie de  mesure et de l'intégration2": Subject("Théorie de  mesure et de l'intégration2", 2),
            "Programmes d'études": Subject("Programmes d'études", 1),
            "Géométrie": Subject("Géométrie", 2),
            "Statistiques et probabilités2": Subject("Statistiques et probabilités2", 2),
            "Équations différentielles": Subject("Équations différentielles", 2)
        }
        self.levels["math4 (+5)"] = math4_5
        
        # Add unsupported years
        self.unsupported_years = ["math4 (+4)", "math5"]

class PhysicsSpecialization(Specialization):
    def _init_levels(self):
        # First year subjects
        physics1 = {
            "analyse": Subject("analyse", 4),
            "algebre": Subject("algebre", 2),
            "thermo": Subject("thermo", 3),
            "stm": Subject("stm", 3),
            "mecanique": Subject("mecanique", 3),
            "elect": Subject("elect", 3),
            "tarikh l3olom": Subject("tarikh l3olom", 1),
            "tarbiya": Subject("tarbiya", 1)
        }
        self.levels["physics1"] = physics1

        # Second year subjects
        physics2 = {
            "math": Subject("math", 4),
            "vibrations": Subject("vibrations", 3),
            "Optique": Subject("Optique", 3),
            "Cinetique && électrochimie": Subject("Cinetique && électrochimie", 3),
            "équilibre": Subject("équilibre", 4),
            "électronique": Subject("électronique", 4),
            "informatique": Subject("informatique", 2),
            "psycho": Subject("psycho", 2)
        }
        self.levels["physics2"] = physics2

        # Third year subjects (+4)
        physics3_4 = {
            "solid_state_physics": Subject("solid_state_physics", 4),
            "modern_physics": Subject("modern_physics", 4),
            "organic_chemistry": Subject("organic_chemistry", 4),
            "physics_education": Subject("physics_education", 4),
            "analytical_chemistry": Subject("analytical_chemistry", 3),
            "chemistry_education": Subject("chemistry_education", 2),
            "technological_measurements": Subject("technological_measurements", 2),
            "psycho3": Subject("psycho3", 2)
        }
        self.levels["physics3 (+4)"] = physics3_4

        # Third year subjects (+5)
        physics3_5 = {
            "mécanique classique": Subject("mécanique classique", 3),
            "nisbiya": Subject("nisbiya", 3),
            "psycho3": Subject("psycho3", 2),
            "chimie organique": Subject("chimie organique", 3),
            "chimie analytique": Subject("chimie analytique", 3),
            "Mécanique quantique": Subject("Mécanique quantique", 3),
            "méthodes math": Subject("méthodes math", 3),
            "thermochimie": Subject("thermochimie", 3),
            "9iyassat": Subject("9iyassat", 2)
        }
        self.levels["physics3 (+5)"] = physics3_5

        # Fourth year subjects (+5)
        physics4_5 = {
            "solid": Subject("solid", 3),
            "analytique": Subject("analytique", 3),
            "Fluides": Subject("Fluides", 2),
            "info": Subject("info", 2),
            "nucl": Subject("nucl", 2),
            "atomique": Subject("atomique", 2),
            "didactique chimie": Subject("didactique chimie", 3),
            "didactique physique": Subject("didactique physique", 3),
            "Manahidj": Subject("Manahidj", 1)
        }
        self.levels["physics4 (+5)"] = physics4_5
        
        # Add unsupported years
        self.unsupported_years = ["physics4 (+4)", "physics5"]

class InfoSpecialization(Specialization):
    def _init_levels(self):
        # First year subjects
        info1 = {
            "algo": Subject("algo", 5),
            "sm1": Subject("sm1", 4),
            "logique": Subject("logique", 3),
            "algebre": Subject("algebre", 3),
            "analyse": Subject("analyse", 3),
            "électro": Subject("électro", 3),
            "stat": Subject("stat", 2),
            "tarikh l3olom": Subject("tarikh l3olom", 1),
            "education sciences 'fares'": Subject("education sciences 'fares'", 1),
            "français": Subject("français", 1)
        }
        self.levels["info1"] = info1

        # Second year subjects
        info2 = {
            "algo2": Subject("algo2", 5),
            "sm2": Subject("sm2", 4),
            "se 1": Subject("se 1", 4),
            "si 1": Subject("si 1", 3),
            "thl": Subject("thl", 3),
            "ts": Subject("ts", 3),
            "analyse numérique": Subject("analyse numérique", 3),
            "psychologie 'fares'": Subject("psychologie 'fares'", 2),
            "anglais": Subject("anglais", 1)
        }
        self.levels["info2"] = info2

        # Third year subjects
        info3 = {
            "réseau": Subject("réseau", 4),
            "se 2": Subject("se 2", 4),
            "compilation": Subject("compilation", 4),
            "web": Subject("web", 3),
            "ro": Subject("ro", 3),
            "psycho": Subject("psycho", 2),
            "si 2": Subject("si 2", 2),
            "ai": Subject("ai", 2),
            "anglais": Subject("anglais", 1)
        }
        self.levels["info3"] = info3

        # Fourth year subjects (+4)
        info4_4 = {
            "Réseau2 ": Subject("Réseau2 ", 4),
            "GL ": Subject("GL ", 3),
            "Poo ": Subject("Poo ", 3),
            "Web2 ": Subject("Web2 ", 3),
            "systemExpert ": Subject("systemExpert ", 2),
            "psycho4 ": Subject("psycho4 ", 1),
            "didactique ": Subject("didactique ", 1),
            "tachri3 ": Subject("tachri3 ", 1),
            "Stage": Subject("Stage", 3)
        }
        self.levels["info4 (+4)"] = info4_4

        # Fourth year subjects (+5)
        info4_5 = {
            "Bdd": Subject("Bdd", 4),
            "Réseau2": Subject("Réseau2", 4),
            "GL": Subject("GL", 3),
            "Poo": Subject("Poo", 3),
            "Web2": Subject("Web2", 3),
            "systemExpert": Subject("systemExpert", 2),
            "psycho4": Subject("psycho4", 1),
            "didactique": Subject("didactique", 1)
        }
        self.levels["info4 (+5)"] = info4_5
        
        # Add unsupported years
        self.unsupported_years = ["info5"]

class SciencesSpecialization(Specialization):
    def _init_levels(self):
        # First year subjects
        sciences1 = {
            "chimie": Subject("chimie", 3),
            "biophysique": Subject("biophysique", 3),
            "math": Subject("math", 3),
            "info": Subject("info", 1),
            "tarbya": Subject("tarbya", 1),
            "cyto": Subject("cyto", 1.5),
            "histo": Subject("histo", 1.5),
            "bv": Subject("bv", 1.5),
            "embryo": Subject("embryo", 1.5),
            "géologie": Subject("géologie", 3)
        }
        self.levels["sciences1"] = sciences1

        # Second year subjects
        sciences2 = {
            "Biochimie": Subject("Biochimie", 4),
            "Botanique": Subject("Botanique", 4),
            "Zoologie": Subject("Zoologie", 4),
            "Microbiologie": Subject("Microbiologie", 3),
            "Génétique": Subject("Génétique", 3),
            "Paléontologie": Subject("Paléontologie", 2),
            "Psycho2": Subject("Psycho2", 2)
        }
        self.levels["sciences2"] = sciences2

        # Third year subjects (+4)
        sciences3_4 = {
            "physiologie_animal": Subject("physiologie_animal", 3),
            "physiologie_végétale": Subject("physiologie_végétale", 3),
            "biomol": Subject("biomol", 2),
            "pétrologie": Subject("pétrologie", 3),
            "psycho3": Subject("psycho3", 2),
            "immunologie": Subject("immunologie", 1),
            "parasitologie": Subject("parasitologie", 1),
            "anglais ": Subject("anglais ", 1),
            "nutrition": Subject("nutrition", 1)
        }
        self.levels["sciences3 (+4)"] = sciences3_4

        # Third year subjects (+5)
        sciences3_5 = {
            "physiologie_animal": Subject("physiologie_animal", 3),
            "physiologie_végétale": Subject("physiologie_végétale", 3),
            "biomol": Subject("biomol", 3),
            "pétrologie": Subject("pétrologie", 3),
            "psycho3": Subject("psycho3", 2),
            "immunologie": Subject("immunologie", 1),
            "parasitologie": Subject("parasitologie", 1),
            "anglais ": Subject("anglais ", 1)
        }
        self.levels["sciences3 (+5)"] = sciences3_5
        
        # Add unsupported years
        self.unsupported_years = ["sciences4 (+4)", "sciences4 (+5)", "sciences5"]

class SpecializationFactory:
    @staticmethod
    def get_specialization(specialization_name: str) -> Optional[Specialization]:
        specializations = {
            'arabic': ArabicSpecialization,
            'math': MathSpecialization,
            'physics': PhysicsSpecialization,
            'info': InfoSpecialization,
            'sciences': SciencesSpecialization
        }
        
        specialization_class = specializations.get(specialization_name.lower())
        if specialization_class:
            return specialization_class()
        return None 
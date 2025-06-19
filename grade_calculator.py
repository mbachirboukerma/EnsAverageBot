from typing import Dict, List, Optional, Tuple
import math
from dataclasses import dataclass
from enum import Enum

class SubjectType(Enum):
    EXAM_ONLY = "exam_only"
    EXAM_TP = "exam_tp"
    EXAM_TD = "exam_td"
    EXAM_TP_TD = "exam_tp_td"
    DIRECT_AVERAGE = "direct_average"

@dataclass
class SubjectGrade:
    exam1: Optional[float] = None
    exam2: Optional[float] = None
    tp: Optional[float] = None
    td: Optional[float] = None
    direct_average: Optional[float] = None
    
    def is_complete(self) -> bool:
        """Check if all required grades are provided"""
        if self.direct_average is not None:
            return True
        
        required_grades = []
        if self.exam1 is not None:
            required_grades.append(self.exam1)
        if self.exam2 is not None:
            required_grades.append(self.exam2)
        if self.tp is not None:
            required_grades.append(self.tp)
        if self.td is not None:
            required_grades.append(self.td)
        
        return len(required_grades) > 0

class GradeCalculator:
    """Improved grade calculator with better validation and calculation methods"""
    
    def __init__(self):
        self.exam1_subjects = {
            "Bdd", "Réseau2", "GL", "Web2", "Poo", "systemExpert", "psycho", 
            "didactique", "tachri3", "analyse", "informatiquee", "algebre", 
            "thermo", "stm", "mecanique", "elect", "tarikh l3olom", "tarbiya",
            "solid_state_physics", "organic_chemistry", "analytical_chemistry",
            "technological_measurements", "modern_physics", "topologie", 
            "analyse 2", "calculs différentiels", "informatique", 
            "psychologie 'enfant'", "psycho éducative", "Mécanique quantique", 
            "méthodes math", "thermochimie", "9iyassat", "géométrie", 
            "algèbre linéaire", "algèbre générale", "analyse numérique", 
            "analyse complexe", "algèbre3", "théorie de mesure و de l'intégration1", 
            "psychologie éducative", "statistiques و probabilités", "logique",
            "math", "Optique", "Cinetique && électrochimie", "équilibre", 
            "électronique", "algo", "physics_education", "sm1", "logique", 
            "électro", "stat", "education sciences 'fares'", "français", 
            "algo2", "sm2", "se 1", "si 1", "psycho4", "thl", "ts", 
            "psychologie 'fares'", "anglais", "réseau", "se 2", "compilation", 
            "web", "ro", "psycho", "si 2", "ai", "chimie", "biophysique", 
            "géologie", "didactiques mathématiques", "Analyse complexe",
            "Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", 
            "Statistiques et probabilités2", "Équations différentielles",
            "Biochimie", "Botanique", "Zoologie", "Microbiologie", "Génétique",
            "Paléontologie", "physiologie_végétale", "physiologie_animal",
            "pétrologie", "biomol", "psycho3"
        }
        
        self.exam2_subjects = {
            "Bdd", "Réseau2", "Web2", "Poo", "systemExpert", "psycho4",
            "didactique", "tachri3", "GL", "Fluides", "didactique chimie",
            "math", "analyse", "informatiquee", "algebre", "thermo", "stm",
            "mecanique", "elect", "tarikh l3olom", "tarbiya",
            "solid_state_physics", "organic_chemistry", "analytical_chemistry",
            "technological_measurements", "modern_physics", "topologie",
            "analyse 2", "calculs différentiels", "informatique",
            "psychologie 'enfant'", "psycho éducative", "Mécanique quantique",
            "méthodes math", "thermochimie", "9iyassat", "géométrie",
            "algèbre linéaire", "algèbre générale", "analyse numérique",
            "analyse complexe", "algèbre3", "théorie de mesure و de l'intégration1",
            "psychologie éducative", "statistiques و probabilités", "logique",
            "math", "Cinetique && électrochimie", "équilibre", "électronique",
            "algo", "education sciences 'fares'", "physics_education", "sm1",
            "logique", "électro", "stat", "français", "algo2", "sm2", "se 1",
            "si 1", "thl", "ts", "psychologie 'fares'", "anglais", "réseau",
            "se 2", "compilation", "web", "ro", "psycho", "si 2", "ai",
            "chimie", "biophysique", "géologie", "didactiques mathématiques",
            "Analyse complexe", "Algèbre4", "Théorie de  mesure et de l'intégration2",
            "Géométrie", "Statistiques et probabilités2", "Équations différentielles",
            "Biochimie", "Botanique", "Zoologie", "Microbiologie", "Génétique",
            "Paléontologie", "physiologie_végétale", "physiologie_animal",
            "pétrologie", "biomol", "psycho3"
        }
        
        self.td_subjects = {
            "GL ", "GL", "Fluides", "didactique chimie", "math", "vibrations",
            "psychologie 'fares'", "psychologie 'enfant'", "Optique",
            "Cinetique && électrochimie", "équilibre", "électronique",
            "informatique", "algo", "algo2", "sm1", "sm2", "stat", "se 1",
            "thl", "si 1", "ts", "analyse numérique", "psycho", "ro", "se 2",
            "compilation", "mécanique classique", "nisbiya", "psycho éducative",
            "chimie organique", "chimie analytique", "Mécanique quantique",
            "méthodes math", "thermochimie", "9iyassat", "topologie",
            "analyse 2", "calculs différentiels", "géométrie", "algèbre linéaire",
            "algèbre générale", "analyse complexe", "stm", "solid", "analytique",
            "nucl", "atomique", "algèbre3", "théorie de mesure و de l'intégration1",
            "statistiques و probabilités", "analyse", "algebre", "thermo",
            "solid_state_physics", "organic_chemistry", "physics_education",
            "analytical_chemistry", "chemistry_education", "technological_measurements",
            "modern_physics", "mecanique", "elect", "logique", "électro",
            "psychologie éducative", "chimie", "biophysique",
            "didactiques mathématiques", "Analyse complexe", "Algèbre4",
            "Théorie de  mesure et de l'intégration2", "Géométrie",
            "Statistiques et probabilités2", "Équations différentielles",
            "Biochimie", "Zoologie", "Génétique", "Psycho2", "biomol", "psycho3"
        }
        
        self.tp_subjects = {
            "Réseau2 ", "Poo ", "Web2 ", "Bdd", "Réseau2", "Poo", "Web2",
            "didactique physique", "info", "vibrations", "informatiquee",
            "Optique", "Cinetique && électrochimie", "équilibre", "électronique",
            "compilation", "web", "réseau", "algo2", "thermo", "stm",
            "mecanique", "elect", "algo", "cyto", "histo", "bv", "embryo",
            "géologie", "Biochimie", "Botanique", "Zoologie", "Microbiologie",
            "Paléontologie", "physiologie_végétale", "physiologie_animal",
            "pétrologie"
        }
        
        self.special_subjects = {"vibrations", "Optique"}
        self.subject_with_cc = {
            "chimie organique", "chimie analytique", "thermochimie", "9iyassat",
            "solid_state_physics", "organic_chemistry", "physics_education",
            "analytical_chemistry", "chemistry_education", "technological_measurements",
            "solid", "analytique", "nucl", "atomique"
        }
    
    @staticmethod
    def validate_grade(grade: str) -> Tuple[bool, Optional[float], str]:
        """Validate grade input and return (is_valid, value, error_message)"""
        try:
            value = float(grade)
            if 0 <= value <= 20:
                return True, value, ""
            else:
                return False, None, "Grade must be between 0 and 20"
        except ValueError:
            return False, None, "Invalid grade format. Please enter a number"
    
    def get_subject_type(self, subject: str) -> SubjectType:
        """Determine the type of subject based on its requirements"""
        if subject in self.special_subjects:
            return SubjectType.DIRECT_AVERAGE
        
        has_exam1 = subject in self.exam1_subjects
        has_exam2 = subject in self.exam2_subjects
        has_tp = subject in self.tp_subjects
        has_td = subject in self.td_subjects
        
        if has_exam1 and has_exam2 and has_tp and has_td:
            return SubjectType.EXAM_TP_TD
        elif has_exam1 and has_exam2 and has_tp:
            return SubjectType.EXAM_TP
        elif has_exam1 and has_exam2 and has_td:
            return SubjectType.EXAM_TD
        else:
            return SubjectType.EXAM_ONLY
    
    def calculate_subject_average(self, subject: str, grades: SubjectGrade, 
                                specialization: str, level: str) -> Tuple[float, str]:
        """Calculate subject average with detailed error handling"""
        
        if not grades.is_complete():
            return 0.0, "Incomplete grades provided"
        
        # Handle special subjects with direct average
        if subject in self.special_subjects:
            if grades.direct_average is None:
                return 0.0, "Direct average required for this subject"
            return grades.direct_average, ""
        
        # Handle sciences specialization special cases
        if specialization == 'sciences':
            return self._calculate_sciences_average(subject, grades, level)
        
        # Handle chemistry education special case
        if subject == "chemistry_education":
            if grades.exam1 is None or grades.td is None:
                return 0.0, "Exam1 and TD required for chemistry_education"
            return (grades.exam1 * 2 + grades.td) / 3, ""
        
        # Handle general cases
        return self._calculate_general_average(subject, grades, specialization, level)
    
    def _calculate_sciences_average(self, subject: str, grades: SubjectGrade, 
                                  level: str) -> Tuple[float, str]:
        """Calculate average for sciences specialization"""
        
        if level == 'sciences1':
            if subject in ["chimie", "biophysique", "math"]:
                if not all([grades.td, grades.exam1, grades.exam2]):
                    return 0.0, "TD, Exam1, and Exam2 required"
                return sum([grades.td, grades.exam1, grades.exam2]) / 3, ""
            
            elif subject == "géologie":
                if not all([grades.exam1, grades.exam2, grades.tp]):
                    return 0.0, "Exam1, Exam2, and TP required"
                return sum([grades.exam1, grades.exam2, grades.tp]) / 3, ""
            
            elif subject in ["cyto", "histo", "bv", "embryo"]:
                if not all([grades.exam1, grades.tp]):
                    return 0.0, "Exam1 and TP required"
                return 0.7 * grades.exam1 + 0.3 * grades.tp, ""
            
            else:  # info, tarbya
                if grades.exam1 is None:
                    return 0.0, "Exam1 required"
                return grades.exam1, ""
        
        elif level == 'sciences2':
            if subject == "Génétique":
                if not all([grades.td, grades.exam1, grades.exam2]):
                    return 0.0, "TD, Exam1, and Exam2 required"
                return sum([grades.td, grades.exam1, grades.exam2]) / 3, ""
            
            elif subject == "Psycho2":
                if not all([grades.exam1, grades.td]):
                    return 0.0, "Exam1 and TD required"
                return (grades.exam1 * 2 + grades.td) / 3, ""
            
            elif subject in ["Botanique", "Microbiologie", "Paléontologie"]:
                if not all([grades.exam1, grades.exam2, grades.tp]):
                    return 0.0, "Exam1, Exam2, and TP required"
                return sum([grades.exam1, grades.exam2, grades.tp]) / 3, ""
            
            elif subject == "Zoologie":
                if not all([grades.exam1, grades.exam2, grades.tp, grades.td]):
                    return 0.0, "Exam1, Exam2, TP, and TD required"
                return (sum([grades.exam1, grades.exam2]) + 
                       (0.5 * grades.tp + 0.5 * grades.td)) / 3, ""
            
            elif subject == "Biochimie":
                if not all([grades.exam1, grades.exam2, grades.tp, grades.td]):
                    return 0.0, "Exam1, Exam2, TP, and TD required"
                return (sum([grades.exam1, grades.exam2]) + 
                       (0.75 * grades.tp + 0.25 * grades.td)) / 3, ""
            
            else:
                if grades.exam1 is None:
                    return 0.0, "Exam1 required"
                return grades.exam1, ""
        
        return 0.0, "Unknown sciences level"
    
    def _calculate_general_average(self, subject: str, grades: SubjectGrade,
                                 specialization: str, level: str) -> Tuple[float, str]:
        """Calculate average for general cases"""
        
        grade_list = []
        if grades.exam1 is not None:
            grade_list.append(grades.exam1)
        if grades.exam2 is not None:
            grade_list.append(grades.exam2)
        if grades.tp is not None:
            grade_list.append(grades.tp)
        if grades.td is not None:
            grade_list.append(grades.td)
        
        if len(grade_list) == 1:
            return grade_list[0], ""
        elif len(grade_list) == 2:
            return sum(grade_list) / 2, ""
        elif len(grade_list) == 3:
            return sum(grade_list) / 3, ""
        elif len(grade_list) == 4:
            if ((specialization == 'physics' and level == 'physics3 (+4)') or 
                (specialization == 'info' and level in ['info2', 'info3'])):
                # Exam1 + Exam2 + (TP * 0.5 + TD * 0.5) / 3
                return (sum(grade_list[:2]) + 
                       (grade_list[2] * 0.5 + grade_list[3] * 0.5)) / 3, ""
            else:
                # Both TP and TD
                return (sum(grade_list[:2]) + 
                       (2 * grade_list[2] + grade_list[3]) / 3) / 3, ""
        
        return 0.0, "Invalid grade combination"
    
    def calculate_overall_average(self, subject_grades: Dict[str, float], 
                                coefficients: Dict[str, int]) -> Tuple[float, str]:
        """Calculate overall average with validation"""
        
        if not subject_grades or not coefficients:
            return 0.0, "No grades or coefficients provided"
        
        total_weighted_sum = 0
        total_coefficients = 0
        
        for subject, grade in subject_grades.items():
            if subject not in coefficients:
                return 0.0, f"Missing coefficient for subject: {subject}"
            
            coefficient = coefficients[subject]
            total_weighted_sum += grade * coefficient
            total_coefficients += coefficient
        
        if total_coefficients == 0:
            return 0.0, "Total coefficients cannot be zero"
        
        average = total_weighted_sum / total_coefficients
        return math.ceil(average * 100) / 100, "" 

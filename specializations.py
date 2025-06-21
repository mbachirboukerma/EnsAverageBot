# Define groups for exams, TD, and TP
exam1_subjects = [
    "Bdd", "Réseau2",  "GL", "Web2", "Poo", "systemExpert", "psycho",  "didactique", "tachri3", "analyse", "informatiquee", "algebre", "thermo", "stm", "mecanique", "elect", "tarikh l3olom", "tarbiya","solid_state_physics","organic_chemistry","analytical_chemistry","technological_measurements","modern_physics",
    "topologie", "analyse 2", "calculs différentiels", "informatique", "psychologie 'enfant'", "psycho éducative", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l'intégration1", "psychologie éducative", "statistiques و probabilités", "logique",
    "math", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "algo","physics_education",
    "sm1", "logique", "électro", "stat", "education sciences 'fares'", "français", "algo2", "sm2", "se 1", "si 1", "psycho4",
    "thl", "ts", "psychologie 'fares'", "anglais", "réseau", "se 2", "compilation", "web", "ro", "psycho", "si 2", "ai", "chimie", "biophysique", "géologie","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Botanique","Zoologie","Microbiologie","Génétique","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie","biomol","psycho3"
]
exam2_subjects = [
    "Bdd", "Réseau2", "Web2", "Poo", "systemExpert", "psycho4",  "didactique", "tachri3", "GL", "Fluides", "didactique chimie", "math","analyse", "informatiquee", "algebre", "thermo", "stm", "mecanique", "elect", "tarikh l3olom", "tarbiya","solid_state_physics","organic_chemistry","analytical_chemistry","technological_measurements","modern_physics",
    "topologie", "analyse 2", "calculs différentiels", "informatique", "psychologie 'enfant'",  "psycho éducative", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l'intégration1", "psychologie éducative", "statistiques و probabilités", "logique",
    "math", "Cinetique && électrochimie", "équilibre", "électronique", "algo","education sciences 'fares'","physics_education",
    "sm1", "logique", "électro", "stat", "français", "algo2", "sm2", "se 1", "si 1",
    "thl", "ts", "psychologie 'fares'", "anglais", "réseau", "se 2", "compilation", "web", "ro", "psycho", "si 2", "ai", "chimie", "biophysique", "géologie","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Botanique","Zoologie","Microbiologie","Génétique","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie","biomol","psycho3"
]

td_subjects = [
    "GL ", "GL", "Fluides", "didactique chimie", "math", "vibrations", "psychologie 'fares'", "psychologie 'enfant'", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "informatique",
    "algo", "algo2", "sm1", "sm2", "stat", "se 1", "thl", "si 1", "ts", "analyse numérique", "psycho", "ro", "se 2", "compilation","mécanique classique", "nisbiya", "psycho éducative", "chimie organique", "chimie analytique", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "topologie", "analyse 2", "calculs différentiels", "géométrie", "algèbre linéaire", "algèbre générale", "analyse complexe", "stm", "solid", "analytique", "nucl", "atomique",
    "algèbre3", "théorie de mesure و de l'intégration1", "statistiques و probabilités", "analyse", "algebre", "thermo","solid_state_physics","organic_chemistry","physics_education","analytical_chemistry","chemistry_education","technological_measurements","modern_physics", "mecanique", "elect", "logique", "électro", "psychologie éducative", "chimie", "biophysique","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Zoologie","Génétique","Psycho2","biomol","psycho3"
]

tp_subjects = [
    "Réseau2 ", "Poo ", "Web2 ", "Bdd", "Réseau2", "Poo","Web2", "didactique physique", "info","vibrations", "informatiquee", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "compilation", "web",
    "réseau", "algo2", "thermo", "stm", "mecanique", "elect", "algo", "cyto", "histo", "bv", "embryo", "géologie","Biochimie","Botanique","Zoologie","Microbiologie","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie",
]

subject_with_cc =["chimie organique", "chimie analytique", "thermochimie", "9iyassat" ,"solid_state_physics", "organic_chemistry", "physics_education", "analytical_chemistry", "chemistry_education", "technological_measurements","solid","analytique","nucl","atomique"]

# Define special subjects that require direct average input
special_subjects = ["vibrations", "Optique"]

# Define levels with sub-levels
levelsWithSubLevels = ["physics4", "math4", "sciences4", "info4","sciences3",'physics3']

# Define grades and coefficients for each specialization and level
specializations = {
    'math': {
        'math1': {
            "analyse": 4,
            "algebre": 2,
            "thermo": 3,
            "stm": 3,
            "mecanique": 3,
            "elect": 3,
            "tarikh l3olom": 1,
            "tarbiya": 1,
        },
        'math2': {
            "topologie": 4,
            "analyse 2": 2,
            "calculs différentiels": 2,
            "informatiquee": 2,
            "psychologie 'enfant'": 2,
            "géométrie": 2,
            "algèbre linéaire": 2,
            "algèbre générale": 2,
        },
        'math3': {
            "analyse numérique": 4,
            "analyse complexe": 2,
            "algèbre3": 2,
            "théorie de mesure و de l'intégration1": 2,
            "psychologie éducative": 2,
            "géométrie": 2,
            "statistiques و probabilités": 2,
            "logic math": 1,
        },
        'math4 (+4)': {},
        'math4 (+5)': {
            "didactiques mathématiques": 2,
            "Analyse complexe": 2,
            "Algèbre4": 2,
            "Théorie de  mesure et de l'intégration2": 2,
            "Programmes d'études": 1,
            "Géométrie": 2,
            "Statistiques et probabilités2": 2,
            "Équations différentielles": 2,
        },
        'math5': {}
    },
    'physics': {
        'physics1': {
            "analyse": 4,
            "algebre": 2,
            "thermo": 3,
            "stm": 3,
            "mecanique": 3,
            "elect": 3,
            "tarikh l3olom": 1,
            "tarbiya": 1,
        },
        'physics2': {
            "math": 4,
            "vibrations": 3,  # اهتزازات
            "Optique": 3,  # الضوء
            "Cinetique && électrochimie": 3,  # الكيمياء الحركية و الكهربائية
            "équilibre": 4,  # توازنات
            "électronique": 4,  # إلكترونيات
            "informatique": 2,  # معلوماتية
            "psycho": 2,  # علم النفس
        },
        'physics3 (+4)': {
            "solid_state_physics": 4,
            "modern_physics": 4,
            "organic_chemistry": 4,
            "physics_education": 4,
            "analytical_chemistry": 3,
            "chemistry_education": 2,
            "technological_measurements": 2,
            "psycho3": 2,
        },
        'physics3 (+5)': {
            "mécanique classique": 3,
            "nisbiya": 3,
            "psycho3": 2,
            "chimie organique": 3,
            "chimie analytique": 3,
            "Mécanique quantique": 3,
            "méthodes math": 3,
            "thermochimie": 3,
            "9iyassat": 2,
        },
        'physics4 (+4)': {},
        'physics4 (+5)': {
            "solid": 3,
            "analytique": 3,
            "Fluides": 2,
            "info": 2,
            "nucl": 2,
            "atomique": 2,
            "didactique chimie": 3,
            "didactique physique": 3,
            "Manahidj": 1,
        },
        'physics5': {}
    },
    'info': {
        'info1': {
            "algo": 5,
            "sm1": 4,
            "logique": 3,
            "algebre": 3,
            "analyse": 3,
            "électro": 3,
            "stat": 2,
            "tarikh l3olom": 1,
            "education sciences 'fares'": 1,
            "français": 1
        },
        'info2': {
            "algo2": 5,
            "sm2": 4,
            "se 1": 4,
            "si 1": 3,
            "thl": 3,
            "ts": 2,
            "analyse numérique": 2,
            "psychologie 'fares'": 2,
            "anglais": 1
        },
        'info3': {
            "réseau": 4,
            "se 2": 4,
            "compilation": 4,
            "web": 3,
            "ro": 3,
            "psycho": 2,
            "si 2": 2,
            "ai": 2,
            "anglais": 1,
        },
        'info4 (+4)': {
            "Réseau2 ": 4,
            "GL ": 3,
            "Poo ": 3,
            "Web2 ": 3,
            "systemExpert ": 2,
            "psycho4 ": 1,
            "didactique ": 1,
            "tachri3 ": 1,
            "Stage": 3,
        },
        'info4 (+5)': {
            "Bdd": 4,
            "Réseau2": 4,
            "GL": 3,
            "Poo": 3,
            "Web2": 3,
            "systemExpert": 2,
            "psycho4": 1,
            "didactique": 1,
        },
        'info5': {}
    },
    'sciences': {
        'sciences1': {
            "chimie": 3,
            "biophysique": 3,
            "math": 3,
            "info": 1,
            "tarbya": 1,
            "cyto": 1.5,
            "histo": 1.5,
            "bv": 1.5,
            "embryo": 1.5,
            "géologie": 3,
        },
        'sciences2': {
            "Biochimie": 4,
            "Botanique": 4,
            "Zoologie": 4,
            "Microbiologie": 3,
            "Génétique": 3,
            "Paléontologie": 2,
            "Psycho2": 2,
        },
        'sciences3 (+4)': {
            "physiologie_animal": 3,
            "physiologie_végétale": 3,
            "biomol": 2,
            "pétrologie": 3,
            "psycho3": 2,
            "immunologie": 1,
            "parasitologie": 1,
            "anglais ": 1,
            "nutrition": 1,
        },
        'sciences3 (+5)': {
            "physiologie_animal": 3,
            "physiologie_végétale": 3,
            "biomol": 3,
            "pétrologie": 3,
            "psycho3": 2,
            "immunologie": 1,
            "parasitologie": 1,
            "anglais ": 1,
        },
        'sciences4 (+4)': {},
        'sciences4 (+5)':{},
        'sciences5': {}
    },
    'musique': {
        'musique1': {},
        'musique2': {},
        'musique3': {},
        'musique4 (+4)': {},
        'musique4 (+5)': {},
        'musique5': {}
    }
}
